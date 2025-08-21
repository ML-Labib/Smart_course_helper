from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from app.core.config import settings
from app.core.db import init_models
from app.core.scheduler import start_scheduler
from app.routes import include_all_routers
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

app = FastAPI(title="Smart Course Helper")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
include_all_routers(app)

@app.on_event("startup")
async def on_startup():
    await init_models()
    start_scheduler()
    
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code in (401, 403):
        next_url = request.url.path
        return RedirectResponse(url=f"/auth/login?next={next_url}", status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
