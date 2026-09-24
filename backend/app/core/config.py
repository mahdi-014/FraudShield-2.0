import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FraudShield 2.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "fraudshield-super-secret-key-change-in-production-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "fraudshield"
    POSTGRES_PASSWORD: str = "fraudshield_secure_pass"
    POSTGRES_DB: str = "fraudshield_db"
    DATABASE_URL: Optional[str] = None

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "fraudshield_graph_pass"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # GenAI / LLM
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = "mock-key-for-development"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vector DB
    VECTOR_DB_URL: Optional[str] = None

    # Risk Weights
    WEIGHT_ML_FRAUD: float = 0.35
    WEIGHT_ANOMALY: float = 0.15
    WEIGHT_BEHAVIOR: float = 0.20
    WEIGHT_RULE: float = 0.15
    WEIGHT_GRAPH: float = 0.15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
