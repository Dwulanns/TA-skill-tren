"""
Admin API Pydantic Models and Schemas

Defines request/response schemas for admin endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================================
# KEYWORD OPERATIONS
# ============================================================================

class KeywordRequest(BaseModel):
    """Request body for keyword creation/update"""
    keyword: str = Field(..., min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "Python Developer"
            }
        }


class KeywordResponse(BaseModel):
    """Response body for keyword operations"""
    id: int
    keyword: str


class KeywordListResponse(BaseModel):
    """Response for keyword list"""
    keywords: List[KeywordResponse]


# ============================================================================
# SCRAPING OPERATIONS
# ============================================================================

class ScrapeRequest(BaseModel):
    """Request body for scraping operation"""
    keyword_ids: Optional[List[int]] = Field(
        None,
        description="Specific keyword IDs to scrape. If None, scrapes all keywords."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword_ids": [1, 2, 3]
            }
        }


class ScrapeStatusResponse(BaseModel):
    """Response for scrape status"""
    status: str  # "idle", "scraping", "completed", "error"
    message: str
    progress: Optional[dict] = None


# ============================================================================
# EXTRACTION OPERATIONS
# ============================================================================

class ExtractionStatusResponse(BaseModel):
    """Response for extraction status"""
    status: str  # "idle", "extracting", "completed", "error"
    message: str
    processed: int
    total: int


# ============================================================================
# DATABASE STATISTICS
# ============================================================================

class DatabaseStatsResponse(BaseModel):
    """Response for database statistics"""
    total_keywords: int
    total_jobs: int
    total_skills: int
    total_job_skills: int
    total_skill_types: int


# ============================================================================
# COMMON RESPONSE MODELS
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    status: str = "success"
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
