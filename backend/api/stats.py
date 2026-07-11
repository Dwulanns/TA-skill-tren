from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
import re

from database.connection import get_db
from database.models import Job, Skill, SkillType, JobSkill, Keyword, JobAnalysis
from .schemas import Statistics, EmployeeSizeResponse, FilterOptions, KeywordOption, CityOption, CompanyOption, EmployeeSizeOption

router = APIRouter(tags=["stats"])

@router.get("/api/employee-sizes", response_model=List[EmployeeSizeResponse])
@router.get("/employee-sizes", response_model=List[EmployeeSizeResponse])
def get_employee_sizes(db: Session = Depends(get_db)):
    """Get distinct employee sizes with counts from jobs table"""
    sizes = db.query(
        Job.employee_size,
        func.count(Job.id).label('count')
    ).filter(
        Job.employee_size.isnot(None),
        Job.employee_size != ''
    ).group_by(
        Job.employee_size
    ).all()
    
    def get_size_sort_key(size_str: str) -> int:
        if not size_str:
            return 0
        match = re.search(r'\d+', size_str)
        if match:
            return int(match.group())
        return 999999
        
    sorted_sizes = sorted(sizes, key=lambda x: get_size_sort_key(x[0]))
    return [
        EmployeeSizeResponse(size=s[0], count=s[1])
        for s in sorted_sizes
    ]


@router.get("/api/stats", response_model=Statistics)
async def get_statistics(db: Session = Depends(get_db)):
    """Statistik umum"""
    total_jobs = db.query(Job).count()
    processed_jobs = db.query(Job).join(JobSkill).distinct().count()
    total_skills = db.query(JobSkill).count()
    unique_skills = db.query(Skill).count()
    
    # Skills by type
    skills_by_type = {}
    skill_types = db.query(SkillType).all()
    for st in skill_types:
        count = db.query(Skill).filter(Skill.skill_type_id == st.id).count()
        skills_by_type[st.name] = count
    
    return Statistics(
        total_jobs=total_jobs,
        total_skills=total_skills,
        unique_skills=unique_skills,
        processed_jobs=processed_jobs,
        skills_by_type=skills_by_type
    )


@router.get("/api/filters", response_model=FilterOptions)
async def get_filter_options(db: Session = Depends(get_db)):
    """
    Ambil opsi untuk filter
    
    - Location: dari tabel job_analysis
    - Keyword, Company, Month, Year: dari tabel jobs
    """
    # Keywords dari tabel JOBS
    keywords = db.query(
        Keyword.id, 
        Keyword.keyword
    ).join(
        Job, Job.keyword_id == Keyword.id
    ).distinct().order_by(
        Keyword.keyword
    ).all()
    keywords_list = [KeywordOption(id=k.id, keyword=k.keyword) for k in keywords]
    
    # LOCATIONS DARI JOB_ANALYSIS (bukan dari jobs)
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
    
    cities_list = [CityOption(city=loc[0], count=loc[1]) for loc in locations]
    
    # Companies dari tabel JOBS
    companies = db.query(
        Job.company,
        func.count(Job.id).label('count')
    ).filter(
        Job.company.isnot(None),
        Job.company != ''
    ).group_by(
        Job.company
    ).order_by(
        func.count(Job.id).desc()
    ).limit(100).all()
    
    companies_list = [CompanyOption(company=c[0], count=c[1]) for c in companies]
    
    # Employee Sizes dari tabel JOBS
    sizes = db.query(
        Job.employee_size,
        func.count(Job.id).label('count')
    ).filter(
        Job.employee_size.isnot(None),
        Job.employee_size != ''
    ).group_by(
        Job.employee_size
    ).all()
    
    def get_size_sort_key(size_str: str) -> int:
        if not size_str:
            return 0
        match = re.search(r'\d+', size_str)
        if match:
            return int(match.group())
        return 999999
        
    sorted_sizes = sorted(sizes, key=lambda x: get_size_sort_key(x[0]))
    employee_sizes_list = [EmployeeSizeOption(employee_size=s[0], count=s[1]) for s in sorted_sizes]
    
    # Months & Years dari tabel JOBS
    dates = db.query(
        extract('month', Job.posted_date).label('month'),
        extract('year', Job.posted_date).label('year')
    ).distinct().filter(
        Job.posted_date.isnot(None)
    ).all()
    
    months = sorted(list(set([int(d.month) for d in dates if d.month])))
    years = sorted(list(set([int(d.year) for d in dates if d.year])), reverse=True)
    
    # Skill types
    skill_types = db.query(SkillType.name).order_by(SkillType.name).all()
    skill_types_list = [st[0] for st in skill_types]
    
    # Ambil tanggal ekstraksi terakhir dari job_analysis
    last_extraction = db.query(func.max(JobAnalysis.extracted_at)).scalar()
    last_extraction_str = last_extraction.isoformat() if last_extraction else None
    
    return FilterOptions(
        keywords=keywords_list,
        cities=cities_list,
        companies=companies_list,
        employee_sizes=employee_sizes_list,
        months=months,
        years=years,
        skill_types=skill_types_list,
        last_extraction_at=last_extraction_str
    )
