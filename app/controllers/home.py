from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from app.middlewares.auth import get_current_user
from app.models.user import User, Role

router = APIRouter()

@router.get("/", include_in_schema=False)
async def home(user: User | None = Depends(get_current_user)):
    if user:
        # Send to role-based dashboard
        return RedirectResponse(url="/admin" if user.role == Role.admin else "/dashboard", status_code=302)
    # Not logged in → show courses grid
    return RedirectResponse(url="/courses", status_code=302)