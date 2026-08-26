from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DailyWeather
from app.schemas import CurrentWeatherOut, DailyWeatherOut, SyncResult, WeatherNowOut
from app.services import weather_client
from app.services.location import get_location

router = APIRouter(prefix="/weather", tags=["weather"])


def _get_location(db: Session) -> tuple[float, float]:
    try:
        return get_location(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _daily_from_forecast_json(payload: dict) -> list[DailyWeatherOut]:
    daily = payload["daily"]
    out = []
    for i, day_str in enumerate(daily["time"]):
        code = daily["weather_code"][i]
        out.append(
            DailyWeatherOut(
                date=day_str,
                temp_max_f=daily["temperature_2m_max"][i],
                temp_min_f=daily["temperature_2m_min"][i],
                precipitation_in=daily["precipitation_sum"][i],
                wind_speed_max_mph=daily["wind_speed_10m_max"][i],
                weather_code=code,
                conditions=weather_client.describe_weather_code(code),
            )
        )
    return out


@router.get("/current", response_model=WeatherNowOut)
def current_weather(db: Session = Depends(get_db)):
    """Live current conditions + a 7-day forecast at the training location.
    Not persisted -- this changes constantly, unlike /weather/daily history.
    """
    lat, lon = _get_location(db)
    payload = weather_client.fetch_forecast(lat, lon, days=7)

    current = payload["current"]
    return WeatherNowOut(
        latitude=payload["latitude"],
        longitude=payload["longitude"],
        current=CurrentWeatherOut(
            temperature_f=current.get("temperature_2m"),
            conditions=weather_client.describe_weather_code(current.get("weather_code")),
            weather_code=current.get("weather_code"),
            wind_speed_mph=current.get("wind_speed_10m"),
            relative_humidity_pct=current.get("relative_humidity_2m"),
        ),
        daily_forecast=_daily_from_forecast_json(payload),
    )


@router.post("/sync", response_model=SyncResult)
def sync_daily_weather(
    days_back: int = Query(default=30, ge=1, le=1100, description="How many past days to backfill"),
    db: Session = Depends(get_db),
):
    """Backfill daily weather at the training location for the past
    `days_back` days, so it can be joined against training history later
    (e.g. was it hot/rainy on the day of a given workout).

    Uses the archive endpoint, which lags a few days behind "today" -- the
    most recent day or two may come back with null values, which are
    skipped rather than stored. /weather/current covers today/upcoming.
    """
    lat, lon = _get_location(db)

    end = date.today()
    start = end - timedelta(days=days_back)

    archive_payload = weather_client.fetch_historical(lat, lon, start, end)
    all_days = _daily_from_forecast_json(archive_payload)

    fetched, created, updated = 0, 0, 0
    for day in all_days:
        if day.temp_max_f is None and day.temp_min_f is None:
            continue  # archive hasn't caught up to this date yet
        day_date = date.fromisoformat(day.date)
        fetched += 1

        existing = db.query(DailyWeather).filter_by(date=day_date).one_or_none()
        if existing is None:
            existing = DailyWeather(date=day_date, latitude=lat, longitude=lon)
            db.add(existing)
            created += 1
        else:
            updated += 1

        existing.temp_max_f = day.temp_max_f
        existing.temp_min_f = day.temp_min_f
        existing.precipitation_in = day.precipitation_in
        existing.wind_speed_max_mph = day.wind_speed_max_mph
        existing.weather_code = day.weather_code
        existing.raw = day.model_dump()

    db.commit()
    return SyncResult(fetched=fetched, created=created, updated=updated)


@router.get("/daily", response_model=list[DailyWeatherOut])
def list_daily_weather(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(DailyWeather)
    if start:
        q = q.filter(DailyWeather.date >= start)
    if end:
        q = q.filter(DailyWeather.date <= end)

    rows = q.order_by(DailyWeather.date.asc()).all()
    return [
        DailyWeatherOut(
            date=row.date.isoformat(),
            temp_max_f=row.temp_max_f,
            temp_min_f=row.temp_min_f,
            precipitation_in=row.precipitation_in,
            wind_speed_max_mph=row.wind_speed_max_mph,
            weather_code=row.weather_code,
            conditions=weather_client.describe_weather_code(row.weather_code),
        )
        for row in rows
    ]
