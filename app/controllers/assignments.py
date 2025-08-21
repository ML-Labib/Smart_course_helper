from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.middlewares.auth import login_required
from app.models.course import Lesson, LessonType
from app.models.submission import AssignmentSubmission

router = APIRouter(prefix="/assignments", tags=["assignments"])
templates = Jinja2Templates(directory="app/views")

@router.get("/{lesson_id}")
async def assignment_detail(request: Request, lesson_id: int, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one()
    if lesson.type != LessonType.assignment:
        return RedirectResponse(url="/dashboard", status_code=302)
    sub = (await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.lesson_id == lesson_id, AssignmentSubmission.user_id == user.id))).scalar_one_or_none()
    return templates.TemplateResponse("assignments/detail.html", {"request": request, "lesson": lesson, "submission": sub})

@router.post("/{lesson_id}/submit")
async def mark_submitted(lesson_id: int, user=Depends(login_required), db: AsyncSession = Depends(get_db), proof_url: str | None = Form(None)):
    exists = (await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.lesson_id == lesson_id, AssignmentSubmission.user_id == user.id))).scalar_one_or_none()
    if not exists:
        db.add(AssignmentSubmission(lesson_id=lesson_id, user_id=user.id, proof_url=proof_url)); await db.commit()
    return RedirectResponse(url=f"/assignments/{lesson_id}", status_code=302)
