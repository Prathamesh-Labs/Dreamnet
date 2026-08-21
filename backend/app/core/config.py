import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DREAMNET API"
    API_V1_STR: str = "/api"
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/dreamnet"
    
    # LLM Keys
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    
    # Sandbox Settings
    SANDBOX_IMAGE: str = "dreamnet-sandbox:latest"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
