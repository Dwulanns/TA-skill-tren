"""
Database Query Helper Module
Provides reusable database query functions to reduce duplication.
Applies DRY principle by centralizing common database operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from typing import List, Dict, Optional, Tuple
from database.models import Job, Skill, SkillType, JobSkill, Keyword, JobAnalysis


class QueryBuilder:
    """Builds reusable database queries for common operations"""
    
    @staticmethod
    def build_skill_count_query(
        db: Session,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        skill_type: Optional[str] = None
    ):
        """
        Build base query for skill count statistics
        
        Args:
            db: Database session
            keyword: Filter by keyword (optional)
            city: Filter by city/location (optional)
            month: Filter by month (optional)
            year: Filter by year (optional)
            skill_type: Filter by skill type (optional)
            
        Returns:
            SQLAlchemy Query object
        """
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
        filters = QueryBuilder._build_filters(
            keyword=keyword,
            city=city,
            month=month,
            year=year,
            skill_type=skill_type
        )
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query
    
    @staticmethod
    def build_skill_trend_query(
        db: Session,
        skill_names: Optional[List[str]] = None,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        skill_type: Optional[str] = None
    ):
        """
        Build query for skill trends over time
        
        Args:
            db: Database session
            skill_names: Filter by specific skill names (optional)
            keyword: Filter by keyword (optional)
            city: Filter by city/location (optional)
            skill_type: Filter by skill type (optional)
            
        Returns:
            SQLAlchemy Query object
        """
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
            filters.append(Skill.name.in_(skill_names))
        
        if keyword:
            filters.append(Keyword.keyword == keyword)
        
        if city:
            filters.append(Job.location == city)
        
        if skill_type:
            filters.append(SkillType.name == skill_type)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query
    
    @staticmethod
    def build_job_list_query(
        db: Session,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ):
        """
        Build query for job listings
        
        Args:
            db: Database session
            keyword: Filter by keyword (optional)
            city: Filter by city/location (optional)
            month: Filter by month (optional)
            year: Filter by year (optional)
            
        Returns:
            SQLAlchemy Query object
        """
        query = db.query(Job, Keyword.keyword).join(
            Keyword, Keyword.id == Job.keyword_id
        )
        
        # Apply filters
        filters = QueryBuilder._build_filters(
            keyword=keyword,
            city=city,
            month=month,
            year=year
        )
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query
    
    @staticmethod
    def build_skill_category_query(
        db: Session,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None
    ):
        """
        Build query for skills grouped by category
        
        Args:
            db: Database session
            keyword: Filter by keyword (optional)
            city: Filter by city/location (optional)
            month: Filter by month (optional)
            year: Filter by year (optional)
            
        Returns:
            SQLAlchemy Query object
        """
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
        filters = QueryBuilder._build_filters(
            keyword=keyword,
            city=city,
            month=month,
            year=year
        )
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query
    
    @staticmethod
    def _build_filters(
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        skill_type: Optional[str] = None
    ) -> List:
        """
        Build filter conditions for database queries
        
        Args:
            keyword: Keyword filter
            city: City filter
            month: Month filter
            year: Year filter
            skill_type: Skill type filter
            
        Returns:
            List of filter conditions
        """
        filters = []
        
        if keyword:
            filters.append(Keyword.keyword == keyword)
        
        if city:
            filters.append(Job.location == city)
        
        if month:
            filters.append(extract('month', Job.posted_date) == month)
        
        if year:
            filters.append(extract('year', Job.posted_date) == year)
        
        if skill_type:
            filters.append(SkillType.name == skill_type)
        
        return filters


class DatabaseRepository:
    """High-level database operations repository"""
    
    @staticmethod
    def get_filter_options(db: Session) -> Dict:
        """
        Get all available filter options
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with keywords, cities, months, years, skill_types
        """
        # Get keywords with jobs
        keywords = db.query(
            Keyword.id,
            Keyword.keyword
        ).join(
            Job, Job.keyword_id == Keyword.id
        ).distinct().order_by(
            Keyword.keyword
        ).all()
        
        # Get cities
        cities = db.query(
            Job.location,
            func.count(Job.id).label('count')
        ).filter(
            Job.location.isnot(None)
        ).group_by(
            Job.location
        ).order_by(
            func.count(Job.id).desc()
        ).all()
        
        # Get months and years
        dates = db.query(
            extract('month', Job.posted_date).label('month'),
            extract('year', Job.posted_date).label('year')
        ).distinct().filter(
            Job.posted_date.isnot(None)
        ).all()
        
        months = sorted(list(set([int(d.month) for d in dates if d.month])))
        years = sorted(list(set([int(d.year) for d in dates if d.year])), reverse=True)
        
        # Get skill types
        skill_types = db.query(SkillType.name).order_by(SkillType.name).all()
        
        return {
            'keywords': keywords,
            'cities': cities,
            'months': months,
            'years': years,
            'skill_types': [st[0] for st in skill_types]
        }
    
    @staticmethod
    def get_statistics(db: Session) -> Dict:
        """
        Get overall statistics
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with statistics
        """
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
        
        return {
            'total_jobs': total_jobs,
            'total_skills': total_skills,
            'unique_skills': unique_skills,
            'processed_jobs': processed_jobs,
            'skills_by_type': skills_by_type
        }
    
    @staticmethod
    def find_job_analysis_by_id(db: Session, job_id: int) -> Optional[JobAnalysis]:
        """
        Find job analysis by job ID
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            JobAnalysis instance or None
        """
        return db.query(JobAnalysis).filter(JobAnalysis.job_id == job_id).first()
    
    @staticmethod
    def get_job_analyses(
        db: Session,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[JobAnalysis], int]:
        """
        Get paginated job analyses with filters
        
        Args:
            db: Database session
            keyword: Filter by keyword
            city: Filter by city
            month: Filter by month
            year: Filter by year
            limit: Result limit
            offset: Pagination offset
            
        Returns:
            Tuple of (analyses list, total count)
        """
        query = db.query(JobAnalysis)
        
        # Apply filters
        filters = []
        if keyword:
            filters.append(JobAnalysis.keyword == keyword)
        if city:
            filters.append(JobAnalysis.location == city)
        if month:
            filters.append(extract('month', JobAnalysis.posted_date) == month)
        if year:
            filters.append(extract('year', JobAnalysis.posted_date) == year)
        
        if filters:
            query = query.filter(and_(*filters))
        
        total = query.count()
        results = query.order_by(
            JobAnalysis.extracted_at.desc()
        ).offset(offset).limit(limit).all()
        
        return results, total
