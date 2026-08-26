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


class CalendarEventOut(BaseModel):
    id: str
    summary: str
    start: str  # ISO datetime, or a bare date ("2026-08-26") if all-day
    end: str
    all_day: bool


class SportLoadOut(BaseModel):
    load: float
    distance_m: float
    time_s: int
    sessions: int


class WeeklyLoadOut(BaseModel):
    week_start: str  # ISO date (Monday)
    by_sport: dict[str, SportLoadOut]
    total_load: float


class TrendPointOut(BaseModel):
    week_start: str  # ISO date (Monday)
    avg_speed_mps: float | None
    avg_heartrate: float | None
    distance_m: float
    sessions: int


class DailyFitnessOut(BaseModel):
    date: str
    ctl: float  # "Fitness" -- 42-day rolling load average
    atl: float  # "Fatigue" -- 7-day rolling load average
    tsb: float  # "Form" -- ctl - atl


class TsbComponentOut(BaseModel):
    value: float
    score: float


class HrvComponentOut(BaseModel):
    status: str | None
    score: float | None


class SleepComponentOut(BaseModel):
    value: float | None
    qualifier: str | None
    score: float | None


class RestingHrComponentOut(BaseModel):
    value: float | None
    baseline: float | None
    score: float | None


class ReadinessComponentsOut(BaseModel):
    tsb: TsbComponentOut
    hrv: HrvComponentOut
    sleep: SleepComponentOut
    resting_hr: RestingHrComponentOut


class ReadinessOut(BaseModel):
    date: str
    score: float
    label: str
    fitness_ctl: float
    fatigue_atl: float
    form_tsb: float
    form_label: str
    components: ReadinessComponentsOut
