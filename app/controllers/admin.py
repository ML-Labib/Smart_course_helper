from datetime import datetime, timedelta, timezone, date

from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.middlewares.auth import require_admin
from app.models.course import Course, Week, Lesson, LessonType
from app.models.quiz import Quiz
from app.services.notifications import send_assignment_notifications, send_quiz_notifications
from app.services.files import save_upload

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/views")


@router.get("")
async def admin_index(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    courses = (await db.execute(select(Course))).scalars().all()
    return templates.TemplateResponse("admin/index.html", {"request": request, "courses": courses})


@router.get("/courses/new")
async def course_new_form(
    request: Request,
    admin=Depends(require_admin),
):
    return templates.TemplateResponse("admin/course_detail.html", {"request": request, "course": None, "weeks": []})


@router.post("/courses/new")
async def course_create(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
    title: str = Form(...),
    course_code: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    published: bool = Form(False),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
    picture: UploadFile | None = File(None),
):
    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None

    picture_url = None
    if picture and picture.filename:
        picture_url = await save_upload(picture, "covers", allowed_types=("image/jpeg", "image/png", "image/webp"))

    c = Course(
        title=title,
        course_code=course_code,
        description=description,
        tags=tags,
        published=published,
        start_date=sd,
        end_date=ed,
        picture_url=picture_url,
    )
    db.add(c)
    await db.commit()
    return RedirectResponse(url=f"/admin/courses/{c.id}", status_code=302)


@router.get("/courses/{course_id}")
async def course_detail(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    c = (
        await db.execute(
            select(Course)
            .options(selectinload(Course.weeks).selectinload(Week.lessons))
            .where(Course.id == course_id)
        )
    ).scalar_one()
    return templates.TemplateResponse("admin/course_detail.html", {"request": request, "course": c, "weeks": c.weeks})


@router.post("/courses/{course_id}/picture")
async def update_course_picture(
    course_id: int,
    picture: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    url = await save_upload(picture, "covers", allowed_types=("image/jpeg", "image/png", "image/webp"))
    c = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one()
    c.picture_url = url
    await db.commit()
    return RedirectResponse(url=f"/admin/courses/{course_id}", status_code=303)


@router.post("/courses/{course_id}/weeks/new")
async def add_week(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
    number: int = Form(...),
    title: str = Form(""),
):
    w = Week(course_id=course_id, number=number, title=title)
    db.add(w)
    await db.commit()
    return RedirectResponse(url=f"/admin/courses/{course_id}", status_code=302)


@router.post("/weeks/{week_id}/lessons/new")
async def add_lesson(
    week_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
    position: int = Form(...),
    type: str = Form("content"),
    title: str = Form(...),
    description: str = Form(""),
    content_url: str | None = Form(None),
    assignment_form_url: str | None = Form(None),
    due_at: str | None = Form(None),
    quiz_title: str | None = Form(None),
):
    # compute due date (default 1 week for assignment/quiz)
    due_dt = None
    if type in ("assignment", "quiz"):
        if due_at:
            try:
                parsed = datetime.fromisoformat(due_at)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                due_dt = parsed
            except Exception:
                due_dt = datetime.now(timezone.utc) + timedelta(days=7)
        else:
            due_dt = datetime.now(timezone.utc) + timedelta(days=7)

    lesson = Lesson(
        week_id=week_id,
        position=position,
        type=LessonType(type),
        title=title,
        description=description,
        content_url=content_url,
        assignment_form_url=assignment_form_url,
        due_at=due_dt,
    )
    db.add(lesson)
    await db.flush()

    if type == "quiz":
        db.add(Quiz(lesson_id=lesson.id, title=quiz_title or f"{title} Quiz"))

    await db.commit()

    # notifications
    if type == "assignment":
        await send_assignment_notifications(db, lesson.id)
    elif type == "quiz":
        await send_quiz_notifications(db, lesson.id)

    week = (await db.execute(select(Week).where(Week.id == week_id))).scalar_one()
    return RedirectResponse(url=f"/admin/courses/{week.course_id}", status_code=302)