from datetime import datetime, date
import enum

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Text,
    Boolean,
    DateTime,
    UniqueConstraint,
    func,
    Enum,
    Date,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class LessonType(str, enum.Enum):
    content = "content"
    assignment = "assignment"
    quiz = "quiz"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    course_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(String(300), default="")
    published: Mapped[bool] = mapped_column(Boolean, default=False)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    weeks: Mapped[list["Week"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    @property
    def cover_url(self) -> str:
        # Fallback to a local default image
        return self.picture_url or "/static/images/course-default.jpg"


class Week(Base):
    __tablename__ = "weeks"
    __table_args__ = (UniqueConstraint("course_id", "number", name="uq_week_course_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200), default="")

    course: Mapped[Course] = relationship(back_populates="weeks")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="week", cascade="all, delete-orphan", order_by="Lesson.position"
    )


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("week_id", "position", name="uq_lesson_week_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)  # 1..n within week
    type: Mapped[LessonType] = mapped_column(Enum(LessonType), default=LessonType.content)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    content_url: Mapped[str | None] = mapped_column(String(500))
    assignment_form_url: Mapped[str | None] = mapped_column(String(500))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    week: Mapped[Week] = relationship(back_populates="lessons")