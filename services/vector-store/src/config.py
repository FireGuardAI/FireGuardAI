from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    chroma_host: str = Field(default="localhost")
    chroma_port: int = Field(default=8000)
    chroma_anonymized_telemetry: bool = Field(default=False)

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_batch_size: int = Field(default=32, gt=0)

    chunk_size: int = Field(default=400, gt=0)
    chunk_overlap: int = Field(default=80, ge=0)

    raw_documents_dir: str = Field(default="raw_documents")
    bm25_index_path: str = Field(default="data/bm25_index.pkl")

    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
