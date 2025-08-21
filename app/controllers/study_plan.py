from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.middlewares.auth import login_required
from app.services.scheduler_service import generate_plan_for_user
from app.models.study_plan import StudyPlan

router = APIRouter(prefix="/study-plan", tags=["study-plan"])
templates = Jinja2Templates(directory="app/views")

@router.get("")
async def plan_index(request: Request, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    plan = (await db.execute(select(StudyPlan).where(StudyPlan.user_id == user.id))).scalar_one_or_none()
    return templates.TemplateResponse("study_plan/index.html", {"request": request, "plan": plan})

@router.post("/generate")
async def regenerate(request: Request, user=Depends(login_required), db: AsyncSession = Depends(get_db), hours_per_week: int = Form(5)):
    await generate_plan_for_user(db, user.id, hours_per_week=hours_per_week)
    return RedirectResponse(url="/study-plan", status_code=302)
