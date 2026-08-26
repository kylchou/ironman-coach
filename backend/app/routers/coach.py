from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CoachBriefOut
from app.services.ai_coach import generate_daily_brief

router = APIRouter(prefix="/coach", tags=["coach"])


@router.post("/brief", response_model=CoachBriefOut)
def daily_brief(db: Session = Depends(get_db)):
    """Generates a fresh AI coaching brief from current data. A POST, not a
    GET, and deliberately not auto-loaded anywhere -- it's a real Claude API
    call with a real cost, triggered on demand rather than on every
    dashboard refresh.
    """
    try:
        brief = generate_daily_brief(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return CoachBriefOut(brief=brief, generated_at=datetime.now(timezone.utc))
