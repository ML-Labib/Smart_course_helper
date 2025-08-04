# File: app/routers/assignments.py

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import datetime

from .. import crud, schemas
from ..database import get_db

# Create a new router instance
router = APIRouter(
    prefix="/assignments",  # All routes in this file will start with /assignments
    tags=["assignments"],      # A tag for the API documentation
)

# Point to the templates directory
templates = Jinja2Templates(directory="app/templates")


@router.get("/{course_id}", response_class=HTMLResponse)
def view_assignments_for_course(request: Request, course_id: int, db: Session = Depends(get_db)):
    """
    Handles viewing the main page for a course's assignments.
    This corresponds to the "Course Details" page in your UI mockup.
    """
    course = crud.get_course(db, course_id=course_id)
    if not course:
        # If the course ID is invalid, show a 404 Not Found error
        raise HTTPException(status_code=404, detail="Course not found")

    # The template for this page is now the course detail view
    # You can pass assignments or other details to it as needed.
    return templates.TemplateResponse("assignments/course_detail.html", {
        "request": request,
        "course": course,
        "title": course.name  # Use the course name as the page title
    })


@router.post("/create/{course_id}", response_class=RedirectResponse)
def create_assignment_for_course(
    course_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    due_date: datetime.date = Form(...)
):
    """
    Handles the form submission to create a new assignment for a specific course.
    """
    # Check if the course exists before creating an assignment for it
    course = crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cannot add assignment to a non-existent course.")

    # Create a Pydantic model from the form data for validation
    assignment_data = schemas.AssignmentCreate(title=title, due_date=due_date)

    # Use the CRUD function to save the new assignment to the database
    crud.create_course_assignment(db=db, assignment=assignment_data, course_id=course_id)

    # Redirect the user back to the course detail page to see the new assignment.
    # The 303 status code is standard practice for POST-Redirect-GET pattern.
    return RedirectResponse(url=f"/assignments/{course_id}", status_code=303)


@router.post("/toggle/{assignment_id}", response_class=RedirectResponse)
def toggle_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """
    Toggles the completion status of a single assignment when its checkbox is clicked.
    """
    # Use the CRUD function to find the assignment and flip its 'is_completed' status
    assignment = crud.toggle_assignment_completion(db, assignment_id=assignment_id)
    if not assignment:
        # If the assignment ID is invalid, show a 404 error
        raise HTTPException(status_code=404, detail="Assignment not found")

    # After toggling, redirect back to the course detail page it belongs to.
    # We get the course_id from the assignment object itself.
    return RedirectResponse(url=f"/assignments/{assignment.course_id}", status_code=303)