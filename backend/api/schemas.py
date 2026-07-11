from pydantic import BaseModel
from typing import List, Optional

# ============================================================================
# RESPONSE MODELS & REQUEST SCHEMAS
# ============================================================================

class SkillCount(BaseModel):
    id: int
    skill_name: str
    skill_type: str
    count: int
    percentage: Optional[float] = None

class SkillTrendByMonth(BaseModel):
    month: str  # Format: "2024-01"
    tech_stack_count: int
    soft_skill_count: int
    total_count: int

class SkillDistribution(BaseModel):
    skill_type: str
    count: int
    percentage: float
    top_skills: List[dict]  # [{name, count}, ...]

class TrendData(BaseModel):
    month: int
    year: int
    skill_name: str
    skill_type: str
    count: int

class JobInfo(BaseModel):
    id: int
    job_title: str
    company: str
    location: str
    keyword: str
    posted_date: str
    created_at: Optional[str] = ""
    source: str

class Statistics(BaseModel):
    total_jobs: int
    total_skills: int
    unique_skills: int
    processed_jobs: int
    skills_by_type: dict

class KeywordOption(BaseModel):
    id: int
    keyword: str

class CityOption(BaseModel):
    city: str
    count: int

class CompanyOption(BaseModel):
    company: str
    count: int

class EmployeeSizeOption(BaseModel):
    employee_size: str
    count: int

class FilterOptions(BaseModel):
    keywords: List[KeywordOption]
    cities: List[CityOption]
    companies: List[CompanyOption]
    employee_sizes: List[EmployeeSizeOption]
    months: List[int]
    years: List[int]
    skill_types: List[str]
    last_extraction_at: Optional[str] = None

class JobAnalysisData(BaseModel):
    id: int
    job_title: str
    company: str
    location: Optional[str]
    posted_date: Optional[str]
    link: str
    keyword: str
    tech_stack: Optional[str]
    soft_skill: Optional[str]
    extracted_at: str
    ai_model: Optional[str]

class EmployeeSizeResponse(BaseModel):
    size: str
    count: int


# ============================================================================
# SKILL MATCHER & CO-OCCURRENCE SCHEMAS
# ============================================================================

class SkillMatcherRequest(BaseModel):
    targetJobTitle: str
    userSkills: List[str]
    # Nilai: "all" | "tech_stack" | "technical_skill" | "soft_skill"
    skillType: Optional[str] = "all"
    employeeSize: Optional[str] = None

class SkillDetail(BaseModel):
    name: str
    demand: int
    demandPct: float
    contribution: float

class SkillMatcherResponse(BaseModel):
    matchScore: int
    matchedSkills: List[str]
    missingSkills: List[str]
    matchedDetails: Optional[List[SkillDetail]] = None
    missingDetails: Optional[List[SkillDetail]] = None
    totalJobsAnalyzed: Optional[int] = None

class CooccurrenceLink(BaseModel):
    source: str
    target: str
    weight: int

class CooccurrenceNode(BaseModel):
    id: str
    frequency: int

class CooccurrenceResponse(BaseModel):
    nodes: List[CooccurrenceNode]
    links: List[CooccurrenceLink]


# ============================================================================
# COMPANY INSIGHTS SCHEMAS
# ============================================================================

class CompanyInfo(BaseModel):
    rank: int
    company: str
    company_linkedin_url: Optional[str] = None
    job_count: int
    percentage: float

class TopCompaniesResponse(BaseModel):
    skill_name: str
    total_jobs_with_skill: int
    companies: List[CompanyInfo]
