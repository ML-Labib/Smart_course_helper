from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.middlewares.auth import login_required
from app.models.discussion import Thread, Post
from app.models.enrollment import Enrollment

router = APIRouter(prefix="/discussions", tags=["discussions"])
templates = Jinja2Templates(directory="app/views")

@router.get("/course/{course_id}")
async def threads_list(request: Request, course_id: int, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    # only enrolled can view/post
    enrolled = (await db.execute(select(Enrollment).where(Enrollment.course_id==course_id, Enrollment.user_id==user.id))).scalar_one_or_none()
    if not enrolled:
        return RedirectResponse(url="/courses", status_code=302)
    threads = (await db.execute(select(Thread).where(Thread.course_id == course_id))).scalars().all()
    return templates.TemplateResponse("discussions/list.html", {"request": request, "course_id": course_id, "threads": threads})

@router.post("/course/{course_id}/new")
async def new_thread(course_id: int, title: str = Form(...), body: str = Form(...), user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    enrolled = (await db.execute(select(Enrollment).where(Enrollment.course_id==course_id, Enrollment.user_id==user.id))).scalar_one_or_none()
    if not enrolled:
        return RedirectResponse(url="/courses", status_code=302)
    t = Thread(course_id=course_id, title=title, created_by=user.id)
    db.add(t); await db.flush()
    db.add(Post(thread_id=t.id, user_id=user.id, body=body)); await db.commit()
    return RedirectResponse(url=f"/discussions/thread/{t.id}", status_code=302)

@router.get("/thread/{thread_id}")
async def thread_view(request: Request, thread_id: int, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(Thread).where(Thread.id == thread_id))).scalar_one()
    posts = (await db.execute(select(Post).where(Post.thread_id == thread_id))).scalars().all()
    return templates.TemplateResponse("discussions/thread.html", {"request": request, "thread": t, "posts": posts})

@router.post("/thread/{thread_id}/reply")
async def reply(thread_id: int, body: str = Form(...), user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    db.add(Post(thread_id=thread_id, user_id=user.id, body=body)); await db.commit()
    return RedirectResponse(url=f"/discussions/thread/{thread_id}", status_code=302)
