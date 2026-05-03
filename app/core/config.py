from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KGU Smart Assistant API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    google_api_key: str
    kakao_map_api_key: str | None = None
    translation_api_key: str | None = None
    translation_provider: str = "google"
    google_translation_api_url: str = "https://translation.googleapis.com/language/translate/v2"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
