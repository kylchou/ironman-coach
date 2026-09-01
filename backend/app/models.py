from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    """Timezone-AWARE UTC now, for created_at defaults. `datetime.utcnow()`
    (used here until this was caught) returns a naive datetime that
    psycopg2 stores using the session's local timezone instead of literal
    UTC -- every created_at in this app was silently off by the local UTC
    offset. Always use this instead.
    """
    return datetime.now(timezone.utc)


class Athlete(Base):
    """A connected athlete, one row per person who has linked a data source."""

    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    garmin_email: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    activities: Mapped[list["Activity"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")


class Activity(Base):
    """A single workout (swim / bike / run for now)."""

    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_activities_source_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), index=True)

    # "garmin" for now; keeps the door open for adding Strava/others later
    # without a schema change.
    source: Mapped[str] = mapped_column(String, index=True, default="garmin")
    external_id: Mapped[int] = mapped_column(BigInteger, index=True)

    name: Mapped[str | None] = mapped_column(String, nullable=True)
    sport_type: Mapped[str] = mapped_column(String, index=True)  # "Run", "Ride", "Swim", etc.
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    moving_time_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    elapsed_time_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_elevation_gain_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    average_speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_heartrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Full raw payload from the source API, kept as-is so later phases
    # (training load, laps) can backfill new fields without a re-sync.
    raw: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    athlete: Mapped["Athlete"] = relationship(back_populates="activities")


class DailyWeather(Base):
    """One day's weather at the training location (from Open-Meteo).

    Single location for now, matching the single-athlete assumption
    elsewhere -- revisit alongside Athlete if this ever supports multiple
    people/locations.
    """

    __tablename__ = "daily_weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    temp_max_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_min_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_max_mph: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    raw: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Task(Base):
    """A single to-do item -- manually added, or synced in from an external
    source (Canvas assignments today; calendar-derived tasks later, maybe).

    Deliberately one table for everything completable, not separate
    Assignment/Todo tables: the whole point of this feature is one unified
    list instead of checking Canvas and a to-do app separately. `source` +
    `external_id` is how synced rows get upserted instead of duplicated.
    """

    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_tasks_source_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    completed: Mapped[bool] = mapped_column(default=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # "manual" for tasks you add yourself; "canvas" for synced assignments.
    source: Mapped[str] = mapped_column(String, index=True, default="manual")
    # Canvas assignment id, etc. -- null for manual tasks (no external record).
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. link to the Canvas assignment page
    course_name: Mapped[str | None] = mapped_column(String, nullable=True)  # Canvas course, if applicable

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
