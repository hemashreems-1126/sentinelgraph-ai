import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelGraph"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Groq LLM Configuration (Groq only)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    USE_MOCK_LLM: bool = False  # Automatically defaults to True if GROQ_API_KEY is not set
    
    # Database Configuration
    # Supports Postgres in Docker/Production and SQLite fallback for instant zero-dependency local runs
    DATABASE_URL: str = "sqlite:///./sentinelgraph.db"
    
    # Deterministic Risk Score Thresholds
    RISK_BAND_LOW_MAX: int = 30
    RISK_BAND_MEDIUM_MAX: int = 60
    RISK_BAND_HIGH_MAX: int = 80
    RISK_BAND_CRITICAL_MAX: int = 100
    
    # Decision Policy Thresholds (calibrated against synthetic dataset risk distribution)
    DECISION_ALLOW_MAX: int = 30
    DECISION_REVIEW_MAX: int = 70
    DECISION_BLOCK_MIN: int = 71
    
    # Investigation parameters
    MAX_INVESTIGATION_LOOPS: int = 2
    EVIDENCE_CONFIDENCE_THRESHOLD: float = 0.65
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def is_mock_llm(self) -> bool:
        return self.USE_MOCK_LLM or not self.GROQ_API_KEY or self.GROQ_API_KEY.strip() == "" or self.GROQ_API_KEY.startswith("gsk_placeholder")


settings = Settings()
