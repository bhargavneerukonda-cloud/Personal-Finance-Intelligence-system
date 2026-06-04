"""Application configuration via Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "FinSight AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    DATABASE_URL: str = "postgresql+asyncpg://finsight:finsight@localhost:5432/finsight_db"
    DATABASE_URL_SYNC: str = "postgresql://finsight:finsight@localhost:5432/finsight_db"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_ENV: str = "sandbox"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "finsight-transactions"

    MLFLOW_TRACKING_URI: str = "http://localhost:5001"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    ML_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
