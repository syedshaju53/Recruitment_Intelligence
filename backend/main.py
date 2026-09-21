from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    student_router,
    job_router,
    saved_job_router,
    application_router,
    notification_router,
    live_job_router,
    admin_router,
    resume_router,
)
import os

app = FastAPI(
    title="Recruitment Intelligence API",
    description="AI-Powered Recruitment Intelligence and Job Recommendation API",
    version="1.0.0",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

allowed_origins = [
    FRONTEND_URL,
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

# --------------------------------------------------
# CORS
# --------------------------------------------------

origins = allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(
    student_router.router,
    prefix="/students",
    tags=["Students"],
)

app.include_router(
    job_router.router,
    prefix="/jobs",
    tags=["Jobs"],
)

app.include_router(
    saved_job_router.router,
    prefix="/saved-jobs",
    tags=["Saved Jobs"],
)

app.include_router(
    application_router.router,
    prefix="/applications",
    tags=["Applications"],
)

app.include_router(notification_router.router, prefix="/notifications")

app.include_router(
    resume_router.router,
)

app.include_router(
    live_job_router.router,
    prefix="/live-jobs",
    tags=["Live Jobs"],
)

app.include_router(
    admin_router.router,
    prefix="/admin",
    tags=["Admin"],
)


@app.get("/")
def root():
    return {
        "message": "Recruitment Intelligence API is running",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }