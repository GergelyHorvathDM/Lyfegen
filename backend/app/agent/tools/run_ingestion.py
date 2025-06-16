"""
This script orchestrates the entire data ingestion pipeline.

It performs the following steps:
1.  Loads the raw PDF documents.
2.  Discovers content-based categories for the documents.
3.  For each category, designs a specific database schema.
4.  Creates the tables in the PostgreSQL database based on the designed schemas.
5.  Classifies, extracts, and inserts data for each document.
"""
import os
import asyncio

from app.agent.tools.ingestion import load_document_texts
from app.agent.tools.category_discovery import discover_categories
from app.agent.tools.schema_design import design_schema_for_category
from app.agent.tools.document_classifier import classify_document
from app.agent.tools.data_extractor import extract_structured_data
from app.db.database import create_table_from_schema, insert_structured_data
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
import chromadb

from app.core.config import settings
from app.core.logging_config import logger

async def main():
    """Main function to run the ingestion pipeline."""
    
    # --- Step 1: Load Document Texts ---
    logger.info("--- Step 1: Loading Documents ---")
    document_texts = load_document_texts(settings.DOCUMENT_DIR)
    
    # --- Initialize ChromaDB Vector Store ---
    logger.info("--- Initializing Vector Store ---")
    # Import embedding model here to avoid circular dependency issues at top level
    from app.agent.llm import embedding_model 
    
    chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    collection_name = settings.CHROMA_COLLECTION
    
    # Get or create the collection
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    # Clear the collection for a fresh run
    if collection.count() > 0:
        logger.info(f"Clearing {collection.count()} existing documents from vector store.")
        # To delete all items, get all their IDs and pass them to the delete function.
        all_item_ids = collection.get(include=[])["ids"]
        if all_item_ids:
            collection.delete(ids=all_item_ids)


    vector_store = Chroma(
        client=chroma_client,
        collection_name=collection_name,
        embedding_function=embedding_model,
    )
    
    # --- Step 2: Discover Categories ---
    logger.info("--- Step 2: Discovering Categories ---")
    # We'll use the content of all documents to get a comprehensive set of categories
    all_content = "\\n\\n".join(document_texts.values())
    categories = await discover_categories(all_content)
    
    if not categories:
        logger.error("Could not discover any categories. Exiting.")
        return

    logger.info(f"Discovered Categories: {', '.join(categories)}")
    
    # --- Step 3: Classify All Documents ---
    logger.info("--- Step 3: Classifying all documents before schema design ---")
    categorized_docs = {cat: [] for cat in categories}
    # Also create a map to store the text for each filename to avoid re-reading
    doc_text_by_category = {cat: [] for cat in categories}

    for filename, doc_text in document_texts.items():
        logger.info(f"  - Classifying '{filename}'...")
        category = await classify_document(doc_text, categories)
        if category and category in categorized_docs:
            categorized_docs[category].append(filename)
            doc_text_by_category[category].append(doc_text)
            logger.info(f"    -> Classified as: {category}")
        else:
            logger.warning(f"    -> Could not reliably classify '{filename}' into any of the discovered categories.")

    # --- Step 4: Design Schema for Each Category ---
    logger.info("--- Step 4: Designing Schemas ---")
    schemas = {}
    for category, docs in doc_text_by_category.items():
        if not docs:
            logger.warning(f"No documents found for category '{category}', skipping schema design.")
            continue
        logger.info(f"Designing schema for category: {category}")
        # Use the first document's text for schema design to keep the prompt small and relevant
        sample_text = docs[0]
        schema_sql = await design_schema_for_category(sample_text, category)
        if schema_sql:
            schemas[category] = schema_sql
            
    # --- Step 5: Create Tables in Database ---
    logger.info("--- Step 5: Creating Tables in DB ---")
    for category, schema_sql in schemas.items():
        logger.info(f"Creating table for category: {category}")
        await create_table_from_schema(schema_sql)
        
    # --- Step 6: Extract and Insert Data for Each Document ---
    logger.info("--- Step 6: Populating Tables and Vector Store ---")
    for filename, doc_text in document_texts.items():
        logger.info(f"Processing document: {filename}")
        
        # 6a: Classify
        category = await classify_document(doc_text, categories)
        if not category:
            logger.warning(f"  - Skipping document {filename}, could not classify.")
            continue
            
        # 6b: Extract
        schema_sql = schemas.get(category)
        if not schema_sql:
            logger.warning(f"  - Skipping document {filename}, no schema found for category '{category}'.")
            continue
            
        structured_data = await extract_structured_data(doc_text, schema_sql)
        if not structured_data:
            logger.warning(f"  - Skipping document {filename}, could not extract data.")
            continue
            
        # 6c: Insert into PostgreSQL
        table_name = category.lower().replace(" ", "_").replace("-", "_").replace("&", "and")
        await insert_structured_data(table_name, structured_data)
        
        # 6d: Chunk, Embed, and Insert into ChromaDB
        logger.info(f"  - Preparing '{filename}' for vector storage...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(doc_text)
        
        chunk_documents = []
        for i, chunk in enumerate(chunks):
            chunk_doc = Document(
                page_content=chunk,
                metadata={
                    "title": filename,
                    "path": os.path.join(settings.DOCUMENT_DIR, filename),
                    "category": category,
                    "chunk_number": i + 1,
                }
            )
            chunk_documents.append(chunk_doc)
        
        # Add the chunked documents to the vector store
        if chunk_documents:
            logger.info(f"  - Adding {len(chunk_documents)} chunks to vector store...")
            vector_store.add_documents(documents=chunk_documents)

    logger.info("--- Ingestion Pipeline Completed ---")


if __name__ == "__main__":
    asyncio.run(main()) 