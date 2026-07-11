from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from typing import List, Optional

from database.connection import get_db
from database.models import Job, Skill, SkillType, JobSkill, Keyword, JobAnalysis
from utils.job_title_normalizer import JobTitleNormalizer
from llm.skill_dedup_normalized import SkillNormalizer
from .schemas import (
    SkillCount, TrendData, SkillMatcherRequest, SkillMatcherResponse,
    SkillDetail, CooccurrenceResponse, CooccurrenceNode, CooccurrenceLink
)

router = APIRouter(tags=["skills"])

# Mapping dari nilai frontend → nama SkillType di database
SKILL_TYPE_MAP = {
    "tech_stack": "tech_stack",
    "technical_skill": "technical_skill",
    "soft_skill": "soft_skill",
}


@router.get("/api/skills/top", response_model=List[SkillCount])
async def get_top_skills(
    limit: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skill_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Top skills dengan filter"""
    # Base query
    query = db.query(
        Skill.id,
        Skill.name,
        SkillType.name.label('skill_type'),
        func.count(JobSkill.id).label('count')
    ).join(
        JobSkill, JobSkill.skill_id == Skill.id
    ).join(
        SkillType, SkillType.id == Skill.skill_type_id
    ).join(
        Job, Job.id == JobSkill.job_id
    ).join(
        Keyword, Keyword.id == Job.keyword_id
    )
    
    # Apply filters
    filters = []
    
    if keyword:
        filters.append(Keyword.keyword == keyword)
    
    if city:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id)
        filters.append(JobAnalysis.location == city)

    if company:
        filters.append(Job.company == company)
        
    if employee_size:
        filters.append(Job.employee_size == employee_size)
    
    if month:
        filters.append(extract('month', Job.posted_date) == month)
    
    if year:
        filters.append(extract('year', Job.posted_date) == year)
    
    if skill_type:
        filters.append(SkillType.name == skill_type)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Group and order
    results = query.group_by(
        Skill.id, Skill.name, SkillType.name
    ).order_by(
        func.count(JobSkill.id).desc()
    ).limit(limit).all()
    
    return [
        SkillCount(id=r[0], skill_name=r[1], skill_type=r[2], count=r[3])
        for r in results
    ]


@router.get("/api/trends", response_model=List[TrendData])
async def get_skill_trends(
    skill_names: Optional[str] = Query(None, description="Comma-separated skill names"),
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    company: Optional[str] = None,
    employee_size: Optional[str] = None,
    skill_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Trend skill per bulan/tahun"""
    # Base query
    query = db.query(
        extract('month', Job.posted_date).label('month'),
        extract('year', Job.posted_date).label('year'),
        Skill.name,
        SkillType.name.label('skill_type'),
        func.count(JobSkill.id).label('count')
    ).join(
        JobSkill, JobSkill.skill_id == Skill.id
    ).join(
        SkillType, SkillType.id == Skill.skill_type_id
    ).join(
        Job, Job.id == JobSkill.job_id
    ).join(
        Keyword, Keyword.id == Job.keyword_id
    ).filter(
        Job.posted_date.isnot(None)
    )
    
    # Apply filters
    filters = []
    
    if skill_names:
        skill_list = [s.strip() for s in skill_names.split(',')]
        filters.append(Skill.name.in_(skill_list))
    
    if keyword:
        filters.append(Keyword.keyword == keyword)
    
    if city:
        query = query.join(JobAnalysis, JobAnalysis.job_id == Job.id)
        filters.append(JobAnalysis.location == city)

    if company:
        filters.append(Job.company == company)
        
    if employee_size:
        filters.append(Job.employee_size == employee_size)
    
    if skill_type:
        filters.append(SkillType.name == skill_type)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Group and order
    results = query.group_by(
        extract('month', Job.posted_date),
        extract('year', Job.posted_date),
        Skill.name,
        SkillType.name
    ).order_by(
        extract('year', Job.posted_date),
        extract('month', Job.posted_date)
    ).all()
    
    return [
        TrendData(
            month=int(r.month),
            year=int(r.year),
            skill_name=r.name,
            skill_type=r.skill_type,
            count=r.count
        )
        for r in results
    ]


@router.get("/api/skills/by-category")
async def get_skills_by_category(
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Skill count grouped by category/type"""
    query = db.query(
        SkillType.name.label('skill_type'),
        func.count(JobSkill.id).label('count')
    ).join(
        Skill, Skill.skill_type_id == SkillType.id
    ).join(
        JobSkill, JobSkill.skill_id == Skill.id
    ).join(
        Job, Job.id == JobSkill.job_id
    ).join(
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
    
    results = query.group_by(SkillType.name).all()
    
    return {
        r.skill_type: r.count
        for r in results
    }


@router.post("/api/skill-matcher", response_model=SkillMatcherResponse)
@router.post("/skill-matcher", response_model=SkillMatcherResponse)
def match_skills(request: SkillMatcherRequest, db: Session = Depends(get_db)):
    """
    Menghitung kesesuaian skill user terhadap target pekerjaan.
    """
    try:
        target_title = request.targetJobTitle.strip()
        user_skills = request.userSkills
        skill_type_filter = request.skillType or "all"
        employee_size = request.employeeSize

        if not target_title:
            return SkillMatcherResponse(matchScore=0, matchedSkills=[], missingSkills=[])

        # --- 1. Temukan jobs yang cocok dengan target job title ---
        normalizer = JobTitleNormalizer()
        clean_title = normalizer.clean_title(target_title)

        jobs_query = db.query(Job).filter(
            or_(
                Job.job_title.ilike(f"%{clean_title}%"),
                Job.job_title.ilike(f"%{target_title}%")
            )
        )
        if employee_size:
            jobs_query = jobs_query.filter(Job.employee_size == employee_size)
        jobs = jobs_query.all()

        if not jobs:
            matching_keyword = db.query(Keyword).filter(
                Keyword.keyword.ilike(f"%{target_title}%")
            ).first()
            if matching_keyword:
                jobs_query = db.query(Job).filter(Job.keyword_id == matching_keyword.id)
                if employee_size:
                    jobs_query = jobs_query.filter(Job.employee_size == employee_size)
                jobs = jobs_query.all()

        if not jobs:
            words = [w for w in clean_title.split() if len(w) > 2]
            if words:
                query_filters = [Job.job_title.ilike(f"%{w}%") for w in words]
                jobs_query = db.query(Job).filter(or_(*query_filters))
                if employee_size:
                    jobs_query = jobs_query.filter(Job.employee_size == employee_size)
                jobs = jobs_query.all()

        if not jobs:
            return SkillMatcherResponse(matchScore=0, matchedSkills=[], missingSkills=[])

        job_ids = [j.id for j in jobs]
        total_jobs_count = len(job_ids)

        def get_top_skills_by_type(type_name: str, limit: int):
            rows = db.query(
                Skill.id,
                Skill.name,
                Skill.normalized_name,
                func.count(func.distinct(JobSkill.job_id)).label('demand')
            ).join(
                JobSkill, JobSkill.skill_id == Skill.id
            ).join(
                SkillType, SkillType.id == Skill.skill_type_id
            ).filter(
                JobSkill.job_id.in_(job_ids),
                SkillType.name == type_name
            ).group_by(
                Skill.id, Skill.name, Skill.normalized_name
            ).order_by(
                func.count(func.distinct(JobSkill.job_id)).desc()
            ).limit(limit).all()
            return rows

        top_skills_raw = []

        if skill_type_filter == "all":
            TOP_PER_TYPE = 100
            for type_name in ["tech_stack", "technical_skill", "soft_skill"]:
                rows = get_top_skills_by_type(type_name, TOP_PER_TYPE)
                top_skills_raw.extend(rows)
        else:
            db_type_name = SKILL_TYPE_MAP.get(skill_type_filter, skill_type_filter)
            rows = get_top_skills_by_type(db_type_name, 100)
            top_skills_raw.extend(rows)

        if not top_skills_raw:
            return SkillMatcherResponse(matchScore=0, matchedSkills=[], missingSkills=[])

        merged_demand: dict[str, int] = {}
        display_names: dict[str, str] = {}

        for skill_id, name, norm_name, demand in top_skills_raw:
            norm_key = norm_name if norm_name else SkillNormalizer.normalize_skill(name)
            if not norm_key:
                continue
            existing = merged_demand.get(norm_key, 0)
            merged_demand[norm_key] = max(existing, demand)
            if norm_key not in display_names or len(name) < len(display_names[norm_key]):
                display_names[norm_key] = name

        sorted_skills = sorted(merged_demand.items(), key=lambda x: x[1], reverse=True)

        user_skills_norm: set[str] = set()
        for s in user_skills:
            s_clean = s.strip()
            if not s_clean:
                continue
            canonical, found = SkillNormalizer.get_canonical_form(s_clean)
            if found:
                user_skills_norm.add(SkillNormalizer.normalize_skill(canonical))
            else:
                user_skills_norm.add(SkillNormalizer.normalize_skill(s_clean))

        total_weight = sum(demand for _, demand in sorted_skills)

        matched_skills = []
        missing_skills = []
        matched_details = []
        missing_details = []
        matched_weight = 0

        for norm_key, demand in sorted_skills:
            display_name = display_names.get(norm_key, norm_key)
            demand_pct = round((demand / total_jobs_count) * 100, 1) if total_jobs_count > 0 else 0.0
            contribution = round((demand / total_weight) * 100, 1) if total_weight > 0 else 0.0

            detail = SkillDetail(
                name=display_name,
                demand=demand,
                demandPct=demand_pct,
                contribution=contribution
            )

            if norm_key in user_skills_norm:
                matched_skills.append(display_name)
                matched_details.append(detail)
                matched_weight += demand
            else:
                missing_skills.append(display_name)
                missing_details.append(detail)

        match_score = (
            round((matched_weight / total_weight) * 100) if total_weight > 0 else 0
        )

        return SkillMatcherResponse(
            matchScore=match_score,
            matchedSkills=matched_skills,
            missingSkills=missing_skills,
            matchedDetails=matched_details,
            missingDetails=missing_details,
            totalJobsAnalyzed=total_jobs_count
        )
    except Exception as e:
        print(f"Error in match_skills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error matching skills: {str(e)}")


@router.get("/api/skill-cooccurrence", response_model=CooccurrenceResponse)
@router.get("/skill-cooccurrence", response_model=CooccurrenceResponse)
def get_skill_cooccurrence(
    skill: str = Query(..., description="Query skill name"),
    keyword_id: Optional[int] = Query(None, description="Filter by job keyword ID"),
    employee_size: Optional[str] = Query(None, description="Filter by employee size"),
    db: Session = Depends(get_db)
):
    """
    Menampilkan hubungan antar skill berdasarkan dataset lowongan kerja dengan filter keyword dan employee size.
    """
    try:
        skill_query = skill.strip()

        db_skill = db.query(Skill).filter(
            or_(
                Skill.name.ilike(skill_query),
                Skill.normalized_name == skill_query.lower()
            )
        ).first()

        if not db_skill:
            db_skill = db.query(Skill).filter(
                Skill.name.ilike(f"%{skill_query}%")
            ).first()

        if not db_skill:
            return CooccurrenceResponse(
                nodes=[CooccurrenceNode(id=skill_query, frequency=0)],
                links=[]
            )

        job_ids_query = db.query(JobSkill.job_id).join(
            Job, Job.id == JobSkill.job_id
        ).filter(
            JobSkill.skill_id == db_skill.id
        )

        if keyword_id:
            job_ids_query = job_ids_query.filter(Job.keyword_id == keyword_id)
        if employee_size:
            job_ids_query = job_ids_query.filter(Job.employee_size == employee_size)

        job_ids = [j[0] for j in job_ids_query.all()]

        if not job_ids:
            freqs_query = db.query(func.count(JobSkill.id)).join(
                Job, Job.id == JobSkill.job_id
            ).filter(
                JobSkill.skill_id == db_skill.id
            )
            if keyword_id:
                freqs_query = freqs_query.filter(Job.keyword_id == keyword_id)
            if employee_size:
                freqs_query = freqs_query.filter(Job.employee_size == employee_size)
            freq = freqs_query.scalar() or 0
            return CooccurrenceResponse(
                nodes=[CooccurrenceNode(id=db_skill.name, frequency=freq)],
                links=[]
            )

        co_skills_query = db.query(
            Skill.name,
            func.count(JobSkill.id).label('weight')
        ).join(
            JobSkill, JobSkill.skill_id == Skill.id
        ).filter(
            JobSkill.job_id.in_(job_ids)
        ).filter(
            Skill.id != db_skill.id
        ).group_by(
            Skill.name
        ).order_by(
            func.count(JobSkill.id).desc()
        ).limit(20).all()

        node_names = [db_skill.name] + [cs[0] for cs in co_skills_query]

        freq_map = {}
        if node_names:
            freqs_query = db.query(
                Skill.name,
                func.count(JobSkill.id).label('count')
            ).join(
                JobSkill, JobSkill.skill_id == Skill.id
            ).join(
                Job, Job.id == JobSkill.job_id
            ).filter(
                Skill.name.in_(node_names)
            )

            if keyword_id:
                freqs_query = freqs_query.filter(Job.keyword_id == keyword_id)
            if employee_size:
                freqs_query = freqs_query.filter(Job.employee_size == employee_size)

            freqs = freqs_query.group_by(Skill.name).all()
            freq_map = {name: count for name, count in freqs}

        nodes = [
            CooccurrenceNode(id=name, frequency=freq_map.get(name, 0))
            for name in node_names
        ]

        links = [
            CooccurrenceLink(
                source=db_skill.name,
                target=cs[0],
                weight=int(cs[1])
            )
            for cs in co_skills_query
        ]

        return CooccurrenceResponse(nodes=nodes, links=links)
    except Exception as e:
        print(f"Error in get_skill_cooccurrence: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching co-occurrences: {str(e)}"
        )


@router.get("/api/skills/list", response_model=List[str])
@router.get("/skills/list", response_model=List[str])
def get_all_skills_list(db: Session = Depends(get_db)):
    """Get list of all skill names in database ordered by frequency"""
    try:
        results = db.query(
            Skill.name
        ).join(
            JobSkill, JobSkill.skill_id == Skill.id
        ).group_by(
            Skill.name
        ).order_by(
            func.count(JobSkill.id).desc()
        ).all()
        return [r[0] for r in results]
    except Exception as e:
        print(f"Error in get_all_skills_list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
