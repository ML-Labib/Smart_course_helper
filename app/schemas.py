# File: app/schemas.py (REPLACE ENTIRE FILE)

from pydantic import BaseModel
from typing import Optional, List
import datetime

# --- Base and Create Schemas first ---

class NoteBase(BaseModel):
    title: str
    content: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class TaskBase(BaseModel):
    title: str

class TaskCreate(TaskBase):
    pass

class AssignmentBase(BaseModel):
    title: str
    due_date: datetime.date

class AssignmentCreate(AssignmentBase):
    pass

class CourseBase(BaseModel):
    name: str
    code: str
    instructor: Optional[str] = None
    credits: Optional[float] = 3.0

class CourseCreate(CourseBase):
    pass

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

# --- Schemas with IDs for reading from DB (includes relationships) ---

class Note(NoteBase):
    id: int
    created_at: datetime.datetime
    course_id: int
    class Config:
        # V2 Update: 'orm_mode' is now 'from_attributes'
        from_attributes = True

class Task(TaskBase):
    id: int
    is_completed: bool
    owner_id: int
    class Config:
        # V2 Update: 'orm_mode' is now 'from_attributes'
        from_attributes = True

class Assignment(AssignmentBase):
    id: int
    is_completed: bool
    course_id: int
    class Config:
        # V2 Update: 'orm_mode' is now 'from_attributes'
        from_attributes = True

class Course(CourseBase):
    id: int
    owner_id: Optional[int] = None
    assignments: List[Assignment] = []
    notes: List[Note] = []
    class Config:
        # V2 Update: 'orm_mode' is now 'from_attributes'
        from_attributes = True

class User(UserBase):
    id: int
    courses: List[Course] = []
    tasks: List[Task] = []
    class Config:
        # V2 Update: 'orm_mode' is now 'from_attributes'
        from_attributes = True