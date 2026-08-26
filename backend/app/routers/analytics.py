from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity
from app.schemas import SportLoadOut, TrendPointOut, WeeklyLoadOut
from app.services.training_load import session_load

router = APIRouter(prefix="/analytics", tags=["analytics"])

# The three disciplines this app tracks -- see models.py's sport_type comment.
# Other sport types (Strength Training, Walking, ...) are excluded from load/
# trend charts, which are about swim/bike/run progress specifically.
SPORTS = ("Run", "Ride", "Swim")


def _week_start(d: date) -> date:
    """Monday of the week containing d, used as the bucket key so weeks
    align with a normal training-week view.
    """
    return d - timedelta(days=d.weekday())


def _recent_activities(db: Session, weeks: int, sport: str | None = None) -> list[Activity]:
    since = date.today() - timedelta(weeks=weeks)
    q = db.query(Activity).filter(Activity.start_date >= since)
    if sport:
        q = q.filter(Activity.sport_type == sport)
    return q.all()


@router.get("/weekly-load", response_model=list[WeeklyLoadOut])
def weekly_load(weeks: int = Query(default=12, ge=1, le=52), db: Session = Depends(get_db)):
    """Training load per week, broken down by sport -- the basis for a
    stacked bar chart of recent training volume/intensity.
    """
    max_hr_observed = db.query(func.max(Activity.max_heartrate)).scalar()

    buckets: dict[date, dict[str, dict]] = defaultdict(
        lambda: {s: {"load": 0.0, "distance_m": 0.0, "time_s": 0, "sessions": 0} for s in SPORTS}
    )

    for a in _recent_activities(db, weeks):
        if a.sport_type not in SPORTS:
            continue
        wk = _week_start(a.start_date.date())
        bucket = buckets[wk][a.sport_type]
        bucket["load"] += session_load(a.moving_time_s, a.average_heartrate, max_hr_observed)
        bucket["distance_m"] += a.distance_m or 0
        bucket["time_s"] += a.moving_time_s or 0
        bucket["sessions"] += 1

    return [
        WeeklyLoadOut(
            week_start=wk.isoformat(),
            by_sport={s: SportLoadOut(**{**buckets[wk][s], "load": round(buckets[wk][s]["load"], 1)}) for s in SPORTS},
            total_load=round(sum(buckets[wk][s]["load"] for s in SPORTS), 1),
        )
        for wk in sorted(buckets.keys())
    ]


@router.get("/trends", response_model=list[TrendPointOut])
def trends(
    sport: str = Query(..., description=f"One of {SPORTS}"),
    weeks: int = Query(default=12, ge=1, le=52),
    db: Session = Depends(get_db),
):
    """Weekly average pace/speed and heart rate for one sport, to chart
    progress (or fatigue) over time.
    """
    if sport not in SPORTS:
        raise HTTPException(status_code=400, detail=f"sport must be one of {SPORTS}")

    buckets: dict[date, list[Activity]] = defaultdict(list)
    for a in _recent_activities(db, weeks, sport=sport):
        buckets[_week_start(a.start_date.date())].append(a)

    points = []
    for wk in sorted(buckets.keys()):
        acts = buckets[wk]
        speeds = [a.average_speed_mps for a in acts if a.average_speed_mps]
        hrs = [a.average_heartrate for a in acts if a.average_heartrate]
        points.append(
            TrendPointOut(
                week_start=wk.isoformat(),
                avg_speed_mps=sum(speeds) / len(speeds) if speeds else None,
                avg_heartrate=sum(hrs) / len(hrs) if hrs else None,
                distance_m=sum(a.distance_m or 0 for a in acts),
                sessions=len(acts),
            )
        )
    return points
