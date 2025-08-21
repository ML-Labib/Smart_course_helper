from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.models.user import User, Role

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/views")

@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user or not bcrypt.verify(password, user.password_hash):
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid credentials"}, status_code=400)
    request.session["uid"] = user.id
    request.session["role"] = user.role.value
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request, "register": True})

@router.post("/register")
async def register(request: Request, db: AsyncSession = Depends(get_db), name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    exists = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if exists:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Email already used", "register": True}, status_code=400)
    user = User(name=name, email=email, password_hash=bcrypt.hash(password), role=Role.student)
    db.add(user); await db.commit()
    request.session["uid"] = user.id
    request.session["role"] = user.role.value
    return RedirectResponse(url="/dashboard", status_code=302)

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=302)
