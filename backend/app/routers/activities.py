from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity, Athlete
from app.schemas import ActivityOut, SyncResult
from app.services import strava_client

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
            detail="No connected athletes yet. Visit /auth/strava/login first.",
        )
    if len(athletes) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple athletes connected; pass ?athlete_id=<id> to disambiguate.",
        )
    return athletes[0]


@router.post("/activities/sync", response_model=SyncResult)
def sync_activities(
    athlete_id: int | None = None,
    pages: int = Query(default=1, ge=1, le=10, description="How many pages of 100 to pull"),
    db: Session = Depends(get_db),
):
    """Pull recent activities from Strava and upsert them into the database."""
    athlete = _get_athlete(db, athlete_id)
    access_token = strava_client.ensure_fresh_token(athlete)

    fetched, created, updated = 0, 0, 0
    for page in range(1, pages + 1):
        batch = strava_client.fetch_activities(access_token, per_page=100, page=page)
        if not batch:
            break
        fetched += len(batch)

        for raw in batch:
            existing = (
                db.query(Activity)
                .filter_by(strava_activity_id=raw["id"])
                .one_or_none()
            )
            if existing is None:
                existing = Activity(athlete_id=athlete.id, strava_activity_id=raw["id"])
                db.add(existing)
                created += 1
            else:
                updated += 1

            existing.name = raw.get("name")
            existing.sport_type = raw.get("sport_type") or raw.get("type", "Unknown")
            existing.start_date = raw["start_date"]
            existing.distance_m = raw.get("distance")
            existing.moving_time_s = raw.get("moving_time")
            existing.elapsed_time_s = raw.get("elapsed_time")
            existing.total_elevation_gain_m = raw.get("total_elevation_gain")
            existing.average_speed_mps = raw.get("average_speed")
            existing.max_speed_mps = raw.get("max_speed")
            existing.average_heartrate = raw.get("average_heartrate")
            existing.max_heartrate = raw.get("max_heartrate")
            existing.average_cadence = raw.get("average_cadence")
            existing.calories = raw.get("calories")
            existing.raw = raw

    db.commit()
    return SyncResult(fetched=fetched, created=created, updated=updated)


@router.get("/activities", response_model=list[ActivityOut])
def list_activities(
    athlete_id: int | None = None,
    sport_type: str | None = Query(default=None, description="Filter e.g. Run, Ride, Swim"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    athlete = _get_athlete(db, athlete_id)
    q = db.query(Activity).filter_by(athlete_id=athlete.id)
    if sport_type:
        q = q.filter_by(sport_type=sport_type)
    return q.order_by(Activity.start_date.desc()).limit(limit).all()
