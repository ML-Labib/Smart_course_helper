# File: app/routers/gpa_calculator.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Create a new router instance
router = APIRouter(
    prefix="/gpa-calculator",  # All routes in this file will start with /gpa-calculator
    tags=["gpa-calculator"],      # A tag for the API documentation (e.g., at /docs)
)

# Point to the templates directory
templates = Jinja2Templates(directory="app/templates")


# Define the route for the main GPA calculator page
@router.get("/", response_class=HTMLResponse)
def gpa_calculator_page(request: Request):
    """
    This endpoint serves the main GPA Calculator page.
    It renders the gpa_calculator/index.html template.
    """
    return templates.TemplateResponse("gpa_calculator/index.html", {
        "request": request,
        "title": "GPA Calculator"  # This title is used in base.html
    })