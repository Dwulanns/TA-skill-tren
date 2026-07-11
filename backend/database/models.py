"""
Database models - Clean relational structure
Normalized schema with proper relationships for filtering
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

# ==========================================================
# BASE DEFINITION
# ==========================================================
Base = declarative_base()

# ==========================================================
# TIMEZONE CONFIG
# ==========================================================
WIB = timezone(timedelta(hours=7))


def get_wib_now():
    """Get current time in WIB timezone"""
    return datetime.now(WIB).replace(tzinfo=None)


# ==========================================================
# KEYWORD
# ==========================================================
class Keyword(Base):
    """Keywords used for job scraping"""

    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=get_wib_now)

    jobs = relationship("Job", back_populates="keyword")

    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"


# ==========================================================
# JOB
# ==========================================================
class Job(Base):
    """Job postings from scraping"""

    __tablename__ = "jobs"

    __table_args__ = (
        Index("idx_posted_date", "posted_date"),
        Index("idx_location", "location"),
        Index("idx_company_linkedin_url", "company_linkedin_url"),
        Index("idx_employee_size", "employee_size"),
        UniqueConstraint("link", name="uq_job_link"),
    )

    id = Column(Integer, primary_key=True, index=True)

    keyword_id = Column(
        Integer,
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), index=True)

    posted_date = Column(Date, index=True)

    source = Column(String(50), default="linkedin", index=True)

    link = Column(String(500), unique=True, nullable=False)

    job_description = Column(Text)

    status_ekstraksi = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime, default=get_wib_now)

    company_linkedin_url = Column(
        String(1000),
        nullable=True,
        index=True,
    )

    employee_size = Column(
        String(100),
        nullable=True,
        index=True,
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================
    keyword = relationship("Keyword", back_populates="jobs")

    job_skills = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    analysis = relationship(
        "JobAnalysis",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Job(id={self.id}, "
            f"title='{self.job_title}', "
            f"company='{self.company}')>"
        )


# ==========================================================
# COMPANY ENRICHMENT
# ==========================================================
class CompanyEnrichment(Base):
    """Enriched company profile data"""

    __tablename__ = "company_enrichment"

    __table_args__ = (
        UniqueConstraint(
            "company_name",
            name="uq_company_enrichment_name",
        ),
        Index(
            "idx_company_enrichment_name",
            "company_name",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(
        String(255),
        nullable=False,
    )

    company_linkedin_url = Column(
        String(1000),
        nullable=True,
        index=True,
    )

    employee_size = Column(
        String(100),
        nullable=True,
    )

    linkedin_slug = Column(
        String(255),
        nullable=True,
        index=True,
    )

    source = Column(
        String(50),
        default="linkedin_enrichment",
        index=True,
    )

    created_at = Column(
        DateTime,
        default=get_wib_now,
    )

    updated_at = Column(
        DateTime,
        default=get_wib_now,
        onupdate=get_wib_now,
    )

    def __repr__(self):
        return (
            f"<CompanyEnrichment("
            f"id={self.id}, "
            f"company_name='{self.company_name}', "
            f"employee_size='{self.employee_size}')>"
        )


# ==========================================================
# SKILL TYPE
# ==========================================================
class SkillType(Base):
    """Types/categories of skills"""

    __tablename__ = "skill_types"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description = Column(String(255))

    created_at = Column(
        DateTime,
        default=get_wib_now,
    )

    skills = relationship(
        "Skill",
        back_populates="skill_type",
    )

    def __repr__(self):
        return (
            f"<SkillType("
            f"id={self.id}, "
            f"name='{self.name}')>"
        )


# ==========================================================
# SKILL
# ==========================================================
class Skill(Base):
    """Master list of unique skills"""

    __tablename__ = "skills"

    __table_args__ = (
        UniqueConstraint(
            "normalized_name",
            "skill_type_id",
            name="uq_skill_normalized",
        ),
        Index(
            "idx_normalized_name",
            "normalized_name",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    skill_type_id = Column(
        Integer,
        ForeignKey(
            "skill_types.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(String(100), nullable=False)

    normalized_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=get_wib_now,
    )

    skill_type = relationship(
        "SkillType",
        back_populates="skills",
    )

    job_skills = relationship(
        "JobSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        skill_type = (
            self.skill_type.name
            if self.skill_type
            else "N/A"
        )

        return (
            f"<Skill("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type='{skill_type}')>"
        )


# ==========================================================
# JOB SKILL
# ==========================================================
class JobSkill(Base):
    """Pivot table connecting jobs and skills"""

    __tablename__ = "job_skills"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "skill_id",
            name="uq_job_skill",
        ),
        Index(
            "idx_job_skill",
            "job_id",
            "skill_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(
        Integer,
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    skill_id = Column(
        Integer,
        ForeignKey(
            "skills.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=get_wib_now,
    )

    job = relationship(
        "Job",
        back_populates="job_skills",
    )

    skill = relationship(
        "Skill",
        back_populates="job_skills",
    )

    def __repr__(self):
        return (
            f"<JobSkill("
            f"job_id={self.job_id}, "
            f"skill_id={self.skill_id})>"
        )


# ==========================================================
# JOB ANALYSIS
# ==========================================================
class JobAnalysis(Base):
    """AI extraction results"""

    __tablename__ = "job_analysis"

    __table_args__ = (
        Index("idx_analysis_keyword", "keyword"),
        Index("idx_analysis_location", "location"),
        Index("idx_analysis_posted_date", "posted_date"),
    )

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    posted_date = Column(Date)
    link = Column(String(500), nullable=False)
    job_description = Column(Text)
    keyword = Column(String(100), nullable=False)

    tech_stack = Column(Text)
    technical_skill = Column(Text)
    soft_skill = Column(Text)

    extracted_at = Column(
        DateTime,
        default=get_wib_now,
    )

    ai_model = Column(String(100))

    job = relationship(
        "Job",
        back_populates="analysis",
    )

    def __repr__(self):
        return (
            f"<JobAnalysis("
            f"id={self.id}, "
            f"job_id={self.job_id}, "
            f"title='{self.job_title}')>"
        )


# ==========================================================
# ADMIN
# ==========================================================
class Admin(Base):
    """Admin users for panel access"""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    is_active = Column(
        Integer,
        default=1,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=get_wib_now,
    )

    last_login = Column(
        DateTime,
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<Admin("
            f"id={self.id}, "
            f"email='{self.email}', "
            f"username='{self.username}')>"
        )