from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity
from app.schemas import DailyFitnessOut, HrvPointOut, ReadinessOut, RestingHrPointOut
from app.services import garmin_client
from app.services import readiness as readiness_service
from app.services.training_load import compute_ctl_atl_tsb, daily_loads_from_activities, form_label

router = APIRouter(prefix="/readiness", tags=["readiness"])


def _ctl_atl_tsb_for_range(db: Session, start: date, end: date) -> list[dict]:
    max_hr_observed = db.query(func.max(Activity.max_heartrate)).scalar()
    # Everything up to `end` is needed to seed the rolling averages correctly,
    # not just activities inside [start, end].
    activities = db.query(Activity).filter(Activity.start_date <= end + timedelta(days=1)).all()
    daily_loads = daily_loads_from_activities(activities, max_hr_observed)
    return compute_ctl_atl_tsb(daily_loads, start, end)


@router.get("/today", response_model=ReadinessOut)
def today(db: Session = Depends(get_db)):
    """Today's composite readiness score: Training Stress Balance (from our
    own synced activities) blended with Garmin's HRV/sleep/resting-HR data.
    """
    today_date = date.today()
    tsb_row = _ctl_atl_tsb_for_range(db, today_date, today_date)[0]

    try:
        client = garmin_client.get_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    sleep = garmin_client.fetch_sleep_detail(client, today_date)
    if sleep is None:
        # This morning's sleep may not have synced yet -- fall back a day.
        sleep = garmin_client.fetch_sleep_detail(client, today_date - timedelta(days=1))
    hrv = garmin_client.fetch_hrv_status(client, today_date)
    resting_hr = garmin_client.fetch_resting_hr(client, today_date)
    resting_hr_baseline = garmin_client.fetch_resting_hr_baseline(client, today_date)

    result = readiness_service.compute_readiness(
        tsb=tsb_row["tsb"],
        hrv_status=hrv,
        sleep=sleep,
        resting_hr=resting_hr,
        resting_hr_baseline=resting_hr_baseline,
    )

    return ReadinessOut(
        date=today_date.isoformat(),
        score=result.score,
        label=result.label,
        fitness_ctl=tsb_row["ctl"],
        fatigue_atl=tsb_row["atl"],
        form_tsb=tsb_row["tsb"],
        form_label=form_label(tsb_row["tsb"]),
        components=result.components,
    )


@router.get("/history", response_model=list[DailyFitnessOut])
def history(days: int = Query(default=90, ge=7, le=730), db: Session = Depends(get_db)):
    """Daily Fitness/Fatigue/Form series, for a Performance-Management-Chart
    style view of training load balance over time.
    """
    end = date.today()
    start = end - timedelta(days=days)
    rows = _ctl_atl_tsb_for_range(db, start, end)
    return [DailyFitnessOut(date=r["date"].isoformat(), ctl=r["ctl"], atl=r["atl"], tsb=r["tsb"]) for r in rows]


@router.get("/resting-hr", response_model=list[RestingHrPointOut])
def resting_hr_history(days: int = Query(default=7, ge=1, le=90)):
    """Daily resting HR for the last `days` days (1 = today only), for the
    dashboard's expandable RHR history view.
    """
    try:
        client = garmin_client.get_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    end = date.today()
    start = end - timedelta(days=days - 1)
    points = garmin_client.fetch_resting_hr_range(client, start, end)
    return [RestingHrPointOut(**p) for p in points]


@router.get("/hrv", response_model=list[HrvPointOut])
def hrv_history(days: int = Query(default=7, ge=1, le=90)):
    """Daily HRV (last night's average) + status + that day's baseline
    range for the last `days` days, for the dashboard's HRV chart.
    """
    try:
        client = garmin_client.get_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    end = date.today()
    start = end - timedelta(days=days - 1)
    points = garmin_client.fetch_hrv_range(client, start, end)
    return [HrvPointOut(**p) for p in points]
