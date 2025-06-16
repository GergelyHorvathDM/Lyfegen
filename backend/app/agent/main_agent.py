"""
This file defines the main agentic framework using LangGraph.

The agent is designed as a stateful graph that can use a variety of tools
to answer user queries about the ingested documents. It maintains conversational
history through a mandatory summarization step in each cycle.
"""
from typing import Annotated, TypedDict, List
import json
import os

from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from app.agent.llm import main_model, final_answer_model
from app.agent.tool_agents import (
    retrieve_relevant_chunks,
    retrieve_full_documents,
    query_structured_data,
    summarize_discussion,
)
from app.core.logging_config import logger


class AgentState(TypedDict):
    """
    Represents the state of our agent.
    
    Attributes:
        messages: The history of messages in the conversation.
        source_documents: A list of unique source document filenames cited by the tools.
        ad_hoc_context: Text extracted from a user-uploaded document for a single query.
    """
    messages: Annotated[list, add_messages]
    source_documents: List[dict]
    ad_hoc_context: str = None


# --- Agent Setup ---

# 1. Define the tools
# We explicitly define the summarization tool to call it manually,
# and the rest are for the agent to choose from.
tools = [retrieve_relevant_chunks, retrieve_full_documents, query_structured_data]
tool_node = ToolNode(tools)

# 2. Bind the tools to the model
# The model will use the tools' schemas to decide when to call them.
model = main_model.bind_tools(tools)


# --- Custom Tool Node ---
async def call_tools_and_update_state(state: AgentState) -> dict:
    """
    Custom node to execute tools, parse their output for source documents,
    and update the agent's state.
    """
    # 1. Execute the tool calls requested by the agent
    tool_messages = await tool_node.ainvoke(state["messages"])
    
    # 2. Extract source documents from tool output
    newly_found_docs = []
    for tm in tool_messages:
        try:
            # The content of a ToolMessage is a string, so we need to parse it
            data = json.loads(tm.content)
            
            # For both chunk and full document retrieval, we now store the whole object
            if tm.name in ["retrieve_relevant_chunks", "retrieve_full_documents"]:
                for item in data:
                    # Create a unique ID for each source to prevent duplicates
                    # A simple combination of path and chunk number (if available) will suffice
                    path = item.get("metadata", {}).get("path") or item.get("filename")
                    chunk_num = item.get("metadata", {}).get("chunk_number", -1)
                    source_id = f"{path}_{chunk_num}"

                    # Add a dictionary with all details, not just the filename
                    newly_found_docs.append({
                        "id": source_id,
                        "content": item.get("content") or item.get("page_content"), # Handle both naming conventions
                        "metadata": item.get("metadata", {}) or {"path": path}
                    })

        except (json.JSONDecodeError, TypeError):
            # This tool call did not return structured data (e.g., query_structured_data)
            # or the content was not valid JSON. We can safely ignore it.
            continue
            
    # 3. Update the state
    current_docs = state.get("source_documents", [])
    # Create a set of existing IDs for efficient checking
    existing_ids = {doc["id"] for doc in current_docs}

    for doc in newly_found_docs:
        if doc["id"] not in existing_ids:
            current_docs.append(doc)
            existing_ids.add(doc["id"])
            
    return {"messages": tool_messages, "source_documents": current_docs}


# --- Graph Nodes ---

async def agent_node(state: AgentState):
    """
    The core node of the agent. It decides what actions to take.
    
    On each turn, it first summarizes the conversation history, then uses that
    summary along with the latest query to decide whether to call a tool or
    respond directly to the user.
    """
    # 1. Summarize the conversation history
    history_for_summary = "\n".join([f"{msg.type}: {msg.content}" for msg in state["messages"]])
    
    summary = await summarize_discussion.ainvoke({"conversation_history": history_for_summary})

    # 2. Check for and prepare ad-hoc document context
    ad_hoc_context_text = ""
    if state.get("ad_hoc_context"):
        ad_hoc_context_text = (
            "--- User-Uploaded Document ---\n"
            f"{state['ad_hoc_context']}\n\n"
            "The user has uploaded the document above. Use its content to help answer their query."
        )

    # 3. Prepend the summary and any ad-hoc context as a system message
    messages_with_context = [
        SystemMessage(
            content=(
                "You are a helpful assistant for the Lyfegen project. "
                "Here is a summary of the conversation so far. Use it for context "
                "before answering the user's latest query.\n\n"
                f"--- Conversation Summary ---\n{summary}\n\n"
                f"{ad_hoc_context_text}" # This will be an empty string if no file was uploaded
                "To answer questions, you can use the user-uploaded document (if provided) and your available tools. "
                "Prioritize the user-uploaded document for context if it is relevant to the query."
            )
        )
    ]
    messages_with_context.extend(state["messages"])
    
    # 4. Decide on the next action using the full context
    response = await model.ainvoke(messages_with_context)
    return {"messages": [response]}


async def generate_final_response(state: AgentState):
    """
    After the agent has finished its work (tool calls), this node
    synthesizes the final, human-readable response and appends source links.
    """
    # The last message from the agent is a routing signal with no content.
    # We use the conversation history *before* that signal to generate a proper response.
    messages_for_final_answer = state["messages"][:-1]
    
    # We use the full message history (minus the routing signal) to generate the final answer
    final_response = await final_answer_model.ainvoke(messages_for_final_answer)
    
    # Un-escape newlines from the LLM's response.
    if isinstance(final_response.content, str):
        final_response.content = final_response.content.replace('\\n', '\n')

    # Append source links to the response content
    source_documents = state.get("source_documents", [])
    if source_documents:
        # The base URL should be what the client uses to access the server
        base_url = "http://127.0.0.1:8000"
        
        # Create a formatted list of unique links
        # Use two newlines to ensure a paragraph break in markdown
        source_links_md = "\n\n---\n**Sources:**\n"
        unique_links = {} # To avoid duplicate links for the same document
        for doc in source_documents:
            path = doc.get("metadata", {}).get("path")
            if path:
                filename = os.path.basename(path)
                # The URL the browser will use
                url = f"{base_url}/documents/{filename}"
                if url not in unique_links:
                    unique_links[url] = filename
        
        for url, filename in unique_links.items():
             source_links_md += f"- [{filename}]({url})\n" # A single newline for list items

        final_response.content += source_links_md

    # We are returning a new list with just the final response. `add_messages`
    # will append this to the history. The API layer is responsible for only
    # streaming the content of the very last message.
    return {"messages": [final_response]}


def should_continue(state: AgentState) -> str:
    """
    Determines the next step in the graph.
    
    If the model has made a tool call, we execute the tool.
    Otherwise, we end the graph and return the response to the user.
    """
    if state["messages"][-1].tool_calls:
        return "continue"
    return "end"


# --- Graph Definition ---

# Initialize the graph
graph = StateGraph(AgentState)

# Add the nodes
graph.add_node("agent", agent_node)
graph.add_node("action", call_tools_and_update_state)
graph.add_node("generate_final_response", generate_final_response)

# Define the edges
graph.set_entry_point("agent")
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": "generate_final_response",
    },
)
graph.add_edge("action", "agent")
graph.add_edge("generate_final_response", END)

# Compile the graph into a runnable
main_agent = graph.compile()

logger.info("Main agent has been compiled successfully.") 