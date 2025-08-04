from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def manage_courses(request: Request, db: Session = Depends(get_db)):
    courses = crud.get_courses(db)
    return templates.TemplateResponse("courses/manage_courses.html", {"request": request, "courses": courses, "title": "Manage Courses"})

@router.post("/", response_class=RedirectResponse)
def create_course_form(
    db: Session = Depends(get_db),
    name: str = Form(...),
    code: str = Form(...),
    instructor: str = Form(None),
    credits: float = Form(3.0)
):
    # Check if course already exists
    db_course = crud.get_course_by_code(db, course_code=code)
    if db_course:
        # You can implement better error handling here, e.g., flash messages
        raise HTTPException(status_code=400, detail="Course with this code already exists")
        
    course = schemas.CourseCreate(name=name, code=code, instructor=instructor, credits=credits)
    crud.create_course(db=db, course=course)
    
    # Redirect to the same page to see the new course
    return RedirectResponse(url="/courses/", status_code=303)