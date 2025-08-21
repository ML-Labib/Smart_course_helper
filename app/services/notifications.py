from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.notification import Notification
from app.models.course import Lesson, LessonType, Week, Course
from app.models.enrollment import Enrollment
from app.models.submission import AssignmentSubmission
from app.models.quiz import Quiz, QuizAttempt

async def send_assignment_notifications(db: AsyncSession, lesson_id: int):
    row = (await db.execute(
        select(Lesson, Week, Course)
        .join(Week, Lesson.week_id == Week.id)
        .join(Course, Week.course_id == Course.id)
        .where(Lesson.id == lesson_id)
    )).first()
    if not row: return
    l, w, c = row
    uids = [uid for (uid,) in (await db.execute(select(Enrollment.user_id).where(Enrollment.course_id == c.id))).all()]
    notes = [Notification(user_id=uid, type="assignment", title=f"New assignment: {c.title} — {l.title}",
                          body=f"Week {w.number}. Due {l.due_at}.", link_url=f"/assignments/{l.id}") for uid in uids]
    db.add_all(notes); await db.commit()

async def send_quiz_notifications(db: AsyncSession, lesson_id: int):
    row = (await db.execute(
        select(Lesson, Week, Course)
        .join(Week, Lesson.week_id == Week.id)
        .join(Course, Week.course_id == Course.id)
        .where(Lesson.id == lesson_id)
    )).first()
    if not row: return
    l, w, c = row
    uids = [uid for (uid,) in (await db.execute(select(Enrollment.user_id).where(Enrollment.course_id == c.id))).all()]
    notes = [Notification(user_id=uid, type="quiz", title=f"New quiz: {c.title} — {l.title}",
                          body=f"Week {w.number}. Due {l.due_at}.", link_url=f"/quizzes/{l.id}") for uid in uids]
    db.add_all(notes); await db.commit()

async def due_soon_scan(db: AsyncSession):
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=1)
    # assignments due soon not submitted
    rows = await db.execute(
        select(Enrollment.user_id, Lesson.id, Lesson.title, Course.title, Lesson.due_at)
        .join(Course, Enrollment.course_id == Course.id)
        .join(Week, Week.course_id == Course.id)
        .join(Lesson, Lesson.week_id == Week.id)
        .where(Lesson.type == LessonType.assignment, Lesson.due_at.between(now, soon))
    )
    for user_id, lid, ltitle, ctitle, due_at in rows.all():
        sub = (await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.lesson_id == lid, AssignmentSubmission.user_id == user_id))).scalar_one_or_none()
        if not sub:
            await _notify_once(db, user_id, f"Assignment due tomorrow: {ctitle} — {ltitle}", f"Due {due_at}", f"/assignments/{lid}")

    # quizzes due soon with zero attempts
    rows2 = await db.execute(
        select(Enrollment.user_id, Lesson.id, Lesson.title, Course.title, Lesson.due_at)
        .join(Course, Enrollment.course_id == Course.id)
        .join(Week, Week.course_id == Course.id)
        .join(Lesson, Lesson.week_id == Week.id)
        .where(Lesson.type == LessonType.quiz, Lesson.due_at.between(now, soon))
    )
    for user_id, lid, ltitle, ctitle, due_at in rows2.all():
        quiz = (await db.execute(select(Quiz).where(Quiz.lesson_id == lid))).scalar_one_or_none()
        if not quiz: continue
        used = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user_id))).scalar() or 0
        if used == 0:
            await _notify_once(db, user_id, f"Quiz due tomorrow: {ctitle} — {ltitle}", f"Due {due_at}", f"/quizzes/{lid}")

async def _notify_once(db: AsyncSession, user_id: int, title: str, body: str, link: str | None):
    dup = (await db.execute(select(Notification).where(Notification.user_id == user_id, Notification.title == title))).scalar_one_or_none()
    if not dup:
        db.add(Notification(user_id=user_id, type="reminder", title=title, body=body, link_url=link))
        await db.commit()
