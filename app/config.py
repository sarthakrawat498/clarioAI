import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PolicyBazaar Health Insurance AI Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key-change-in-production-policybazaar-ai"
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

    @property
    def effective_model(self) -> str:
        return self.OPENAI_MODEL or self.LLM_MODEL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
