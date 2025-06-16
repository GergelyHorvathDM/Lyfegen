from fastapi import Security, HTTPException, status, Depends, Query
from fastapi.security import APIKeyHeader
from typing import Optional

from app.core.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Query(None, alias="api_key")
):
    """
    Dependency to verify the API key.
    The key can be provided in the request header ('X-API-KEY') or as a query parameter ('api_key').
    Query parameter is checked first, then the header.
    
    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    # Prefer the query parameter if it exists, otherwise use the header
    api_key = api_key_query or api_key_header

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An API key is required. Provide it in the 'X-API-KEY' header or as an 'api_key' query parameter.",
        )
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key. Please check your credentials.",
        )
    return api_key 