from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strava_activity_id: int
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
    strava_athlete_id: int
    first_name: str | None
    last_name: str | None


class SyncResult(BaseModel):
    fetched: int
    created: int
    updated: int
