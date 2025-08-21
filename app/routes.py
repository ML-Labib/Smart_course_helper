from fastapi import FastAPI
from app.controllers import home, auth, admin, courses, lessons, dashboard, quizzes, assignments, discussions, calendar, tools, study_plan

def include_all_routers(app: FastAPI):
    app.include_router(home.router)      # <= add this
    app.include_router(auth.router)
    app.include_router(courses.router)
    app.include_router(lessons.router)
    app.include_router(quizzes.router)
    app.include_router(assignments.router)
    app.include_router(discussions.router)
    app.include_router(calendar.router)
    app.include_router(study_plan.router)
    app.include_router(tools.router)
    app.include_router(dashboard.router)
    app.include_router(admin.router)