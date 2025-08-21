from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.middlewares.auth import login_required, require_admin
from app.models.course import Lesson, LessonType, Week
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt

router = APIRouter(prefix="/quizzes", tags=["quizzes"])
templates = Jinja2Templates(directory="app/views")

@router.get("/{lesson_id}")
async def attempt_form(request: Request, lesson_id: int, user=Depends(login_required), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one()
    if lesson.type != LessonType.quiz:
        raise HTTPException(404)
    quiz = (await db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id))).scalar_one()
    questions = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.order))).scalars().all()
    used = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id))).scalar() or 0
    attempts_left = max(0, 3 - used)
    return templates.TemplateResponse("quizzes/attempt.html", {"request": request, "lesson": lesson, "quiz": quiz, "questions": questions, "attempts_left": attempts_left})

@router.post("/{lesson_id}/submit")
async def submit_quiz(lesson_id: int, request: Request, user=Depends(login_required), db: AsyncSession = Depends(get_db), answers: list[int] = Form(...)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one()
    if lesson.type != LessonType.quiz:
        raise HTTPException(404)
    quiz = (await db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id))).scalar_one()
    used = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id))).scalar() or 0
    if used >= 3:
        return templates.TemplateResponse("quizzes/result.html", {"request": request, "error": "No attempts left"})
    qs = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.order))).scalars().all()
    if len(qs) != 10 or len(answers) != 10:
        return templates.TemplateResponse("quizzes/result.html", {"request": request, "error": "Quiz is not properly configured (needs 10 questions)."})
    score = sum(1 for i, q in enumerate(qs) if int(answers[i]) == q.correct_index)
    attempt = QuizAttempt(quiz_id=quiz.id, user_id=user.id, attempt_no=used+1, score=score, answers=[int(a) for a in answers])
    db.add(attempt); await db.commit()
    return templates.TemplateResponse("quizzes/result.html", {"request": request, "score": score, "total": 10, "attempt_no": used+1})

# Admin quiz builder (exactly 10 questions)
@router.get("/builder/{lesson_id}")
async def quiz_builder(request: Request, lesson_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one()
    if lesson.type != LessonType.quiz:
        raise HTTPException(404)
    quiz = (await db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id))).scalar_one()
    qs = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.order))).scalars().all()
    return templates.TemplateResponse("admin/quiz_builder.html", {"request": request, "lesson": lesson, "quiz": quiz, "questions": qs})

@router.post("/builder/{lesson_id}")
async def save_quiz(lesson_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require_admin),
                    q_text: list[str] = Form(...),
                    a1: list[str] = Form(...), a2: list[str] = Form(...), a3: list[str] = Form(...), a4: list[str] = Form(...),
                    correct: list[int] = Form(...)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one()
    if lesson.type != LessonType.quiz:
        raise HTTPException(404)
    quiz = (await db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id))).scalar_one()
    # enforce exactly 10
    if not (len(q_text) == len(a1) == len(a2) == len(a3) == len(a4) == len(correct) == 10):
        raise HTTPException(status_code=400, detail="Exactly 10 questions are required.")
    # Replace all existing questions
    await db.execute(f"DELETE FROM quiz_questions WHERE quiz_id={quiz.id}")
    for i in range(10):
        db.add(QuizQuestion(quiz_id=quiz.id, order=i+1, question=q_text[i], options=[a1[i], a2[i], a3[i], a4[i]], correct_index=int(correct[i])))
    await db.commit()
    return {"ok": True}
