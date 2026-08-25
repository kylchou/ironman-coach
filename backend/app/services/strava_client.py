"""Thin wrapper around the Strava v3 API: OAuth token exchange/refresh and
fetching activities. See https://developers.strava.com/docs/reference/
"""

from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx

from app.config import settings

AUTH_BASE = "https://www.strava.com/oauth"
API_BASE = "https://www.strava.com/api/v3"


def authorize_url(state: str) -> str:
    """URL to send the user to so they can approve access to their Strava data."""
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        # activity:read_all is needed to see private activities too.
        "scope": "read,activity:read_all",
        "state": state,
        "approval_prompt": "auto",
    }
    return f"{AUTH_BASE}/authorize?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Trade a one-time OAuth `code` for access/refresh tokens + athlete info."""
    resp = httpx.post(
        f"{AUTH_BASE}/token",
        data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> dict:
    """Get a new access token using a stored refresh token. Strava rotates the
    refresh token on every call, so callers must persist the new one too.
    """
    resp = httpx.post(
        f"{AUTH_BASE}/token",
        data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def ensure_fresh_token(athlete) -> str:
    """Return a valid access token for `athlete`, refreshing (and persisting)
    it first if it has expired. Caller is responsible for committing the
    session afterwards.
    """
    now = datetime.now(timezone.utc)
    if athlete.token_expires_at.tzinfo is None:
        expires_at = athlete.token_expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = athlete.token_expires_at

    if expires_at > now:
        return athlete.access_token

    token_data = refresh_access_token(athlete.refresh_token)
    athlete.access_token = token_data["access_token"]
    athlete.refresh_token = token_data["refresh_token"]
    athlete.token_expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)
    return athlete.access_token


def fetch_activities(access_token: str, per_page: int = 100, page: int = 1) -> list[dict]:
    """Fetch one page of the athlete's activities, newest first."""
    resp = httpx.get(
        f"{API_BASE}/athlete/activities",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"per_page": per_page, "page": page},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
