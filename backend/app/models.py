from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Athlete(Base):
    """A connected athlete, one row per person who has linked Strava."""

    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strava_athlete_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # OAuth tokens for calling the Strava API on this athlete's behalf.
    access_token: Mapped[str] = mapped_column(String)
    refresh_token: Mapped[str] = mapped_column(String)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    activities: Mapped[list["Activity"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")


class Activity(Base):
    """A single workout, synced from Strava (swim / bike / run for now)."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), index=True)
    strava_activity_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

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

    # Full Strava payload, kept as-is so we can backfill new fields later
    # (e.g. training load, laps) without a migration.
    raw: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    athlete: Mapped["Athlete"] = relationship(back_populates="activities")
