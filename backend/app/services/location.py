"""Training location resolution, shared by weather.py and ai_coach.py."""

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Activity


def get_location(db: Session) -> tuple[float, float]:
    """Fixed location from settings if set, otherwise the coordinates of the
    most recent GPS-tagged activity (outdoor runs/rides carry startLatitude/
    startLongitude in their raw Garmin payload).
    """
    if settings.location_lat is not None and settings.location_lon is not None:
        return settings.location_lat, settings.location_lon

    recent = (
        db.query(Activity)
        .filter(Activity.raw["startLatitude"].isnot(None))
        .order_by(Activity.start_date.desc())
        .first()
    )
    if recent is not None:
        lat = recent.raw.get("startLatitude")
        lon = recent.raw.get("startLongitude")
        if lat is not None and lon is not None:
            return lat, lon

    raise RuntimeError(
        "No location available. Set LOCATION_LAT/LOCATION_LON in backend/.env, "
        "or sync at least one outdoor (GPS-tagged) activity first."
    )
