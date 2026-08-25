from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Activity, Athlete
from app.schemas import ActivityOut, SyncResult
from app.services import garmin_client

router = APIRouter(tags=["activities"])


def _get_athlete(db: Session, athlete_id: int | None) -> Athlete:
    """Resolve the target athlete. With `athlete_id` omitted, falls back to
    the only connected athlete -- convenient while this is a single-user app.
    """
    if athlete_id is not None:
        athlete = db.get(Athlete, athlete_id)
        if athlete is None:
            raise HTTPException(status_code=404, detail=f"No athlete with id {athlete_id}")
        return athlete

    athletes = db.query(Athlete).all()
    if len(athletes) == 0:
        raise HTTPException(
            status_code=404,
            detail="No connected athletes yet. Run `POST /activities/sync` once you've "
            "completed `python scripts/garmin_login.py`.",
        )
    if len(athletes) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple athletes connected; pass ?athlete_id=<id> to disambiguate.",
        )
    return athletes[0]


def _get_or_create_athlete(db: Session, client) -> Athlete:
    key = settings.garmin_email or client.get_full_name() or "default"
    athlete = db.query(Athlete).filter_by(garmin_email=key).one_or_none()
    if athlete is None:
        athlete = Athlete(garmin_email=key, display_name=client.get_full_name())
        db.add(athlete)
        db.flush()
    else:
        athlete.display_name = client.get_full_name()
    return athlete


@router.post("/activities/sync", response_model=SyncResult)
def sync_activities(
    pages: int = Query(default=1, ge=1, le=10, description="How many pages of 100 to pull"),
    db: Session = Depends(get_db),
):
    """Pull recent activities from Garmin and upsert them into the database."""
    try:
        client = garmin_client.get_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    athlete = _get_or_create_athlete(db, client)

    fetched, created, updated = 0, 0, 0
    for page in range(pages):
        batch = garmin_client.fetch_activities(client, start=page * 100, limit=100)
        if not batch:
            break
        fetched += len(batch)

        for raw in batch:
            external_id = raw["activityId"]
            existing = (
                db.query(Activity)
                .filter_by(source="garmin", external_id=external_id)
                .one_or_none()
            )
            if existing is None:
                existing = Activity(athlete_id=athlete.id, source="garmin", external_id=external_id)
                db.add(existing)
                created += 1
            else:
                updated += 1

            activity_type = (raw.get("activityType") or {}).get("typeKey")

            existing.name = raw.get("activityName")
            existing.sport_type = garmin_client.normalize_sport_type(activity_type)
            existing.start_date = raw.get("startTimeGMT") or raw.get("startTimeLocal")
            elapsed = raw.get("duration")
            moving = raw.get("movingDuration") or elapsed
            # Garmin occasionally reports a wildly corrupted movingDuration on
            # some pool swims (seen: ~193h for a 61-minute swim). Moving time
            # can never exceed elapsed time, so fall back when that happens.
            if moving is not None and elapsed is not None and moving > elapsed:
                moving = elapsed

            existing.distance_m = raw.get("distance")
            existing.moving_time_s = moving
            existing.elapsed_time_s = elapsed
            existing.total_elevation_gain_m = raw.get("elevationGain")
            existing.average_speed_mps = raw.get("averageSpeed")
            existing.max_speed_mps = raw.get("maxSpeed")
            existing.average_heartrate = raw.get("averageHR")
            existing.max_heartrate = raw.get("maxHR")
            existing.average_cadence = (
                raw.get("averageRunningCadenceInStepsPerMinute")
                or raw.get("averageBikingCadenceInRevPerMinute")
            )
            existing.calories = raw.get("calories")
            existing.raw = raw

    db.commit()
    return SyncResult(fetched=fetched, created=created, updated=updated)


@router.get("/activities", response_model=list[ActivityOut])
def list_activities(
    athlete_id: int | None = None,
    sport_type: str | None = Query(default=None, description="Filter e.g. Run, Ride, Swim"),
    limit: int = Query(default=50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    athlete = _get_athlete(db, athlete_id)
    q = db.query(Activity).filter_by(athlete_id=athlete.id)
    if sport_type:
        q = q.filter_by(sport_type=sport_type)
    return q.order_by(Activity.start_date.desc()).limit(limit).all()
