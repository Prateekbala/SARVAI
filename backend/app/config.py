from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "SARVAI"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "sarvai"
    MINIO_SECURE: bool = False
    
    # AI/ML
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Text Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    LLM_CONTEXT_WINDOW: int = 4096
    
    # Web Search
    BRAVE_API_KEY: str = ""
    SERP_API_KEY: str = ""
    WEB_SEARCH_RESULTS: int = 5
    WEB_SCRAPE_TIMEOUT: int = 10
    
    # RAG Configuration
    RAG_TOP_K: int = 5
    RAG_HYBRID_ALPHA: float = 0.7
    RAG_MIN_SIMILARITY: float = 0.3
    RAG_ENABLE_RERANK: bool = False
    
    # Optional APIs
    OPENAI_API_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        case_sensitive=True
    )

# Create global settings instance
settings = Settings()

# Ensure models directory exists
MODELS_DIR = Path(__file__).parent.parent / "models_cache"
MODELS_DIR.mkdir(exist_ok=True)