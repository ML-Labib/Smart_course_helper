# File: app/models.py (REPLACE ENTIRE FILE)

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base
import datetime

# (NEW) User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    courses = relationship("Course", back_populates="owner")
    tasks = relationship("Task", back_populates="owner")

# (UPDATED) Course Model
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True)
    instructor = Column(String)
    credits = Column(Float, default=3.0)
    owner_id = Column(Integer, ForeignKey("users.id")) # New foreign key

    owner = relationship("User", back_populates="courses")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="course", cascade="all, delete-orphan") # New relationship

# (UPDATED) Assignment Model
class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="assignments")

# (NEW) Note Model
class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="notes")

# (NEW) Task Model (for general, non-course-specific tasks)
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    is_completed = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="tasks")
    
