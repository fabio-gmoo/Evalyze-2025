from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    # LLM
    provider_base_url: str
    provider_api_key: str
    provider_model: str = "gpt-4o-mini"

    # Auth (JWT de Django)
    jwt_alg: str = "HS256"  # o RS256
    jwt_secret: str | None = None  # HS256
    jwt_public_key: str | None = None  # RS256 (clave pública)

    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_table: str = "messages"

    # CORS
    cors_allow_origins: list[str] = ["http://localhost:4200"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
