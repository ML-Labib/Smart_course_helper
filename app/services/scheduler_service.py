from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.study_plan import StudyPlan, PlanItem
from app.models.enrollment import Enrollment
from app.models.course import Course, Week, Lesson, LessonType

def _now():
    return datetime.now(timezone.utc)

async def generate_plan_for_user(db: AsyncSession, user_id: int, hours_per_week: int = 5):
    # fetch or create plan
    plan = (await db.execute(select(StudyPlan).where(StudyPlan.user_id == user_id))).scalar_one_or_none()
    if not plan:
        plan = StudyPlan(user_id=user_id, target_hours_per_week=hours_per_week)
        db.add(plan); await db.flush()
    else:
        plan.target_hours_per_week = hours_per_week
        # wipe old items
        await db.execute(f"DELETE FROM plan_items WHERE plan_id={plan.id}")

    # lessons from enrolled courses, prioritize by due date then week/position
    q = await db.execute(
        select(Lesson, Week, Course)
        .join(Week, Lesson.week_id == Week.id)
        .join(Course, Week.course_id == Course.id)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user_id)
    )
    lessons = [l for (l, w, c) in sorted(q.all(), key=lambda x: (x[0].due_at or _now() + timedelta(days=365), x[0].id))]
    if not lessons:
        await db.commit(); return plan

    minutes_per_week = hours_per_week * 60
    slot = _now().replace(hour=18, minute=0, second=0, microsecond=0)
    used = 0
    items = []
    for l in lessons:
        # skip assignments/quizzes to focus plan on content; still allow scheduling short review
        dur = 45 if l.type == LessonType.content else 25
        if used + dur > minutes_per_week:
            slot += timedelta(days=7); used = 0
        # pull earlier if deadline is sooner than slot
        if l.due_at and l.due_at < slot:
            slot = l.due_at - timedelta(hours=2)
        items.append(PlanItem(plan_id=plan.id, lesson_id=l.id, scheduled_at=slot, duration_minutes=dur))
        slot += timedelta(minutes=dur); used += dur

    db.add_all(items)
    await db.commit()
    return plan
