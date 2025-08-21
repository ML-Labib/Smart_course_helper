from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String, JSON, DateTime, UniqueConstraint, func
from app.core.db import Base
from sqlalchemy import ForeignKey, Integer, String, JSON, DateTime, UniqueConstraint, func
from datetime import datetime
class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    order: Mapped[int]
    question: Mapped[str] = mapped_column(String(500))
    options: Mapped[list[str]] = mapped_column(JSON)     # 4 options
    correct_index: Mapped[int] = mapped_column(Integer)   # 0..3
    quiz: Mapped["Quiz"] = relationship(back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (UniqueConstraint("quiz_id", "user_id", "attempt_no", name="uq_quiz_attempt_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    attempt_no: Mapped[int] = mapped_column(Integer)  # 1..3
    score: Mapped[int] = mapped_column(Integer)       # 0..10
    answers: Mapped[list[int]] = mapped_column(JSON)  # 10 ints (0..3)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
