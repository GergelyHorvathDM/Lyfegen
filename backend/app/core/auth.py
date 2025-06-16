from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """
    Dependency to verify the API key.
    """
    if api_key_header == settings.API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        ) 