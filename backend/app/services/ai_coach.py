"""Daily AI coaching brief: gathers everything the app already knows (Phases
1-5 -- recent activities, readiness score, training load, weather, upcoming
schedule) into one prompt and asks an LLM to explain it in plain language
and suggest what to do in the next few days.

Deliberately a single call, not an agent -- this is a straightforward
"summarize + advise" task over data we've already computed, not something
that benefits from tool use or multi-step exploration.

Uses the Gemini API (free tier) via plain REST/httpx rather than the
`google-generativeai` SDK or Claude -- see README for why: this machine's
Application Control policy blocks the `cryptography` package that Google's
official Python libraries pull in, and the free tier is genuinely free
where Claude's API is pay-as-you-go (a cheap per-call cost, but not $0).
"""

from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Activity
from app.services import calendar_client, garmin_client, weather_client
from app.services.location import get_location
from app.services.readiness import compute_readiness
from app.services.training_load import compute_ctl_atl_tsb, daily_loads_from_activities, form_label

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = """You are an experienced, encouraging Ironman triathlon coach reviewing one \
athlete's recent data. You are given their readiness score, recent swim/bike/run history, \
training load, upcoming schedule, and weather.

Write a short daily briefing in plain, friendly language -- no jargon dumps, no restating every \
number you were given. Structure it as:
1. One or two sentences on how they're doing right now and why (reference the readiness score \
and what's driving it).
2. Two or three concrete, specific suggestions for the next few days -- what kind of session, \
roughly how hard, and note any real constraint from their calendar or the weather forecast that \
should shape it (e.g. a packed class day, an upcoming thunderstorm).

Keep it to about 150-200 words total. Don't be alarmist about normal day-to-day fluctuations. \
Don't recommend anything that ignores a schedule conflict or bad weather you were told about."""


def _recent_activity_lines(db: Session, days: int = 14) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    activities = (
        db.query(Activity)
        .filter(Activity.start_date >= since)
        .order_by(Activity.start_date.desc())
        .all()
    )
    if not activities:
        return "No activities logged in the last 14 days."

    lines = []
    for a in activities:
        dist_km = (a.distance_m or 0) / 1000
        mins = (a.moving_time_s or 0) / 60
        hr = f", avg HR {round(a.average_heartrate)}" if a.average_heartrate else ""
        lines.append(
            f"- {a.start_date.date().isoformat()} {a.sport_type}: {dist_km:.1f} km, {mins:.0f} min{hr}"
        )
    return "\n".join(lines)


def _weekly_load_lines(db: Session) -> str:
    since = date.today() - timedelta(weeks=4)
    activities = db.query(Activity).filter(Activity.start_date >= since).all()
    max_hr = db.query(func.max(Activity.max_heartrate)).scalar()
    daily_loads = daily_loads_from_activities(activities, max_hr)
    total = sum(daily_loads.values())
    return f"Total training load over the last 4 weeks: {total:.0f} (higher = more/harder training)."


def _readiness_summary(db: Session) -> str:
    today = date.today()
    max_hr = db.query(func.max(Activity.max_heartrate)).scalar()
    all_activities = db.query(Activity).filter(Activity.start_date <= today + timedelta(days=1)).all()
    daily_loads = daily_loads_from_activities(all_activities, max_hr)
    tsb_row = compute_ctl_atl_tsb(daily_loads, today, today)[0]

    sleep = hrv = resting_hr = resting_hr_baseline = None
    try:
        client = garmin_client.get_client()
        sleep = garmin_client.fetch_sleep_score(client, today) or garmin_client.fetch_sleep_score(
            client, today - timedelta(days=1)
        )
        hrv = garmin_client.fetch_hrv_status(client, today)
        resting_hr = garmin_client.fetch_resting_hr(client, today)
        resting_hr_baseline = garmin_client.fetch_resting_hr_baseline(client, today)
    except RuntimeError:
        pass  # no Garmin session -- readiness will just use TSB alone

    result = compute_readiness(tsb_row["tsb"], hrv, sleep, resting_hr, resting_hr_baseline)

    if resting_hr is not None and resting_hr_baseline is not None:
        rhr_text = f"{resting_hr} (baseline {resting_hr_baseline:.0f})"
    else:
        rhr_text = "no data"

    return (
        f"Readiness score: {result.score}/100 ({result.label}). "
        f"Training form (TSB): {tsb_row['tsb']:.1f} ({form_label(tsb_row['tsb'])}). "
        f"HRV status: {hrv['status'] if hrv else 'no data'}. "
        f"Sleep score: {sleep['score'] if sleep else 'no data'}. "
        f"Resting HR: {rhr_text}."
    )


def _weather_summary(db: Session) -> str:
    try:
        lat, lon = get_location(db)
        forecast = weather_client.fetch_forecast(lat, lon, days=4)
    except Exception:  # noqa: BLE001 -- weather is optional context, not worth failing the brief over
        return "Weather forecast unavailable."

    lines = []
    for i, d in enumerate(forecast["daily"]["time"]):
        code = forecast["daily"]["weather_code"][i]
        hi = forecast["daily"]["temperature_2m_max"][i]
        lo = forecast["daily"]["temperature_2m_min"][i]
        lines.append(f"- {d}: {weather_client.describe_weather_code(code)}, {lo:.0f}-{hi:.0f}°F")
    return "\n".join(lines)


def _calendar_summary() -> str:
    try:
        access_token = calendar_client.get_valid_access_token()
    except RuntimeError:
        return "Calendar not connected."

    now = datetime.now(timezone.utc)
    events = calendar_client.fetch_upcoming_events(access_token, now, now + timedelta(days=7))
    if not events:
        return "Nothing on the calendar for the next 7 days."
    lines = [f"- {e.get('summary', '(no title)')} ({(e.get('start') or {}).get('dateTime') or (e.get('start') or {}).get('date')})" for e in events[:20]]
    return "\n".join(lines)


def generate_daily_brief(db: Session) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set in backend/.env. Get a free one (no credit "
            "card) at https://aistudio.google.com/apikey"
        )

    context = f"""READINESS
{_readiness_summary(db)}

TRAINING LOAD (last 4 weeks)
{_weekly_load_lines(db)}

RECENT ACTIVITIES (last 14 days)
{_recent_activity_lines(db)}

WEATHER FORECAST (next 4 days)
{_weather_summary(db)}

UPCOMING SCHEDULE (next 7 days)
{_calendar_summary()}
"""

    url = GEMINI_URL.format(model=settings.gemini_model)
    resp = httpx.post(
        url,
        params={"key": settings.gemini_api_key},
        json={
            "contents": [{"role": "user", "parts": [{"text": context}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {"maxOutputTokens": 1024},
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        # Most commonly a safety block -- promptFeedback carries the reason.
        reason = (data.get("promptFeedback") or {}).get("blockReason", "no candidates returned")
        raise RuntimeError(f"Gemini returned no response ({reason}).")

    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)
