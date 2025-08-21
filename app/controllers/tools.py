from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app.services.ai import ask_ai

router = APIRouter(prefix="/tools", tags=["tools"])
templates = Jinja2Templates(directory="app/views")

@router.get("/gpa")
def gpa_page(request: Request):
    return templates.TemplateResponse("tools/gpa.html", {"request": request})

@router.get("/ai")
def ai_page(request: Request):
    return templates.TemplateResponse("tools/ai.html", {"request": request, "answer": None})

@router.post("/ai")
async def ai_query(request: Request, prompt: str = Form(...)):
    answer = await ask_ai(prompt)
    return templates.TemplateResponse("tools/ai.html", {"request": request, "answer": answer})
