from datetime import timedelta, timezone, datetime
from sqlalchemy import select
from app.models.enrollment import Enrollment
from app.models.course import Lesson, Week, Course
from app.models.study_plan import StudyPlan, PlanItem
import uuid

async def events_for_user(db, user_id: int):
    # Deadlines from enrolled courses
    res = await db.execute(
        select(Lesson, Week, Course)
        .join(Week, Lesson.week_id == Week.id)
        .join(Course, Week.course_id == Course.id)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user_id, Lesson.due_at.is_not(None))
    )
    events = []
    for lesson, week, course in res.all():
        events.append({
            "kind": "deadline",
            "title": f"{course.title}: {lesson.title}",
            "type": lesson.type.value,
            "due_at": lesson.due_at,
            "course": course.title,
            "week": week.number,
            "lesson_id": lesson.id
        })

    # Study plan items
    plan = (await db.execute(select(StudyPlan).where(StudyPlan.user_id == user_id))).scalar_one_or_none()
    if plan:
        items = (await db.execute(select(PlanItem).where(PlanItem.plan_id == plan.id))).scalars().all()
        for it in items:
            events.append({
                "kind": "study",
                "title": f"Study Session (Lesson {it.lesson_id})",
                "type": "study",
                "due_at": it.scheduled_at,
                "course": "",
                "week": "",
                "lesson_id": it.lesson_id
            })
    return events

def _dt_ics(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")

def to_ics(events):
    # Minimal VCALENDAR builder (CRLF endings)
    now = datetime.now(timezone.utc)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Smart Course Helper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for e in events:
        start = e["due_at"]
        end = start + timedelta(minutes=30)
        uid = f"{uuid.uuid4()}@sch.local"
        summary = f"{'Study' if e['kind']=='study' else e['type'].capitalize()} — {e['title']}"
        desc = []
        if e.get("course"):
            desc.append(f"Course: {e['course']}")
        if e.get("week"):
            desc.append(f"Week: {e['week']}")
        description = "\\n".join(desc) if desc else ""
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{_dt_ics(now)}",
            f"DTSTART:{_dt_ics(start)}",
            f"DTEND:{_dt_ics(end)}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"