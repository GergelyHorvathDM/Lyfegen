from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import tempfile
import os
from typing import Optional

from langchain_core.messages import HumanMessage
from app.agent.main_agent import main_agent
from app.agent.document_loader import load_and_extract_text
from app.core.config import settings
from app.core.logging_config import logger

router = APIRouter()

# In-memory storage for conversation history
conversation_history = {}

class ChatResponse(BaseModel):
    """The final answer from the agent, including sources."""
    answer: str
    sources: list[dict]

@router.post("/query-stream")
async def query_stream(
    session_id: str = Form(...),
    query: str = Form(...),
    api_key: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    """
    Handles both general queries and queries with an uploaded document.
    Always streams the response back.
    The API key is sent as part of the form data.
    """
    logger.info(f"=== QUERY STREAM ENDPOINT HIT ===")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Query: {query}")
    logger.info(f"API Key received: {api_key}")
    logger.info(f"File: {file.filename if file else 'None'}")
    
    # Verify the API key from the form
    if api_key != settings.API_KEY:
        logger.error(f"Invalid API key. Expected: {settings.API_KEY}, Got: {api_key}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key."
        )

    logger.info(f"API key validated successfully")
    logger.info(f"Received query for session_id: {session_id}")
    
    initial_state = conversation_history.get(session_id, {"messages": [], "source_documents": []})
    initial_state["ad_hoc_context"] = None

    # If a file is uploaded, process it and add its content to the state
    if file:
        logger.info(f"File received: {file.filename}")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            
            logger.info(f"File saved to temporary path: {tmp_path}")
            ad_hoc_content = load_and_extract_text(tmp_path)
            initial_state["ad_hoc_context"] = ad_hoc_content

        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}", exc_info=True)
            async def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'content': f'Failed to process file: {e}'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Add the user's query to the message history
    initial_state["messages"] = initial_state.get("messages", []) + [HumanMessage(content=query)]

    async def stream_agent_response():
        logger.info(f"Streaming agent response for session_id: {session_id}")
        final_state = None
        try:
            async for event in main_agent.astream_events(
                initial_state,
                version="v1", 
            ):
                kind = event["event"]
                
                if kind == "on_chain_start":
                    if event["name"] == "agent_node":
                        pass

                elif kind == "on_tool_start":
                    status_update = f"Running: {event['name']}"
                    logger.info(f"Streaming status update: {status_update}")
                    yield f"data: {json.dumps({'type': 'status', 'content': status_update})}\n\n"
                    if event['name'] == 'summarize_discussion':
                        logger.info("Summarizing conversation history.")

                elif kind == "on_chain_end":
                    if event["name"] == "generate_final_response":
                        final_state = event["data"]["output"]
                        
                        # Extract the final answer and sources
                        final_message = final_state["messages"][-1]
                        answer = final_message.content
                        sources = final_state.get("source_documents", [])
                        
                        # Create the final payload
                        final_payload = {
                            "type": "final_response",
                            "content": answer,
                            "sources": sources
                        }
                        
                        logger.info(f"Streaming final answer for session_id: {session_id}")
                        yield f"data: {json.dumps(final_payload)}\n\n"
            
            if final_state:
                conversation_history[session_id] = final_state

        except Exception as e:
            logger.error(f"Error during agent execution for session {session_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': f'An unexpected error occurred: {e}'})}\n\n"

    return StreamingResponse(stream_agent_response(), media_type="text/event-stream") 