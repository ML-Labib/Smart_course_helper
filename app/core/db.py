from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, select
from app.core.config import settings

# Async engine and session factory
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

# Enable foreign keys for SQLite
@event.listens_for(engine.sync_engine, "connect")
def _fk_pragma(dbapi_conn, conn_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Dependency for FastAPI controllers
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# Create tables and seed default admin
async def init_models():
    # Import models to register metadata
    from app.models import user, course, enrollment, quiz, submission, notification, discussion, study_plan  # noqa

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default admin
    from app.models.user import User, Role
    from passlib.hash import bcrypt
    async with SessionLocal() as db:
        exists = (await db.execute(select(User).where(User.email == "admin@local"))).scalar_one_or_none()
        if not exists:
            admin = User(name="admin", email="admin@local", password_hash=bcrypt.hash("admin"), role=Role.admin)
            db.add(admin)
            await db.commit()