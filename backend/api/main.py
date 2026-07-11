"""
FastAPI Backend untuk Skill Trend Visualization
API dengan filter: bulan, tahun, kota, keyword

DATA SOURCE DOCUMENTATION:
==========================
✅ SEMUA ENDPOINT MENGEMBALIKAN DATA DARI DATABASE
✅ Tidak ada hardcoded atau fallback data
✅ Setiap endpoint melakukan database query secara langsung
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db
from constants import (
    ALLOWED_CORS_ORIGINS,
    CORS_CONFIG,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION
)

# Import routers
try:
    from api.admin import router as admin_router
    from api.admin_protected import router as admin_protected_router
    from api.auth import router as auth_router
    from api.stats import router as stats_router
    from api.jobs import router as jobs_router
    from api.skills import router as skills_router
    from api.dashboard import router as dashboard_router
except ImportError:
    from .admin import router as admin_router
    from .admin_protected import router as admin_protected_router
    from .auth import router as auth_router
    from .stats import router as stats_router
    from .jobs import router as jobs_router
    from .skills import router as skills_router
    from .dashboard import router as dashboard_router

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Ensure there is at least a sensible default for local development
if not ALLOWED_CORS_ORIGINS:
    ALLOWED_CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

# Make preflight methods explicit to avoid issues with some browsers
cors_methods = CORS_CONFIG.get("allow_methods", ["*"])
if cors_methods == ["*"]:
    cors_methods = ["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH", "HEAD"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=CORS_CONFIG.get("allow_credentials", True),
    allow_methods=cors_methods,
    allow_headers=CORS_CONFIG.get("allow_headers", ["*"]),
)

# Include all sub-routers
app.include_router(admin_router)
app.include_router(admin_protected_router)
app.include_router(auth_router)
app.include_router(stats_router)
app.include_router(jobs_router)
app.include_router(skills_router)
app.include_router(dashboard_router)


@app.on_event("startup")
async def startup_event():
    """Create all database tables on application start."""
    init_db()


@app.get("/")
async def root():
    return {
        "message": "Job Skills Trend API v2.0",
        "version": "2.0.0",
        "endpoints": {
            "statistics": "/api/stats",
            "filter_options": "/api/filters",
            "top_skills": "/api/skills/top",
            "skill_trends": "/api/trends",
            "jobs": "/api/jobs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)