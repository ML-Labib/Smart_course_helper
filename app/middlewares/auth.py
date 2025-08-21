from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.models.user import User, Role

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    uid = request.session.get("uid")
    if not uid:
        return None
    res = await db.execute(select(User).where(User.id == uid))
    return res.scalar_one_or_none()

def login_required(user: User | None = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    return user

def require_admin(user: User = Depends(login_required)):
    if user.role != Role.admin:
        raise HTTPException(status_code=403)
    return user
