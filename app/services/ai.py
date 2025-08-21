import os
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def ask_ai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        return "AI is not configured. Add OPENAI_API_KEY to your environment."
    # Placeholder; integrate your model/provider here
    return f"Suggestion: break the problem into steps. Prompt: {prompt[:200]}"
