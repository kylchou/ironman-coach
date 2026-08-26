from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import activities, analytics, calendar, coach, garmin_auth, google_auth, readiness, weather

app = FastAPI(title="Ironman Coach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(garmin_auth.router)
app.include_router(weather.router)
app.include_router(google_auth.router)
app.include_router(calendar.router)
app.include_router(analytics.router)
app.include_router(readiness.router)
app.include_router(coach.router)
app.include_router(activities.router)


@app.get("/health")
def health():
    return {"status": "ok"}
