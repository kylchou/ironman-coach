from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.schemas import CalendarEventOut
from app.services import calendar_client

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEventOut])
def upcoming_events(days: int = Query(default=7, ge=1, le=60)):
    """Upcoming events on the primary Google Calendar, for factoring
    schedule into workout recommendations later.
    """
    try:
        access_token = calendar_client.get_valid_access_token()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    now = datetime.now(timezone.utc)
    raw_events = calendar_client.fetch_upcoming_events(access_token, now, now + timedelta(days=days))

    events = []
    for e in raw_events:
        start = e.get("start", {})
        end = e.get("end", {})
        is_all_day = "date" in start  # timed events use "dateTime" instead
        events.append(
            CalendarEventOut(
                id=e["id"],
                summary=e.get("summary", "(No title)"),
                start=start.get("dateTime") or start.get("date", ""),
                end=end.get("dateTime") or end.get("date", ""),
                all_day=is_all_day,
            )
        )
    return events
