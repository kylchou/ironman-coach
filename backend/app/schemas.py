from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: int
    name: str | None
    sport_type: str
    start_date: datetime
    distance_m: float | None
    moving_time_s: int | None
    elapsed_time_s: int | None
    total_elevation_gain_m: float | None
    average_speed_mps: float | None
    max_speed_mps: float | None
    average_heartrate: float | None
    max_heartrate: float | None
    average_cadence: float | None
    calories: float | None


class AthleteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garmin_email: str
    display_name: str | None


class SyncResult(BaseModel):
    fetched: int
    created: int
    updated: int


class DailyWeatherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str
    temp_max_f: float | None
    temp_min_f: float | None
    precipitation_in: float | None
    wind_speed_max_mph: float | None
    weather_code: int | None
    conditions: str


class CurrentWeatherOut(BaseModel):
    temperature_f: float | None
    conditions: str
    weather_code: int | None
    wind_speed_mph: float | None
    relative_humidity_pct: float | None


class WeatherNowOut(BaseModel):
    latitude: float
    longitude: float
    current: CurrentWeatherOut
    daily_forecast: list[DailyWeatherOut]
