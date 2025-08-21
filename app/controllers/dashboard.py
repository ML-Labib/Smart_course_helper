from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.middlewares.auth import login_required
from app.models.enrollment import Enrollment
from app.models.course import Course, Lesson, LessonType, Week
from app.models.notification import Notification
from app.models.submission import AssignmentSubmission
from app.models.quiz import Quiz, QuizAttempt
from fastapi.responses import RedirectResponse
from app.models.user import Role
router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/views")

@router.get("/dashboard")
async def dashboard(request: Request, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    if user.role == Role.admin:
        return RedirectResponse(url="/admin", status_code=303)
    my_courses = (await db.execute(select(Course).join(Enrollment, Enrollment.course_id == Course.id).where(Enrollment.user_id == user.id))).scalars().all()
    notes = (await db.execute(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(10))).scalars().all()
    # assignments
    rows_a = await db.execute(
      select(Lesson, Course).join(Week, Lesson.week_id==Week.id).join(Course, Week.course_id==Course.id)
      .join(Enrollment, Enrollment.course_id==Course.id).where(Enrollment.user_id==user.id, Lesson.type==LessonType.assignment))
    upcoming_assignments=[]
    for l, c in rows_a.all():
        sub = (await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.lesson_id==l.id, AssignmentSubmission.user_id==user.id))).scalar_one_or_none()
        upcoming_assignments.append({"title": l.title, "course": c.title, "due_at": l.due_at, "submitted": sub is not None})
    # quizzes
    rows_q = await db.execute(
      select(Lesson, Course, Quiz).join(Week, Lesson.week_id==Week.id).join(Course, Week.course_id==Course.id)
      .join(Quiz, Quiz.lesson_id==Lesson.id).join(Enrollment, Enrollment.course_id==Course.id)
      .where(Enrollment.user_id==user.id, Lesson.type==LessonType.quiz))
    upcoming_quizzes=[]
    for l, c, qz in rows_q.all():
        used = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id==qz.id, QuizAttempt.user_id==user.id))).scalar() or 0
        upcoming_quizzes.append({"title": l.title, "course": c.title, "due_at": l.due_at, "attempts_left": max(0, 3 - used)})
    return templates.TemplateResponse("dashboard/index.html", {"request": request, "my_courses": my_courses, "notifications": notes, "upcoming_assignments": upcoming_assignments, "upcoming_quizzes": upcoming_quizzes})
