import secrets

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.config import settings
from app.services import calendar_client

router = APIRouter(prefix="/auth/google", tags=["google-auth"])

# In-memory CSRF state store -- fine for a single-user local app, same as
# the (now-removed) Strava flow used. See garmin_login.py's docstring
# pattern for why this doesn't need to be more robust here.
_pending_states: set[str] = set()


@router.get("/login")
def login():
    """Redirect the browser to Google's OAuth consent screen."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are not set in backend/.env. "
            "See the README for how to create them in Google Cloud Console.",
        )
    state = secrets.token_urlsafe(16)
    _pending_states.add(state)
    return RedirectResponse(calendar_client.authorize_url(state))


@router.get("/callback")
def callback(code: str, state: str):
    """Google redirects here after the user approves (or denies) access."""
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Unknown or expired OAuth state")
    _pending_states.discard(state)

    token_data = calendar_client.exchange_code_for_token(code)
    calendar_client.save_tokens(token_data)

    return {"message": "Google Calendar connected."}


@router.get("/status")
def status():
    try:
        calendar_client.get_valid_access_token()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"connected": True}
