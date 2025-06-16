"""
This file defines the tools that the master agent will use to answer queries.
It includes tools for:
- Retrieving relevant chunks from the vector database.
- Retrieving full documents based on relevance.
- Querying the structured PostgreSQL database using natural language.
- Summarizing conversation history for memory.
"""
import os
from typing import Any, Dict, List

import chromadb
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain.tools import tool
# from langchain_community.document_loaders import PyPDFLoader # No longer needed
import pypdf # Use the base library directly
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_chroma import Chroma

from app.agent.llm import embedding_model, main_model, reasoning_model
from app.core.config import settings
from app.core.logging_config import logger

# --- Tool-specific Initializers ---

def get_vector_store() -> Chroma:
    """Initializes and returns the Chroma vector store client."""
    chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    vector_store = Chroma(
        client=chroma_client,
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=embedding_model,
    )
    return vector_store

def get_sql_database() -> SQLDatabase:
    """Initializes and returns the LangChain SQLDatabase connector."""
    # The 'sample_rows_in_table_info' parameter is crucial for the LLM to understand the data format
    return SQLDatabase.from_uri(
        str(settings.DATABASE_URL),
        sample_rows_in_table_info=2
    )


# --- Tool Definitions ---

@tool
def retrieve_relevant_chunks(query: str) -> List[Dict[str, Any]]:
    """
    Retrieves the 5 most relevant document chunks from the vector database based on a query.
    Useful for getting specific, targeted information from the documents.
    """
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_relevance_scores(query, k=5)

    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "relevance_score": score
        })
    return formatted_results

@tool
def retrieve_full_documents(query: str) -> List[Dict[str, str]]:
    """
    Retrieves the full text of the 2 most relevant documents from the vector database.
    Useful when a broader context is needed to answer a question.
    It finds relevant chunks and returns the entire content of the documents those chunks belong to.
    """
    vector_store = get_vector_store()
    # Retrieve more chunks to increase the chance of getting diverse documents
    retrieved_chunks = vector_store.similarity_search(query, k=10)

    unique_paths = []
    for chunk in retrieved_chunks:
        path = chunk.metadata.get("path")
        if path and path not in unique_paths:
            unique_paths.append(path)
        if len(unique_paths) >= 2:
            break

    if not unique_paths:
        logger.warning(f"Could not find any documents for query: '{query}'")
        return [{"filename": "No relevant documents found.", "content": ""}]

    documents = []
    for path in unique_paths:
        filename = os.path.basename(path)
        # The path stored in metadata should be the source of truth.
        correct_path = path

        if os.path.exists(correct_path):
            try:
                logger.info(f"Loading full document from path: {correct_path}")
                reader = pypdf.PdfReader(correct_path)
                full_text = ""
                for page in reader.pages:
                    full_text += page.extract_text() + "\n\n"
                documents.append({
                    "filename": filename,
                    "content": f"--- Document: {filename} ---\n\n{full_text}"
                })
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Could not load document {filename}: {e}", exc_info=True)
                documents.append({"filename": filename, "content": f"Could not load document {filename}: {e}"})
        else:
            logger.error(f"Document not found at path: {correct_path}")
            documents.append({"filename": filename, "content": f"Document not found at path: {correct_path}"})

    return documents

@tool
def query_structured_data(query: str) -> str:
    """
    Accepts a natural language query about factual information, converts it to a SQL query,
    executes it against the PostgreSQL database, and returns the result.
    Useful for questions about specific numbers, dates, parties, or other structured data.
    """
    db = get_sql_database()
    try:
        # Create a chain that generates SQL
        query_chain = create_sql_query_chain(reasoning_model, db)
        sql_query = query_chain.invoke({"question": query})
        logger.info(f"Generated SQL query: {sql_query}")

        # Execute the query and return the result
        result = db.run(sql_query)
        logger.info(f"SQL query result: {result}")
        return f"Executed SQL Query: {sql_query}\n\nResult:\n{result}"
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error querying structured data for query '{query}': {e}", exc_info=True)
        # Provide a more informative error message for the agent
        return (f"An error occurred while querying the database: {e}. "
                f"Please check if your question is valid for the available tables "
                f"or try rephrasing your question.")

@tool
async def summarize_discussion(conversation_history: str) -> str:
    """
    Generates a concise summary of the conversation history.
    This tool is used by the agent to maintain context and awareness in a long conversation.
    """
    prompt = f"""
    Please provide a concise, high-level summary of the following conversation.
    Focus on the key questions asked and the main findings. Do not summarize turn-by-turn.

    Conversation History:
    ---
    {conversation_history}
    ---

    High-level Summary:
    """
    logger.info("Summarizing conversation history.")
    response = await main_model.ainvoke(prompt)
    return response.content
