from backend.app.api.execution_events import router as execution_events_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.candidates import router as candidates_router
from backend.app.api.users import router as users_router
from backend.app.api.skills import router as skills_router
from backend.app.api.projects import router as projects_router
from backend.app.api.education import router as education_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.resumes import router as resumes_router
from backend.app.api.candidate_evidence import router as candidate_evidence_router
from backend.app.api.job_requirements import router as job_requirements_router
from backend.app.api.job_understanding import router as job_understanding_router
from backend.app.api.job_matching import router as job_matching_router
from backend.app.api.job_fit import router as job_fit_router
from backend.app.api.job_ranking import router as job_ranking_router
from backend.app.api.resume_tailoring import router as resume_tailoring_router
from backend.app.api.application_readiness import router as application_readiness_router
from backend.app.api.application_package import (
    router as application_package_router,
)
from backend.app.api.application_review import router as application_review_router
from backend.app.api.application_tracker import router as application_tracker_router
from backend.app.api.resume_upload import router as resume_upload_router
from backend.app.api.application_execution import router as application_execution_router
from backend.app.api.human_input import (
    router as human_input_router,
)


app = FastAPI(
    title="Agentic Job Intelligence API",
    description="AI-powered job intelligence and application platform",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates_router)
app.include_router(users_router)
app.include_router(skills_router)
app.include_router(projects_router)
app.include_router(education_router)
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(candidate_evidence_router)
app.include_router(job_requirements_router)
app.include_router(job_understanding_router)
app.include_router(job_matching_router)
app.include_router(job_fit_router)
app.include_router(job_ranking_router)
app.include_router(resume_tailoring_router)
app.include_router(application_readiness_router)
app.include_router(application_package_router)
app.include_router(application_review_router)
app.include_router(application_tracker_router)
app.include_router(resume_upload_router)
app.include_router(application_execution_router)
app.include_router(execution_events_router)
app.include_router(human_input_router)

@app.get("/")
def root():
    return {
        "message": "Agentic Job Intelligence API is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
