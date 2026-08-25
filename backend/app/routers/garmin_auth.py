from fastapi import APIRouter, HTTPException

from app.services import garmin_client

router = APIRouter(prefix="/auth/garmin", tags=["garmin-auth"])


@router.get("/status")
def status():
    """Check whether a cached Garmin session exists and still works.

    Login itself happens out-of-band via `python scripts/garmin_login.py`
    (interactive, so it can prompt for MFA) -- this just reports on it.
    """
    try:
        client = garmin_client.get_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return {"connected": True, "name": client.get_full_name()}
