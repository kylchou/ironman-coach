from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Task
from app.schemas import SyncResult, TaskCreateIn, TaskOut, TaskUpdateIn
from app.services import canvas_client

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(include_completed: bool = False, db: Session = Depends(get_db)):
    """The unified list: manual tasks and synced Canvas assignments together,
    soonest due date first. Tasks with no due date sort last.
    """
    q = db.query(Task)
    if not include_completed:
        q = q.filter(Task.completed.is_(False))
    tasks = q.all()
    tasks.sort(key=lambda t: (t.due_date is None, t.due_date, t.created_at))
    return tasks


@router.post("", response_model=TaskOut)
def create_task(body: TaskCreateIn, db: Session = Depends(get_db)):
    task = Task(title=body.title, description=body.description, due_date=body.due_date, source="manual")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdateIn, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"No task with id {task_id}")

    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.due_date is not None:
        task.due_date = body.due_date
    if body.completed is not None:
        task.completed = body.completed
        task.completed_at = datetime.now(timezone.utc) if body.completed else None

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"No task with id {task_id}")
    db.delete(task)
    db.commit()


@router.post("/sync-canvas", response_model=SyncResult)
def sync_canvas(db: Session = Depends(get_db)):
    """Pulls assignments Canvas considers still needing action and upserts
    them into the unified task list.
    """
    if not settings.canvas_access_token:
        raise HTTPException(
            status_code=500,
            detail="CANVAS_ACCESS_TOKEN is not set in backend/.env. See README for how to "
            "generate one in Canvas (Account -> Settings -> New Access Token).",
        )

    try:
        course_names = canvas_client.fetch_course_names()
        todo_items = canvas_client.fetch_todo_assignments()
    except Exception as exc:  # noqa: BLE001 -- surface Canvas/network errors clearly
        raise HTTPException(status_code=502, detail=f"Failed to reach Canvas: {exc}") from exc

    fetched, created, updated = 0, 0, 0
    for item in todo_items:
        assignment = item["assignment"]
        external_id = str(assignment["id"])
        fetched += 1

        existing = db.query(Task).filter_by(source="canvas", external_id=external_id).one_or_none()
        if existing is None:
            existing = Task(source="canvas", external_id=external_id)
            db.add(existing)
            created += 1
        else:
            updated += 1

        existing.title = assignment.get("name") or "Untitled assignment"
        due_at = assignment.get("due_at")
        existing.due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00")) if due_at else None
        existing.source_url = assignment.get("html_url") or item.get("html_url")
        course_id = item.get("course_id") or assignment.get("course_id")
        existing.course_name = course_names.get(course_id)

    db.commit()
    return SyncResult(fetched=fetched, created=created, updated=updated)
