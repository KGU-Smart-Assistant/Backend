from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KGU Smart Assistant API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    kakao_rest_api_key: str | None = None
    kakao_map_api_key: str | None = None
    kakao_local_base_url: str = "https://dapi.kakao.com"
    google_api_key: str # 키 추가
    vector_store_mode: str = "embedded"
    vector_store_path: str = ".tmp/chroma"
    vector_store_collection_name: str = "document_chunks"
    vector_store_host: str = "chroma"
    vector_store_port: int = 8000
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" 
    )


settings = Settings()
