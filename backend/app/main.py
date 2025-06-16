"""
This is the main entrypoint for the FastAPI application.

It defines the API endpoints for interacting with the Lyfegen AI agent.
"""
from fastapi import FastAPI, Depends, Security, Header, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path

from app.agent.main_agent import main_agent, AgentState
from app.core.logging_config import logger
from app.core.security import get_api_key
from app.core.config import settings
from app.api.v1 import agent

# --- App Initialization ---
app = FastAPI(
    title="Lyfegen Document Intelligence API",
    description="API for the Lyfegen document intelligence application.",
    version="1.0.0"
)

# --- Middleware ---
# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you should restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Include the agent router with a /v1 prefix
app.include_router(agent.router, prefix="/v1")

# --- Static File Serving ---
# Serve the uploaded documents so they can be accessed by URL
# The path should be relative to where the backend is run from
document_storage_path = Path(settings.DOCUMENT_DIR)
if not document_storage_path.exists():
    document_storage_path.mkdir(parents=True, exist_ok=True)
    
app.mount("/documents", StaticFiles(directory=document_storage_path), name="documents")

# --- State Management ---

# A simple in-memory dictionary to store conversation state.
# The key is the conversation_id and the value is the agent's state.
# For production, this would be replaced with a more robust solution like Redis.
conversation_history = {}

# --- Pydantic Models ---

class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""
    session_id: str
    query: str


class QueryResponse(BaseModel):
    """Response model for the /query endpoint."""
    response: str
    source_documents: List[str] = Field(default_factory=list, description="List of source document filenames used to generate the response.")

# --- API Endpoints ---

@app.get("/", tags=["Root"])
async def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"message": "Welcome to the Lyfegen Document Intelligence API!"}


@app.post("/query", response_model=QueryResponse, tags=["Agent"])
async def query_agent(
    request: QueryRequest,
    api_key: str = Security(get_api_key),
    x_session_id: str = Header(None, alias="X-Session-ID") # Optional header for stateless clients
):
    """
    Main endpoint to interact with the conversational agent.
    
    It maintains conversation history in memory based on the session_id.
    """
    session_id = request.session_id or x_session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="A session_id must be provided in the request body or X-Session-ID header.")

    logger.info(f"Received query for session_id: {session_id}")

    # Get or create the session state
    session_state = conversation_history.get(session_id, AgentState(messages=[], source_documents=[]))
    
    # Add the user's query to the message history
    session_state["messages"].append(("user", request.query))

    logger.info(f"Invoking agent for session_id: {session_id}")
    final_state = await main_agent.ainvoke(session_state)
    logger.info(f"Returning response for session_id: {session_id}")

    # Save the updated state
    conversation_history[session_id] = final_state

    # Extract the agent's final response and source documents
    agent_response = final_state["messages"][-1].content
    sources = final_state.get("source_documents", [])

    return QueryResponse(response=agent_response, source_documents=sources)
