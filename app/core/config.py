from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Adaptive Document Preparation System"
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "adaptive_doc_prep"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "slatefall_chunks"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    llm_provider: str = "mock"
    gemini_api_key: str | None = None
    groq_api_key: str | None = None

    # 🔗 Redis এবং Celery-র নতুন কনফিগারেশন ফিল্ডসমূহ
    redis_url: str = "redis://localhost:6380/0"
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0
    celery_broker_url: str = "redis://localhost:6380/0"
    celery_result_backend: str = "redis://localhost:6380/0"
    
    qdrant_score_threshold: float = 0.75

    # ⚙️ অতিরিক্ত ভ্যারিয়েবল ব্লকিং এড়াতে extra="ignore" সেট করা হলো
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore", 
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()