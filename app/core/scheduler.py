from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.db import SessionLocal
from app.services.notifications import due_soon_scan

scheduler = AsyncIOScheduler()

async def _run_due_scan():
    async with SessionLocal() as db:
        await due_soon_scan(db)

def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(_run_due_scan, CronTrigger(hour=9, minute=0))  # daily 09:00
    scheduler.start()
