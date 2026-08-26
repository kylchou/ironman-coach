"""Wrapper around Garmin Connect via the unofficial `garminconnect` library
(https://github.com/cyberjunky/python-garminconnect). There is no free
official API for personal use, so this talks to the same endpoints the
Garmin Connect app/website use, authenticated as your own account.

Your password is never stored. Run scripts/garmin_login.py once (from the
backend/ directory, with the venv active) to log in interactively -- it
caches session tokens to .garmin_tokens/, which this module then resumes.
Re-run that script if the cached session ever expires or gets revoked.
"""

from datetime import date, timedelta
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


# --- Wellness data, for the daily readiness score (Phase 5) -----------------
# Availability depends on the athlete's specific device/firmware -- every
# function here returns None rather than raising when Garmin has nothing for
# that date, so readiness.py can degrade gracefully instead of failing outright.


def fetch_sleep_score(client: Garmin, d: date) -> dict | None:
    """Garmin's own 0-100 sleep score + qualifier for the sleep period ending
    on the morning of `d`. None if no sleep was recorded (e.g. tonight's
    sleep hasn't synced yet, or the device doesn't track sleep).
    """
    data = client.get_sleep_data(d.isoformat())
    overall = (data or {}).get("dailySleepDTO", {}).get("sleepScores", {}).get("overall")
    if not overall or overall.get("value") is None:
        return None
    return {"score": overall["value"], "qualifier": overall.get("qualifierKey")}


def fetch_hrv_status(client: Garmin, d: date) -> dict | None:
    """Garmin's HRV status classification (e.g. "BALANCED", "UNBALANCED",
    "LOW") for the night ending on `d`. Requires an HRV-capable device.
    """
    data = client.get_hrv_data(d.isoformat())
    summary = (data or {}).get("hrvSummary")
    if not summary or not summary.get("status"):
        return None
    return {
        "status": summary["status"],
        "last_night_avg": summary.get("lastNightAvg"),
        "weekly_avg": summary.get("weeklyAvg"),
    }


def fetch_resting_hr(client: Garmin, d: date) -> float | None:
    data = client.get_rhr_day(d.isoformat())
    metrics = (data or {}).get("allMetrics", {}).get("metricsMap", {})
    entries = metrics.get("WELLNESS_RESTING_HEART_RATE") or []
    return entries[0]["value"] if entries and entries[0].get("value") is not None else None


def fetch_resting_hr_baseline(client: Garmin, before: date, days: int = 30) -> float | None:
    """Average resting HR over the `days` before `before` (exclusive), as a
    personal baseline to compare today's RHR against.
    """
    start = before - timedelta(days=days)
    end = before - timedelta(days=1)
    entries = client.get_rhr_daily(start.isoformat(), end.isoformat()) or []
    values = [e["value"] for e in entries if e and e.get("value") is not None]
    return sum(values) / len(values) if values else None
