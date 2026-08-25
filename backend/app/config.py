from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str

    # Informational only -- the Garmin password is never stored. Run
    # scripts/garmin_login.py to authenticate; it prompts for the password
    # interactively and caches session tokens to .garmin_tokens/.
    garmin_email: str = ""

    # Optional: fixed training location for weather. If unset, it's derived
    # from the most recent GPS-tagged activity instead.
    location_lat: float | None = None
    location_lon: float | None = None

    secret_key: str = "dev-secret"
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
