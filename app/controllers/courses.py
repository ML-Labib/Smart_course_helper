from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.middlewares.auth import get_current_user, login_required
from app.models.course import Course, Week
from app.models.enrollment import Enrollment
from app.services.search import search_courses

router = APIRouter(prefix="/courses", tags=["courses"])
templates = Jinja2Templates(directory="app/views")


@router.get("")
async def list_courses(
    request: Request,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None),
):
    courses = (
        await db.execute(select(Course).where(Course.published == True))
    ).scalars().all()
    courses = search_courses(courses, q)
    return templates.TemplateResponse(
        "courses/list.html",
        {"request": request, "courses": courses, "q": q},
    )


@router.get("/{course_id}")
async def course_detail(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    c = (
        await db.execute(
            select(Course)
            .options(selectinload(Course.weeks).selectinload(Week.lessons))
            .where(Course.id == course_id)
        )
    ).scalar_one()
    weeks = c.weeks  # eagerly loaded
    is_enrolled = False
    if user:
        is_enrolled = (
            await db.execute(
                select(Enrollment).where(
                    Enrollment.course_id == course_id,
                    Enrollment.user_id == user.id,
                )
            )
        ).scalar_one_or_none() is not None

    return templates.TemplateResponse(
        "courses/detail.html",
        {
            "request": request,
            "course": c,
            "weeks": weeks,
            "is_enrolled": is_enrolled,
        },
    )


@router.post("/{course_id}/enroll")
async def enroll(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(login_required),
):
    exists = (
        await db.execute(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if not exists:
        db.add(Enrollment(user_id=user.id, course_id=course_id))
        await db.commit()
    return {"ok": True}