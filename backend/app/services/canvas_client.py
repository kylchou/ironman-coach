"""Canvas LMS API wrapper via plain REST (httpx) -- Canvas's API is a
simple bearer-token REST API (no OAuth dance, no SDK needed), same style
as every other integration in this app. Reference:
https://canvas.instructure.com/doc/api/

NOT yet verified against a real Canvas account/token (unlike everything
else in this codebase, which was checked against live data before being
considered done) -- built from documented API shapes. Re-verify field
names here against a real response the first time /tasks/sync-canvas is
actually run, and fix anything that doesn't match.
"""

import httpx

from app.config import settings


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.canvas_access_token}"}


def _base_url() -> str:
    return f"https://{settings.canvas_domain}/api/v1"


def fetch_course_names() -> dict[int, str]:
    """Maps course id -> a human-readable name, for active courses."""
    resp = httpx.get(
        f"{_base_url()}/courses",
        headers=_headers(),
        params={"enrollment_state": "active", "per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    return {c["id"]: c.get("name") or c.get("course_code") or f"Course {c['id']}" for c in resp.json() if c.get("id")}


def fetch_todo_assignments() -> list[dict]:
    """Assignments Canvas considers still needing action (not yet
    submitted), across all active courses. This is Canvas's own "to-do"
    concept, which is why it's the primary source here rather than every
    assignment that ever existed.
    """
    resp = httpx.get(
        f"{_base_url()}/users/self/todo",
        headers=_headers(),
        params={"per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    # Only assignment-type items have an "assignment" key; ungraded-quiz
    # style entries use a different shape we don't handle yet.
    return [item for item in resp.json() if item.get("assignment")]
