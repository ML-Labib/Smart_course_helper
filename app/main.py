# File: app/main.py

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# Important: Make sure all necessary modules are imported
from .database import engine, Base, get_db
from .routers import courses, assignments, gpa_calculator # Ensure all router modules are imported
from . import crud

# Create database tables (if they don't exist)
Base.metadata.create_all(bind=engine)

# Create the main FastAPI app instance
app = FastAPI(title="Smart Course Helper")

# Mount static files (for CSS, etc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# -----------------------------------------------------------------
# --- THIS IS THE MOST LIKELY PLACE FOR THE ERROR ---
# You MUST include your routers for their paths to be registered.
# -----------------------------------------------------------------
app.include_router(courses.router)
app.include_router(assignments.router)
app.include_router(gpa_calculator.router)
# -----------------------------------------------------------------


# This root route should now be defined in main.py, not a separate router
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    """
    Handles the dashboard/root page.
    """
    # Fetching upcoming deadlines for the dashboard
    upcoming_deadlines = crud.get_upcoming_assignments(db=db, limit=3)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "upcoming_deadlines": upcoming_deadlines
    })

# You'll also need a Jinja2Templates instance here for the root route to work.
templates = Jinja2Templates(directory="app/templates")