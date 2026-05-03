from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KGU Smart Assistant API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    google_api_key: str # 키 추가
    vector_store_path: str = ".tmp/chroma"
    vector_store_collection_name: str = "document_chunks"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" 
    )


settings = Settings()
