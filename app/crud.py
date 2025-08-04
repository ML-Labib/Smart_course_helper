from sqlalchemy.orm import Session
from . import models, schemas
import datetime
# === Course CRUD Functions ===

def get_course_by_code(db: Session, course_code: str):
    return db.query(models.Course).filter(models.Course.code == course_code).first()

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Course).offset(skip).limit(limit).all()

def get_upcoming_assignments(db: Session, limit: int = 5):
    now = datetime.datetime.utcnow()
    # Assuming due_date is a Date field, we compare with today's date
    today = datetime.date.today()
    return db.query(models.Assignment)\
        .filter(models.Assignment.is_completed == False)\
        .filter(models.Assignment.due_date >= today)\
        .order_by(models.Assignment.due_date)\
        .limit(limit)\
        .all()


def create_course(db: Session, course: schemas.CourseCreate):
    db_course = models.Course(
        name=course.name,
        code=course.code,
        instructor=course.instructor,
        credits=course.credits
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course