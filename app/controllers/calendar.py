from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.middlewares.auth import login_required
from app.services.calendar import events_for_user, to_ics

router = APIRouter(prefix="/calendar", tags=["calendar"])
templates = Jinja2Templates(directory="app/views")

@router.get("")
async def calendar_page(request: Request, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    events = await events_for_user(db, user.id)
    return templates.TemplateResponse("calendar/index.html", {"request": request, "events": events})

@router.get("/me.ics")
async def calendar_ics(user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    events = await events_for_user(db, user.id)
    return Response(content=to_ics(events), media_type="text/calendar", headers={"Content-Disposition": "attachment; filename=deadlines.ics"})
