"""Wrapper around Garmin Connect via the unofficial `garminconnect` library
(https://github.com/cyberjunky/python-garminconnect). There is no free
official API for personal use, so this talks to the same endpoints the
Garmin Connect app/website use, authenticated as your own account.

Your password is never stored. Run scripts/garmin_login.py once (from the
backend/ directory, with the venv active) to log in interactively -- it
caches session tokens to .garmin_tokens/, which this module then resumes.
Re-run that script if the cached session ever expires or gets revoked.
"""

from pathlib import Path

from garminconnect import Garmin

TOKEN_DIR = Path(__file__).resolve().parents[2] / ".garmin_tokens"

# Garmin's activityType.typeKey values, collapsed down to the three
# disciplines this app cares about. Anything not listed here is passed
# through title-cased (e.g. "strength_training" -> "Strength Training").
SPORT_MAP = {
    "running": "Run",
    "treadmill_running": "Run",
    "trail_running": "Run",
    "track_running": "Run",
    "indoor_running": "Run",
    "cycling": "Ride",
    "road_biking": "Ride",
    "indoor_cycling": "Ride",
    "virtual_ride": "Ride",
    "mountain_biking": "Ride",
    "gravel_cycling": "Ride",
    "cyclocross": "Ride",
    "lap_swimming": "Swim",
    "open_water_swimming": "Swim",
}


def get_client() -> Garmin:
    """Return an authenticated Garmin client, resuming the cached session.

    Deliberately does not accept email/password or an MFA callback here --
    if the cached session is missing or has gone stale, this should fail
    loudly rather than hang the API server waiting on interactive input.
    """
    if not TOKEN_DIR.exists():
        raise RuntimeError(
            "No cached Garmin session found. From backend/, with the venv "
            "active, run: python scripts/garmin_login.py"
        )
    client = Garmin()
    try:
        client.login(tokenstore=str(TOKEN_DIR))
    except Exception as exc:  # noqa: BLE001 -- surfacing as an actionable message
        raise RuntimeError(
            "Cached Garmin session is invalid or expired. Re-run "
            "`python scripts/garmin_login.py` from backend/ to log in again."
        ) from exc
    return client


def normalize_sport_type(type_key: str | None) -> str:
    if not type_key:
        return "Other"
    return SPORT_MAP.get(type_key, type_key.replace("_", " ").title())


def fetch_activities(client: Garmin, start: int = 0, limit: int = 100) -> list[dict]:
    """Fetch one page of the athlete's activities, newest first."""
    activities = client.get_activities(start, limit)
    return activities or []
