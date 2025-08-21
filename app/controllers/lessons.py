from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import urlparse, parse_qs
from app.core.db import get_db
from app.models.course import Lesson, LessonType

router = APIRouter(prefix="/lessons", tags=["lessons"])
templates = Jinja2Templates(directory="app/views")

def yt_embed(url: str) -> str | None:
    if not url: return None
    if "youtube.com" in url:
        q = parse_qs(urlparse(url).query)
        vid = (q.get("v") or [None])[0]
        return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else None
    if "youtu.be" in url:
        vid = url.rstrip("/").split("/")[-1]
        return f"https://www.youtube-nocookie.com/embed/{vid}"
    return None

@router.get("/{lesson_id}")
async def lesson_detail(request: Request, lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson or lesson.type != LessonType.content:
        raise HTTPException(status_code=404)
    embed = yt_embed(lesson.content_url or "")
    is_pdf = (lesson.content_url or "").lower().endswith(".pdf")
    return templates.TemplateResponse("lessons/detail.html", {"request": request, "lesson": lesson, "embed_url": embed, "is_pdf": is_pdf})
