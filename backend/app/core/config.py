import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Path Setup ---
# The .env file should be located in the 'backend' directory.
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
env_file_path = BACKEND_ROOT / ".env"

# --- Load Environment Variables ---
# We load the .env file. If variables are already set in the environment
# (e.g., via shell commands), they will take precedence.
load_dotenv(dotenv_path=env_file_path, override=False)

# The project root is one level up from the backend root.
PROJECT_ROOT = BACKEND_ROOT.parent

class Settings(BaseSettings):
    """Pydantic model for application settings."""
    # --- LLM Provider ---
    OPENAI_API_KEY: str # This will be loaded from the environment

    # --- Database ---
    # Hardcoded temporarily to resolve environment-specific issues
    DATABASE_URL: str = "postgresql://user:password@localhost:5433/lyfegen"
    
    # --- Vector Store ---
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "lyfegen_contracts"

    # --- Document Storage ---
    DOCUMENT_DIR: str = str(PROJECT_ROOT / "document_storage")

    # --- API Security ---
    API_KEY_NAME: str = "X-API-KEY"
    API_KEY: str = "lyfegen-ai-task-2024"

    # Pydantic reads from the environment, which we have pre-loaded.
    model_config = SettingsConfigDict(extra="ignore")

settings = Settings() 