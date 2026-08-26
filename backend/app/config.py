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

    # Google Calendar OAuth (see README for how to create these in Google
    # Cloud Console). Client secret is a real credential, unlike everything
    # else in this file -- backend/.env is gitignored, never commit it.
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # AI coach (Phase 6). Free tier -- get a key at https://aistudio.google.com/apikey
    # (no credit card). Model is configurable since Gemini's free-tier lineup moves
    # fast; bump this if gemini_model ever gets deprecated/moved off free tier.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    secret_key: str = "dev-secret"
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
