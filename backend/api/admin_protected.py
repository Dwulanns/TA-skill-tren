"""
Protected Admin Endpoints - Requires Authentication
====================================================

Protected endpoints for admin data management operations.
All endpoints require valid JWT token from /api/auth/login
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_context
from database.models import Job, Skill, Admin
from dependencies_admin import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin-protected"])


# Pydantic Models
class JobUpdate(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    ids: list[int]


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete a specific job by ID (Protected)"""
    try:
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            db.delete(job)
            db.commit()
            
            return {
                "success": True,
                "message": f"Job with ID {job_id} deleted successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_admin: Admin = Depends(get_current_admin)
):
    """Update a specific job by ID (Protected)"""
    try:
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Update only provided fields
            if job_data.job_title is not None:
                job.job_title = job_data.job_title
            if job_data.company is not None:
                job.company = job_data.company
            if job_data.location is not None:
                job.location = job_data.location
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Job with ID {job_id} updated successfully",
                "job": {
                    "id": job.id,
                    "job_title": job.job_title,
                    "company": job.company,
                    "location": job.location
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/skills/{skill_id}")
async def delete_skill(
    skill_id: int,
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete a specific skill by ID (Protected)"""
    try:
        with get_db_context() as db:
            skill = db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                raise HTTPException(status_code=404, detail="Skill not found")
            
            db.delete(skill)
            db.commit()
            
            return {
                "success": True,
                "message": f"Skill with ID {skill_id} deleted successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs")
async def delete_all_jobs(
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete all jobs from database (Protected) - Requires confirmation"""
    try:
        with get_db_context() as db:
            count = db.query(Job).count()
            db.query(Job).delete()
            db.commit()
            
            return {
                "success": True,
                "message": f"All {count} jobs deleted successfully"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/skills")
async def delete_all_skills(
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete all skills from database (Protected) - Requires confirmation"""
    try:
        with get_db_context() as db:
            count = db.query(Skill).count()
            db.query(Skill).delete()
            db.commit()
            
            return {
                "success": True,
                "message": f"All {count} skills deleted successfully"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/info")
async def get_admin_info(
    current_admin: Admin = Depends(get_current_admin)
):
    """Get current admin information (Protected)"""
    return {
        "id": current_admin.id,
        "email": current_admin.email,
        "username": current_admin.username,
        "is_active": current_admin.is_active,
        "created_at": current_admin.created_at,
        "last_login": current_admin.last_login
    }
