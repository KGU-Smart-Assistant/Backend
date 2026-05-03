from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KGU Smart Assistant API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    kakao_rest_api_key: str | None = None
    kakao_map_api_key: str | None = None
    kakao_local_base_url: str = "https://dapi.kakao.com"
    database_url: str = "sqlite:///./app.db"
    google_api_key: str # 키 추가
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" 
    )


settings = Settings()
