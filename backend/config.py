import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load the .env file from the root directory
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-3.5-turbo"
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./data/uploads")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
    
    # Server Settings
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "localhost")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Chunking Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    ROWS_PER_CHUNK: int = 50
    
    # Vector Search Settings
    VECTOR_SEARCH_TOP_K: int = 5

settings = Settings()
