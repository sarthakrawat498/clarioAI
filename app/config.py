import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PolicyBazaar Health Insurance AI Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: Optional[str] = None  # Must be provided in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Database: Supports SQLite (sqlite:///./health_insurance.db), Azure SQL (mssql+pyodbc://...), PostgreSQL
    DATABASE_URL: str = "sqlite:///./health_insurance.db"

    # OpenAI / Azure Settings
    LLM_PROVIDER: Optional[str] = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vector Storage
    CHROMA_DB_DIR: str = "./data/chromadb"

    # App Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Demo Mode: Set to true to allow unauthenticated demo access
    ENABLE_DEMO_MODE: bool = False
    DEMO_USER_EMAIL: str = "demo@clario.ai"
    DEMO_USER_PASSWORD: str = "demo123456"
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate SECRET_KEY for production
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY == "super-secret-key-change-in-production-policybazaar-ai":
                raise ValueError(
                    "SECRET_KEY must be set to a strong value in production. "
                    "Set the SECRET_KEY environment variable to a secure random value."
                )
        # Provide default for development only
        if not self.SECRET_KEY and self.ENVIRONMENT != "production":
            self.SECRET_KEY = "dev-secret-key-change-in-production-policybazaar-ai"

    @property
    def effective_model(self) -> str:
        return self.OPENAI_MODEL or self.LLM_MODEL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
