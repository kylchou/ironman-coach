"""Google Calendar via plain OAuth2 + REST calls (httpx), deliberately not
Google's official client libraries: `google-auth`/`google-api-python-client`
pull in the `cryptography` package, whose native (Rust) extension is
blocked by this machine's Application Control policy. The OAuth
authorization-code flow used here needs no client-side crypto -- it's just
JSON over HTTPS -- so plain httpx calls sidestep the problem entirely.
See https://developers.google.com/identity/protocols/oauth2/web-server
and https://developers.google.com/calendar/api/v3/reference/events/list
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.config import settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/calendar/v3"
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"

TOKEN_DIR = Path(__file__).resolve().parents[2] / ".google_tokens"
TOKEN_FILE = TOKEN_DIR / "token.json"


def authorize_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",  # required to receive a refresh_token
        "prompt": "consent",  # forces a refresh_token even on repeat auths
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _refresh_access_token(refresh_token: str) -> dict:
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def save_tokens(token_data: dict) -> None:
    """Persists access/refresh token + absolute expiry to a local gitignored
    file. Google's response gives `expires_in` (seconds from now), so we
    convert it to an absolute timestamp before storing.
    """
    TOKEN_DIR.mkdir(exist_ok=True)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
    existing = _load_raw() or {}
    existing["access_token"] = token_data["access_token"]
    # Google only returns refresh_token on the very first authorization (or
    # when prompt=consent forces a new one) -- keep the old one otherwise.
    if token_data.get("refresh_token"):
        existing["refresh_token"] = token_data["refresh_token"]
    existing["expires_at"] = expires_at.isoformat()
    TOKEN_FILE.write_text(json.dumps(existing))


def _load_raw() -> dict | None:
    if not TOKEN_FILE.exists():
        return None
    return json.loads(TOKEN_FILE.read_text())


def get_valid_access_token() -> str:
    """Returns a usable access token, transparently refreshing (and
    persisting) it first if it has expired.
    """
    data = _load_raw()
    if data is None:
        raise RuntimeError(
            "No Google Calendar connection yet. Visit /auth/google/login in a browser first."
        )

    expires_at = datetime.fromisoformat(data["expires_at"])
    if expires_at > datetime.now(timezone.utc):
        return data["access_token"]

    if not data.get("refresh_token"):
        raise RuntimeError(
            "Google Calendar session expired and no refresh token was saved. "
            "Visit /auth/google/login again."
        )

    token_data = _refresh_access_token(data["refresh_token"])
    save_tokens(token_data)
    return token_data["access_token"]


def fetch_upcoming_events(access_token: str, time_min: datetime, time_max: datetime, max_results: int = 50) -> list[dict]:
    resp = httpx.get(
        f"{API_BASE}/calendars/primary/events",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])
