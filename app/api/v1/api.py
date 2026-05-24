from fastapi import APIRouter
from app.api.v1.endpoints import auth, jobs, applications, interviews, proctoring , interview_engine, candidate_profiles, recruiter_profiles # Add new imports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(candidate_profiles.router, prefix="/candidate-profiles", tags=["Candidate Profiles"]) # New
api_router.include_router(recruiter_profiles.router, prefix="/recruiter-profiles", tags=["Recruiter Profiles"]) # New
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(proctoring.router, prefix="/proctoring", tags=["Proctoring"])
api_router.include_router(interview_engine.router, tags=["Interview WebSocket"])