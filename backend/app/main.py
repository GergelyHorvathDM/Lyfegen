"""
This is the main entrypoint for the FastAPI application.

It defines the API endpoints for interacting with the Lyfegen AI agent.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.logging_config import logger
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

# --- API Endpoints ---

@app.get("/", tags=["Root"])
async def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"message": "Welcome to the Lyfegen Document Intelligence API!"}
