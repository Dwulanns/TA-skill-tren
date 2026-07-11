from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from typing import List, Optional
import json

from database.connection import get_db, get_db_context
from database.models import Job, Skill, SkillType, JobSkill, Keyword, JobAnalysis
from .schemas import TopCompaniesResponse, CompanyInfo

router = APIRouter(tags=["dashboard"])

@router.get("/api/dashboard/skills-distribution")
def get_skills_distribution(
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Distribusi skills berdasarkan type (tech_stack, tools, soft_skill)
    dengan top 5 skills untuk masing-masing kategori
    """
    # Base query untuk job filtering
    job_query = db.query(Job.id)
    
    if keyword_id:
        job_query = job_query.filter(Job.keyword_id == keyword_id)
    if location:
        job_query = job_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        job_query = job_query.filter(Job.company == company)
    if employee_size:
        job_query = job_query.filter(Job.employee_size == employee_size)
    if month:
        job_query = job_query.filter(extract('month', Job.posted_date) == month)
    if year:
        job_query = job_query.filter(extract('year', Job.posted_date) == year)
    
    job_ids = [j[0] for j in job_query.all()]
    
    if not job_ids:
        return []
    
    # Query skills grouped by type
    results = []
    total_skills = 0
    
    for skill_type_name in ['tech_stack', 'soft_skill']:
        # Get skill type
        skill_type = db.query(SkillType).filter(SkillType.name == skill_type_name).first()
        if not skill_type:
            continue
        
        # Count total skills for this type
        type_count = db.query(func.count(JobSkill.id)).join(
            Skill, Skill.id == JobSkill.skill_id
        ).filter(
            Skill.skill_type_id == skill_type.id,
            JobSkill.job_id.in_(job_ids)
        ).scalar() or 0
        
        total_skills += type_count
        
        # Get top 5 skills for this type
        top_skills = db.query(
            Skill.name,
            func.count(JobSkill.id).label('count')
        ).join(
            JobSkill, JobSkill.skill_id == Skill.id
        ).filter(
            Skill.skill_type_id == skill_type.id,
            JobSkill.job_id.in_(job_ids)
        ).group_by(
            Skill.name
        ).order_by(
            func.count(JobSkill.id).desc()
        ).limit(5).all()
        
        results.append({
            'skill_type': skill_type_name,
            'count': type_count,
            'percentage': 0,  # Will calculate below
            'top_skills': [{'name': s[0], 'count': s[1]} for s in top_skills]
        })
    
    # Calculate percentages
    for r in results:
        if total_skills > 0:
            r['percentage'] = round((r['count'] / total_skills) * 100, 1)
    
    return results


@router.get("/api/dashboard/skills-trend-timeline")
def get_skills_trend_timeline(
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    limit_months: int = 12,
    db: Session = Depends(get_db)
):
    """
    Timeline trend skills per bulan (untuk line chart)
    Menampilkan jumlah skill berdasarkan type per bulan
    """
    # Base query
    query = db.query(
        extract('year', Job.posted_date).label('year'),
        extract('month', Job.posted_date).label('month'),
        SkillType.name.label('skill_type'),
        func.count(JobSkill.id).label('count')
    ).join(
        JobSkill, JobSkill.job_id == Job.id
    ).join(
        Skill, Skill.id == JobSkill.skill_id
    ).join(
        SkillType, SkillType.id == Skill.skill_type_id
    )
    
    # Apply filters
    if keyword_id:
        query = query.filter(Job.keyword_id == keyword_id)
    if location:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        query = query.filter(Job.company == company)
    if employee_size:
        query = query.filter(Job.employee_size == employee_size)
    
    # Group and order
    results = query.group_by(
        extract('year', Job.posted_date),
        extract('month', Job.posted_date),
        SkillType.name
    ).order_by(
        extract('year', Job.posted_date).desc(),
        extract('month', Job.posted_date).desc()
    ).limit(limit_months * 3).all()  # 3 types per month
    
    # Format results
    timeline = {}
    for year, month, skill_type, count in results:
        if year and month:
            month_key = f"{int(year)}-{int(month):02d}"
            if month_key not in timeline:
                timeline[month_key] = {
                    'month': month_key,
                    'tech_stack': 0,
                    'soft_skill': 0,
                    'total': 0
                }
            timeline[month_key][skill_type] = count
            timeline[month_key]['total'] += count
    
    return sorted(timeline.values(), key=lambda x: x['month'])


@router.get("/api/dashboard/top-skills-ranked")
def get_top_skills_ranked(
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Top N skills dengan ranking (untuk bar chart)
    """
    # Base query
    query = db.query(
        Skill.name.label('skill_name'),
        SkillType.name.label('skill_type'),
        func.count(JobSkill.id).label('count')
    ).join(
        JobSkill, JobSkill.skill_id == Skill.id
    ).join(
        SkillType, SkillType.id == Skill.skill_type_id
    ).join(
        Job, Job.id == JobSkill.job_id
    )
    
    # Apply filters
    if keyword_id:
        query = query.filter(Job.keyword_id == keyword_id)
    if location:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        query = query.filter(Job.company == company)
    if employee_size:
        query = query.filter(Job.employee_size == employee_size)
    if month:
        query = query.filter(extract('month', Job.posted_date) == month)
    if year:
        query = query.filter(extract('year', Job.posted_date) == year)
    
    # Group and order
    results = query.group_by(
        Skill.name, SkillType.name
    ).order_by(
        func.count(JobSkill.id).desc()
    ).limit(limit).all()
    
    # Calculate percentages
    total = sum(r[2] for r in results) if results else 0
    
    return [
        {
            'rank': idx + 1,
            'skill_name': r[0],
            'skill_type': r[1],
            'count': r[2],
            'percentage': round((r[2] / total) * 100, 1) if total > 0 else 0
        }
        for idx, r in enumerate(results)
    ]


@router.get("/api/dashboard/jobs-by-location")
def get_jobs_by_location(
    keyword_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Distribusi lowongan berdasarkan lokasi
    """
    query = db.query(
        Job.location,
        func.count(Job.id).label('count')
    )
    
    if keyword_id:
        query = query.filter(Job.keyword_id == keyword_id)
    if month:
        query = query.filter(extract('month', Job.posted_date) == month)
    if year:
        query = query.filter(extract('year', Job.posted_date) == year)
    
    results = query.group_by(Job.location).order_by(
        func.count(Job.id).desc()
    ).limit(limit).all()
    
    total = sum(r[1] for r in results)
    
    return [
        {
            'location': r[0],
            'count': r[1],
            'percentage': round((r[1] / total) * 100, 1) if total > 0 else 0
        }
        for r in results
    ]


@router.get("/api/dashboard/top-tech-stack")
async def get_top_tech_stack(
    keyword_ids: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    years: Optional[str] = Query(None),
    limit: int = Query(10)
):
    """Get Top 10 Tech Stack with multi-select filters"""
    with get_db_context() as db:
        # Base query - join SkillType to filter by name
        query = db.query(
            Skill.name,
            func.count(JobSkill.id).label('count')
        ).join(JobSkill).join(Job).join(SkillType, Skill.skill_type_id == SkillType.id)\
        .filter(SkillType.name == 'tech_stack')
        
        # Apply filters
        if keyword_ids:
            ids = [int(x.strip()) for x in keyword_ids.split(',') if x.strip()]
            if ids:
                query = query.filter(Job.keyword_id.in_(ids))
        
        if locations:
            locs = [x.strip() for x in locations.split(',') if x.strip()]
            if locs:
                query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location.in_(locs))
        
        if months:
            mnths = [int(x.strip()) for x in months.split(',') if x.strip()]
            if mnths:
                query = query.filter(extract('month', Job.posted_date).in_(mnths))
        
        if years:
            yrs = [int(x.strip()) for x in years.split(',') if x.strip()]
            if yrs:
                query = query.filter(extract('year', Job.posted_date).in_(yrs))
        
        # Get results
        results = query.group_by(Skill.name).order_by(func.count(JobSkill.job_id.distinct()).desc()).limit(limit).all()
        
        # Calculate total
        total_query = db.query(func.count(Job.id.distinct()))
        if keyword_ids:
            ids = [int(x.strip()) for x in keyword_ids.split(',') if x.strip()]
            if ids:
                total_query = total_query.filter(Job.keyword_id.in_(ids))
        if locations:
            locs = [x.strip() for x in locations.split(',') if x.strip()]
            if locs:
                total_query = total_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location.in_(locs))
        if months:
            mnths = [int(x.strip()) for x in months.split(',') if x.strip()]
            if mnths:
                total_query = total_query.filter(extract('month', Job.posted_date).in_(mnths))
        if years:
            yrs = [int(x.strip()) for x in years.split(',') if x.strip()]
            if yrs:
                total_query = total_query.filter(extract('year', Job.posted_date).in_(yrs))
        
        total_jobs = total_query.scalar() or 0
        
        return [
            {
                'rank': idx + 1,
                'skill_name': r[0],
                'count': r[1],
                'percentage': round((r[1] / total_jobs) * 100, 1) if total_jobs > 0 else 0,
                'total_jobs': total_jobs
            }
            for idx, r in enumerate(results)
        ]


@router.get("/api/dashboard/top-tools")
async def get_top_tools(
    keyword_ids: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    years: Optional[str] = Query(None),
    limit: int = Query(10)
):
    """Get Top 10 Tech Stack (previously Tools) with multi-select filters - now merged with tech_stack"""
    with get_db_context() as db:
        query = db.query(
            Skill.name,
            func.count(JobSkill.id).label('count')
        ).join(JobSkill).join(Job).join(SkillType, Skill.skill_type_id == SkillType.id)\
        .filter(SkillType.name == 'tech_stack')
        
        if keyword_ids:
            ids = [int(x.strip()) for x in keyword_ids.split(',') if x.strip()]
            if ids:
                query = query.filter(Job.keyword_id.in_(ids))
        
        if locations:
            locs = [x.strip() for x in locations.split(',') if x.strip()]
            if locs:
                query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location.in_(locs))
        
        if months:
            mnths = [int(x.strip()) for x in months.split(',') if x.strip()]
            if mnths:
                query = query.filter(extract('month', Job.posted_date).in_(mnths))
        
        if years:
            yrs = [int(x.strip()) for x in years.split(',') if x.strip()]
            if yrs:
                query = query.filter(extract('year', Job.posted_date).in_(yrs))
        
        results = query.group_by(Skill.name).order_by(func.count(JobSkill.id).desc()).limit(limit).all()
        
        total_query = db.query(func.count(Job.id.distinct()))
        if keyword_ids:
            ids = [int(x.strip()) for x in keyword_ids.split(',') if x.strip()]
            if ids:
                total_query = total_query.filter(Job.keyword_id.in_(ids))
        if locations:
            locs = [x.strip() for x in locations.split(',') if x.strip()]
            if locs:
                total_query = total_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location.in_(locs))
        if months:
            mnths = [int(x.strip()) for x in months.split(',') if x.strip()]
            if mnths:
                total_query = total_query.filter(extract('month', Job.posted_date).in_(mnths))
        if years:
            yrs = [int(x.strip()) for x in years.split(',') if x.strip()]
            if yrs:
                total_query = total_query.filter(extract('year', Job.posted_date).in_(yrs))
        
        total_jobs = total_query.scalar() or 0
        
        return [
            {
                'rank': idx + 1,
                'skill_name': r[0],
                'count': r[1],
                'percentage': round((r[1] / total_jobs) * 100, 1) if total_jobs > 0 else 0,
                'total_jobs': total_jobs
            }
            for idx, r in enumerate(results)
        ]


@router.get("/api/dashboard/top-soft-skills")
async def get_top_soft_skills(
    keyword_ids: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
    months: Optional[str] = Query(None),
    years: Optional[str] = Query(None),
    limit: int = Query(10)
):
    """Get Top 10 Soft Skills with multi-select filters"""
    with get_db_context() as db:
        query = db.query(
            Skill.name,
            func.count(JobSkill.id).label('count')
        ).join(JobSkill).join(Job).join(SkillType, Skill.skill_type_id == SkillType.id)\
        .filter(SkillType.name == 'soft_skill')
        
        if keyword_ids:
            ids = [int(x.strip()) for x in keyword_ids.split(',') if x.strip()]
            if ids:
                query = query.filter(Job.keyword_id.in_(ids))
        
        if locations:
            locs = [x.strip() for x in locations.split(',') if x.strip()]
            if locs:
                query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location.in_(locs))
        
        if months:
            mnths = [int(x.strip()) for x in months.split(',') if x.strip()]
            if mnths:
                query = query.filter(extract('month', Job.posted_date).in_(mnths))
        
        if years:
            yrs = [int(x.strip()) for x in years.split(',') if x.strip()]
            if yrs:
                query = query.filter(extract('year', Job.posted_date).in_(yrs))
        
        results = query.group_by(Skill.name).order_by(func.count(JobSkill.job_id.distinct()).desc()).limit(limit).all()
        
        total_query = db.query(func.count(Job.id.distinct()))
        if keyword_ids:
            ids = [int(x.strip()) for x in keyword_ids.split(',') if x.strip()]
            if ids:
                total_query = total_query.filter(Job.keyword_id.in_(ids))
        if locations:
            locs = [x.strip() for x in locations.split(',') if x.strip()]
            if locs:
                total_query = total_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location.in_(locs))
        if months:
            mnths = [int(x.strip()) for x in months.split(',') if x.strip()]
            if mnths:
                total_query = total_query.filter(extract('month', Job.posted_date).in_(mnths))
        if years:
            yrs = [int(x.strip()) for x in years.split(',') if x.strip()]
            if yrs:
                total_query = total_query.filter(extract('year', Job.posted_date).in_(yrs))
        
        total_jobs = total_query.scalar() or 0
        
        return [
            {
                'rank': idx + 1,
                'skill_name': r[0],
                'count': r[1],
                'percentage': round((r[1] / total_jobs) * 100, 1) if total_jobs > 0 else 0,
                'total_jobs': total_jobs
            }
            for idx, r in enumerate(results)
        ]


@router.get("/api/dashboard/top-skills-by-type")
def get_top_skills_by_type(
    skill_type_id: int,
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Top N skills berdasarkan skill type dengan filter lengkap
    """
    try:
        skill_type = db.query(SkillType).filter(SkillType.id == skill_type_id).first()
        if not skill_type:
            return []
        
        total_jobs_query = db.query(Job)
        
        if keyword_id:
            total_jobs_query = total_jobs_query.filter(Job.keyword_id == keyword_id)
        if location:
            total_jobs_query = total_jobs_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
        if company:
            total_jobs_query = total_jobs_query.filter(Job.company == company)
        if employee_size:
            total_jobs_query = total_jobs_query.filter(Job.employee_size == employee_size)
        if month and month >= 1 and month <= 12:
            total_jobs_query = total_jobs_query.filter(extract('month', Job.posted_date) == month)
        if year and year > 1900:
            total_jobs_query = total_jobs_query.filter(extract('year', Job.posted_date) == year)
        
        total_jobs = total_jobs_query.count()
        
        if total_jobs == 0:
            return []
        
        query = db.query(
            Skill.id.label('skill_id'),
            Skill.name.label('skill_name'),
            SkillType.name.label('skill_type'),
            func.count(func.distinct(JobSkill.job_id)).label('job_count')
        ).join(
            JobSkill, JobSkill.skill_id == Skill.id
        ).join(
            SkillType, SkillType.id == Skill.skill_type_id
        ).join(
            Job, Job.id == JobSkill.job_id
        )
        
        query = query.filter(Skill.skill_type_id == skill_type_id)
        
        if keyword_id:
            query = query.filter(Job.keyword_id == keyword_id)
        if location:
            query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
        if company:
            query = query.filter(Job.company == company)
        if employee_size:
            query = query.filter(Job.employee_size == employee_size)
        if month and month >= 1 and month <= 12:
            query = query.filter(extract('month', Job.posted_date) == month)
        if year and year > 1900:
            query = query.filter(extract('year', Job.posted_date) == year)
        
        results = query.group_by(
            Skill.id, Skill.name, SkillType.name
        ).order_by(
            func.count(func.distinct(JobSkill.job_id)).desc()
        ).limit(limit).all()
        
        if not results:
            return []
        
        return [
            {
                'rank': idx + 1,
                'skill_name': r[1],
                'skill_type': r[2],
                'skill_type_id': skill_type_id,
                'job_count': r[3],
                'count': r[3],
                'total_jobs': total_jobs,
                'percentage': round((r[3] / total_jobs) * 100, 1) if total_jobs > 0 else 0
            }
            for idx, r in enumerate(results)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/api/dashboard/skill-types")
def get_skill_types(db: Session = Depends(get_db)):
    """
    Get all available skill types dengan ID untuk reference di frontend
    """
    skill_types = db.query(SkillType.id, SkillType.name, SkillType.description).all()
    
    return [
        {
            'id': st[0],
            'name': st[1],
            'description': st[2] or ''
        }
        for st in skill_types
    ]


@router.get("/api/dashboard/skill-trend/{skill_name}")
def get_skill_trend_detail(
    skill_name: str,
    skill_type_id: Optional[int] = None,
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Detail trend untuk skill tertentu - berapa banyak kemunculan per bulan
    """
    skill = db.query(Skill.id, Skill.skill_type_id, SkillType.name).join(
        SkillType, SkillType.id == Skill.skill_type_id
    ).filter(Skill.name == skill_name).first()
    
    if not skill:
        return {
            'error': 'Skill tidak ditemukan',
            'skill_name': skill_name,
            'data': []
        }
    
    skill_id, st_id, skill_type_name = skill
    
    query = db.query(
        extract('year', Job.posted_date).label('year'),
        extract('month', Job.posted_date).label('month'),
        func.count(JobSkill.id).label('count')
    ).select_from(Skill).join(
        JobSkill, JobSkill.skill_id == Skill.id
    ).join(
        Job, Job.id == JobSkill.job_id
    ).filter(Skill.id == skill_id)
    
    if keyword_id:
        query = query.filter(Job.keyword_id == keyword_id)
    if location:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        query = query.filter(Job.company == company)
    if employee_size:
        query = query.filter(Job.employee_size == employee_size)
    if month:
        query = query.filter(extract('month', Job.posted_date) == month)
    if year:
        query = query.filter(extract('year', Job.posted_date) == year)
    
    results = query.group_by(
        extract('year', Job.posted_date),
        extract('month', Job.posted_date)
    ).order_by(
        extract('year', Job.posted_date).asc(),
        extract('month', Job.posted_date).asc()
    ).all()
    
    trend_data = []
    for year, month, count in results:
        if year and month:
            month_str = f"{int(year)}-{int(month):02d}"
            trend_data.append({
                'month': month_str,
                'count': count
            })
    
    return {
        'skill_name': skill_name,
        'skill_type': skill_type_name,
        'skill_type_id': st_id,
        'data': trend_data,
        'months_count': len(trend_data)
    }


@router.get("/api/dashboard/all-skills-by-type")
def get_all_skills_by_type(
    skill_type_id: int,
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get ALL skills (tidak ada limit) untuk skill type tertentu dengan persentase berdasarkan lowongan unik
    """
    # Build base query for total jobs count
    total_jobs_query = db.query(Job)
    
    if keyword_id:
        total_jobs_query = total_jobs_query.filter(Job.keyword_id == keyword_id)
    if location:
        total_jobs_query = total_jobs_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        total_jobs_query = total_jobs_query.filter(Job.company == company)
    if employee_size:
        total_jobs_query = total_jobs_query.filter(Job.employee_size == employee_size)
    if month:
        total_jobs_query = total_jobs_query.filter(extract('month', Job.posted_date) == month)
    if year:
        total_jobs_query = total_jobs_query.filter(extract('year', Job.posted_date) == year)
    
    total_jobs = total_jobs_query.distinct(Job.id).count()
    
    if total_jobs == 0:
        return []
    
    query = db.query(
        Skill.id,
        Skill.name.label('skill_name'),
        SkillType.name.label('skill_type'),
        func.count(func.distinct(JobSkill.job_id)).label('job_count')
    ).join(
        JobSkill, JobSkill.skill_id == Skill.id
    ).join(
        SkillType, SkillType.id == Skill.skill_type_id
    ).join(
        Job, Job.id == JobSkill.job_id
    )
    
    query = query.filter(SkillType.id == skill_type_id)
    
    if keyword_id:
        query = query.filter(Job.keyword_id == keyword_id)
    if location:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        query = query.filter(Job.company == company)
    if employee_size:
        query = query.filter(Job.employee_size == employee_size)
    if month:
        query = query.filter(extract('month', Job.posted_date) == month)
    if year:
        query = query.filter(extract('year', Job.posted_date) == year)
    
    results = query.group_by(
        Skill.id, Skill.name, SkillType.name
    ).order_by(
        func.count(func.distinct(JobSkill.job_id)).desc()
    ).all()
    
    if not results:
        return []
    
    return [
        {
            'rank': idx + 1,
            'skill_name': r[1],
            'skill_type': r[2],
            'skill_type_id': skill_type_id,
            'count': r[3],
            'job_count': r[3],
            'total_jobs': total_jobs,
            'percentage': round((r[3] / total_jobs) * 100, 1) if total_jobs > 0 else 0
        }
        for idx, r in enumerate(results)
    ]


@router.get("/api/dashboard/trend-by-month")
def get_trend_by_month(
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skill_type_id: Optional[int] = None,
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get top skills trend organized by month
    """
    months_query = db.query(
        extract('year', Job.posted_date).label('year'),
        extract('month', Job.posted_date).label('month')
    ).distinct().filter(
        Job.posted_date.isnot(None)
    )
    
    if keyword_id:
        months_query = months_query.filter(Job.keyword_id == keyword_id)
    if location:
        months_query = months_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        months_query = months_query.filter(Job.company == company)
    if employee_size:
        months_query = months_query.filter(Job.employee_size == employee_size)
    if month:
        months_query = months_query.filter(extract('month', Job.posted_date) == month)
    if year:
        months_query = months_query.filter(extract('year', Job.posted_date) == year)
    
    months = sorted(months_query.all(), reverse=True)

    year_col = extract('year', Job.posted_date).label('year')
    month_col = extract('month', Job.posted_date).label('month')

    jobs_by_month_query = db.query(
        year_col,
        month_col,
        func.count(func.distinct(Job.id)).label('total_jobs')
    ).filter(
        Job.posted_date.isnot(None)
    )

    if keyword_id:
        jobs_by_month_query = jobs_by_month_query.filter(Job.keyword_id == keyword_id)
    if location:
        jobs_by_month_query = jobs_by_month_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
    if company:
        jobs_by_month_query = jobs_by_month_query.filter(Job.company == company)
    if employee_size:
        jobs_by_month_query = jobs_by_month_query.filter(Job.employee_size == employee_size)
    if month:
        jobs_by_month_query = jobs_by_month_query.filter(extract('month', Job.posted_date) == month)
    if year:
        jobs_by_month_query = jobs_by_month_query.filter(extract('year', Job.posted_date) == year)

    jobs_by_month = {
        (int(r.year), int(r.month)): int(r.total_jobs)
        for r in jobs_by_month_query.group_by(year_col, month_col).all()
        if r.year and r.month
    }
    
    result = []
    
    for year, month in months:
        if not year or not month:
            continue
        
        month_key = f"{int(year)}-{int(month):02d}"
        
        query = db.query(
            Skill.name.label('skill_name'),
            SkillType.name.label('skill_type'),
            func.count(JobSkill.id).label('count')
        ).join(
            JobSkill, JobSkill.skill_id == Skill.id
        ).join(
            SkillType, SkillType.id == Skill.skill_type_id
        ).join(
            Job, Job.id == JobSkill.job_id
        ).filter(
            extract('year', Job.posted_date) == year,
            extract('month', Job.posted_date) == month
        )
        
        if keyword_id:
            query = query.filter(Job.keyword_id == keyword_id)
        if location:
            query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
        if company:
            query = query.filter(Job.company == company)
        if employee_size:
            query = query.filter(Job.employee_size == employee_size)
        if skill_type_id:
            query = query.filter(Skill.skill_type_id == skill_type_id)
        
        if skill_type_id:
            skills = query.group_by(
                Skill.id, Skill.name, SkillType.name
            ).order_by(
                func.count(JobSkill.id).desc()
            ).all()
        else:
            skills = query.group_by(
                Skill.id, Skill.name, SkillType.name
            ).order_by(
                func.count(JobSkill.id).desc()
            ).limit(limit).all()
        
        month_data = {
            'month': month_key,
            'year': int(year),
            'month_num': int(month),
            'total_jobs': jobs_by_month.get((int(year), int(month)), 0),
            'skills': [
                {
                    'rank': idx + 1,
                    'skill_name': s[0],
                    'skill_type': s[1],
                    'count': s[2]
                }
                for idx, s in enumerate(skills)
            ]
        }
        
        result.append(month_data)
    
    return result


@router.get("/api/dashboard/top-companies-by-skill/{skill_name}", response_model=TopCompaniesResponse)
def get_top_companies_by_skill(
    skill_name: str,
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get top companies requiring a specific skill
    """
    try:
        normalized_skill_name = skill_name.strip().lower()
        skill = db.query(Skill).filter(
            func.lower(Skill.normalized_name) == normalized_skill_name
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
        
        query = db.query(
            Job.company,
            Job.company_linkedin_url,
            func.count(func.distinct(Job.id)).label('job_count')
        ).join(
            JobSkill, Job.id == JobSkill.job_id
        ).filter(
            JobSkill.skill_id == skill.id,
            Job.company.isnot(None),
            Job.company != ''
        )
        
        if keyword_id:
            query = query.filter(Job.keyword_id == keyword_id)
        if location:
            query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
        if employee_size:
            query = query.filter(Job.employee_size == employee_size)
        if month:
            query = query.filter(extract('month', Job.posted_date) == month)
        if year:
            query = query.filter(extract('year', Job.posted_date) == year)
        
        company_data = query.group_by(
            Job.company, Job.company_linkedin_url
        ).order_by(
            func.count(func.distinct(Job.id)).desc()
        ).limit(limit).all()
        
        if not company_data:
            return TopCompaniesResponse(
                skill_name=skill_name,
                total_jobs_with_skill=0,
                companies=[]
            )
        
        total_query = db.query(
            func.count(func.distinct(Job.id)).label('total')
        ).join(
            JobSkill, Job.id == JobSkill.job_id
        ).filter(
            JobSkill.skill_id == skill.id
        )
        
        if keyword_id:
            total_query = total_query.filter(Job.keyword_id == keyword_id)
        if location:
            total_query = total_query.join(JobAnalysis, JobAnalysis.job_id == Job.id).filter(JobAnalysis.location == location)
        if employee_size:
            total_query = total_query.filter(Job.employee_size == employee_size)
        if month:
            total_query = total_query.filter(extract('month', Job.posted_date) == month)
        if year:
            total_query = total_query.filter(extract('year', Job.posted_date) == year)
        
        total_jobs = total_query.scalar() or 0
        
        companies = [
            {
                "rank": idx + 1,
                "company": company,
                "company_linkedin_url": company_url,
                "job_count": int(count),
                "percentage": round((int(count) / total_jobs * 100) if total_jobs > 0 else 0, 1)
            }
            for idx, (company, company_url, count) in enumerate(company_data)
        ]
        
        return {
            "skill_name": skill_name,
            "total_jobs_with_skill": total_jobs,
            "companies": companies
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/api/dashboard/top-skills-by-type-from-analysis")
def get_top_skills_by_type_from_analysis(
    skill_type_id: int,
    keyword_id: Optional[int] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get top skills FROM JOB_ANALYSIS table dengan filter location"""
    try:
        query = db.query(JobAnalysis)
        
        if keyword_id:
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if keyword:
                query = query.filter(JobAnalysis.keyword == keyword.keyword)
        if location:
            query = query.filter(JobAnalysis.location == location)
        if company:
            query = query.filter(JobAnalysis.company == company)
        if employee_size:
            query = query.join(Job, Job.id == JobAnalysis.job_id).filter(Job.employee_size == employee_size)
        if month:
            query = query.filter(extract('month', JobAnalysis.posted_date) == month)
        if year:
            query = query.filter(extract('year', JobAnalysis.posted_date) == year)
        
        results = query.all()
        
        if not results:
            return []
        
        skill_counts = {}
        total_jobs = len(results)
        
        for job in results:
            skills_text = None
            if skill_type_id == 1:
                skills_text = job.soft_skill
            elif skill_type_id == 2:
                skills_text = job.technical_skill
            elif skill_type_id == 3:
                skills_text = job.tech_stack
            
            if skills_text:
                try:
                    if skills_text.startswith('['):
                        skills = json.loads(skills_text.replace("'", '"'))
                    else:
                        skills = [skills_text]
                    for skill in skills:
                        if skill and skill.strip():
                            skill_counts[skill.strip()] = skill_counts.get(skill.strip(), 0) + 1
                except:
                    pass
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'rank': idx + 1,
                'skill_name': skill_name,
                'count': count,
                'job_count': count,
                'total_jobs': total_jobs,
                'percentage': round((count / total_jobs) * 100, 1) if total_jobs > 0 else 0
            }
            for idx, (skill_name, count) in enumerate(sorted_skills)
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

@router.get("/api/dashboard/skills-distribution-from-analysis")
def get_skills_distribution_from_analysis(
    skill_type_id: Optional[int] = None,
    location: Optional[str] = None,
    keyword_id: Optional[int] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get skills distribution FROM JOB_ANALYSIS table
    """
    try:
        query = db.query(JobAnalysis)
        
        if location:
            query = query.filter(JobAnalysis.location == location)
        
        if keyword_id:
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if keyword:
                query = query.filter(JobAnalysis.keyword == keyword.keyword)
        
        if company:
            query = query.filter(JobAnalysis.company == company)
            
        if employee_size:
            query = query.join(Job, Job.id == JobAnalysis.job_id).filter(Job.employee_size == employee_size)
        
        if month:
            query = query.filter(extract('month', JobAnalysis.posted_date) == month)
        
        if year:
            query = query.filter(extract('year', JobAnalysis.posted_date) == year)
        
        results = query.all()
        
        if not results:
            return []
        
        tech_stack_skills = {}
        technical_skills = {}
        soft_skills = {}
        
        for job in results:
            if job.tech_stack:
                try:
                    skills_text = job.tech_stack
                    if skills_text.startswith('['):
                        skills = json.loads(skills_text.replace("'", '"'))
                    else:
                        skills = [s.strip() for s in skills_text.split(',')]
                    
                    for skill in skills:
                        if skill and len(skill) > 1:
                            tech_stack_skills[skill] = tech_stack_skills.get(skill, 0) + 1
                except Exception as e:
                    print(f"Error parsing tech_stack: {e}")
            
            if job.technical_skill:
                try:
                    skills_text = job.technical_skill
                    if skills_text.startswith('['):
                        skills = json.loads(skills_text.replace("'", '"'))
                    else:
                        skills = [s.strip() for s in skills_text.split(',')]
                    
                    for skill in skills:
                        if skill and len(skill) > 1:
                            technical_skills[skill] = technical_skills.get(skill, 0) + 1
                except Exception as e:
                    print(f"Error parsing technical_skill: {e}")
            
            if job.soft_skill:
                try:
                    skills_text = job.soft_skill
                    if skills_text.startswith('['):
                        skills = json.loads(skills_text.replace("'", '"'))
                    else:
                        skills = [s.strip() for s in skills_text.split(',')]
                    
                    for skill in skills:
                        if skill and len(skill) > 1:
                            soft_skills[skill] = soft_skills.get(skill, 0) + 1
                except Exception as e:
                    print(f"Error parsing soft_skill: {e}")
        
        total_tech = sum(tech_stack_skills.values())
        total_tech_skill = sum(technical_skills.values())
        total_soft = sum(soft_skills.values())
        total_all = total_tech + total_tech_skill + total_soft
        
        def get_top_n(skills_dict, n=limit):
            sorted_skills = sorted(skills_dict.items(), key=lambda x: x[1], reverse=True)[:n]
            return [{'name': k, 'count': v} for k, v in sorted_skills]
        
        result = []
        
        if tech_stack_skills:
            result.append({
                'skill_type': 'tech_stack',
                'count': total_tech,
                'percentage': round((total_tech / total_all) * 100, 1) if total_all > 0 else 0,
                'top_skills': get_top_n(tech_stack_skills)
            })
        
        if technical_skills:
            result.append({
                'skill_type': 'technical_skill',
                'count': total_tech_skill,
                'percentage': round((total_tech_skill / total_all) * 100, 1) if total_all > 0 else 0,
                'top_skills': get_top_n(technical_skills)
            })
        
        if soft_skills:
            result.append({
                'skill_type': 'soft_skill',
                'count': total_soft,
                'percentage': round((total_soft / total_all) * 100, 1) if total_all > 0 else 0,
                'top_skills': get_top_n(soft_skills)
            })
        
        type_name_map = {
            1: 'soft_skill',
            2: 'technical_skill',
            3: 'tech_stack'
        }
        
        target_type = type_name_map.get(skill_type_id)
        if not target_type:
            return result
            
        type_result = next((r for r in result if r['skill_type'] == target_type), None)
        if type_result:
            top_skills = type_result['top_skills'][:limit]
            return [
                {
                    'rank': idx + 1,
                    'skill_name': skill['name'],
                    'count': skill['count'],
                    'job_count': skill['count'],
                    'percentage': round((skill['count'] / type_result['count']) * 100, 1) if type_result['count'] > 0 else 0
                }
                for idx, skill in enumerate(top_skills)
            ]
        return []
        
    except Exception as e:
        print(f"Error in skills-distribution-from-analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
