from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from typing import List, Optional

from database.connection import get_db
from database.models import Job, Keyword, JobAnalysis
from .schemas import JobInfo, JobAnalysisData

router = APIRouter(tags=["jobs"])

@router.get("/api/jobs", response_model=List[JobInfo])
async def get_jobs(
    limit: int = Query(50, ge=1, le=500),
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List job dengan filter"""
    query = db.query(Job, Keyword.keyword).join(
        Keyword, Keyword.id == Job.keyword_id
    )
    
    # Apply filters
    filters = []
    
    if keyword:
        filters.append(Keyword.keyword == keyword)
    
    if city:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id)
        filters.append(JobAnalysis.location == city)
    
    if month:
        filters.append(extract('month', Job.posted_date) == month)
    
    if year:
        filters.append(extract('year', Job.posted_date) == year)
    
    if filters:
        query = query.filter(and_(*filters))
    
    results = query.order_by(Job.posted_date.desc()).limit(limit).all()
    
    return [
        JobInfo(
            id=job.id,
            job_title=job.job_title,
            company=job.company,
            location=job.location or "Indonesia",
            keyword=keyword_text,
            posted_date=job.posted_date.isoformat() if job.posted_date else "",
            created_at=job.created_at.isoformat() if job.created_at else "",
            source=job.source
        )
        for job, keyword_text in results
    ]


@router.get("/api/job-analysis", response_model=List[JobAnalysisData])
async def get_job_analysis(
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    city: Optional[str] = Query(None, description="Filter by city"),
    employee_size: Optional[str] = Query(None, description="Filter by employee size"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get job analysis data (AI extraction results)
    Includes job info + extracted skills in denormalized format
    """
    query = db.query(JobAnalysis)
    
    # Apply filters
    filters = []
    
    if keyword:
        filters.append(JobAnalysis.keyword == keyword)
    
    if city:
        filters.append(JobAnalysis.location == city)

    if employee_size:
        query = query.join(Job, Job.id == JobAnalysis.job_id)
        filters.append(Job.employee_size == employee_size)
    
    if month:
        filters.append(extract('month', JobAnalysis.posted_date) == month)
    
    if year:
        filters.append(extract('year', JobAnalysis.posted_date) == year)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Order by most recent
    query = query.order_by(JobAnalysis.extracted_at.desc())
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    results = query.all()
    
    return [
        JobAnalysisData(
            id=r.id,
            job_title=r.job_title,
            company=r.company,
            location=r.location,
            posted_date=r.posted_date.isoformat() if r.posted_date else None,
            link=r.link,
            keyword=r.keyword,
            tech_stack=r.tech_stack,
            soft_skill=r.soft_skill,
            extracted_at=r.extracted_at.isoformat() if r.extracted_at else None,
            ai_model=r.ai_model
        )
        for r in results
    ]


@router.get("/api/job-analysis/locations")
async def get_job_analysis_locations(db: Session = Depends(get_db)):
    """
    Get unique locations from job_analysis table for filter dropdown
    """
    try:
        locations = db.query(
            JobAnalysis.location,
            func.count(JobAnalysis.id).label('count')
        ).filter(
            JobAnalysis.location.isnot(None),
            JobAnalysis.location != '',
            JobAnalysis.location != 'other',
            JobAnalysis.location != 'Remote'
        ).group_by(
            JobAnalysis.location
        ).order_by(
            func.count(JobAnalysis.id).desc()
        ).all()
        
        return [
            {"city": loc[0], "count": loc[1]}
            for loc in locations
        ]
    except Exception as e:
        print(f"❌ Error in /api/job-analysis/locations: {str(e)}")
        return []


@router.get("/api/job-analysis/{job_id}", response_model=JobAnalysisData)
async def get_job_analysis_by_id(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get job analysis by job ID
    """
    result = db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job analysis not found")
    
    return JobAnalysisData(
        id=result.id,
        job_title=result.job_title,
        company=result.company,
        location=result.location,
        posted_date=result.posted_date.isoformat() if result.posted_date else None,
        link=result.link,
        keyword=result.keyword,
        tech_stack=result.tech_stack,
        soft_skill=result.soft_skill,
        extracted_at=result.extracted_at.isoformat() if result.extracted_at else None,
        ai_model=result.ai_model
    )
