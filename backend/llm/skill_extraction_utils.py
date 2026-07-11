"""
Skill Extraction Utilities Module
Provides helper functions for skill extraction, retry logic, and JSON parsing.
Applies SRP (Single Responsibility Principle) by separating concerns.
"""

import json
import time
import re
from typing import Dict, Optional, Tuple, List


class RetryConfig:
    """Configuration for retry logic - encapsulates retry parameters"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: int = 30,
        multiplier: float = 3.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.multiplier = multiplier
    
    def calculate_delay(self, attempt: int) -> int:
        """Calculate retry delay based on attempt number (exponential backoff)"""
        return int(self.base_delay * (self.multiplier ** attempt))


class JSONResponseParser:
    """Handles parsing and cleaning JSON responses from LLM"""
    
    @staticmethod
    def extract_json_from_response(response_text: str) -> Optional[str]:
        """
        Extract valid JSON string from LLM response
        Handles markdown code blocks and extra text
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Cleaned JSON string or None if invalid
        """
        if not response_text:
            return None
        
        # Remove markdown code blocks
        cleaned = JSONResponseParser._remove_markdown_blocks(response_text)
        
        # Extract JSON object
        json_text = JSONResponseParser._find_json_object(cleaned)
        
        return json_text if json_text else None
    
    @staticmethod
    def _remove_markdown_blocks(text: str) -> str:
        """Remove markdown code block markers"""
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()
    
    @staticmethod
    def _find_json_object(text: str) -> Optional[str]:
        """Find and extract JSON object from text"""
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start == -1 or json_end == -1 or json_end <= json_start:
            return None
        
        return text[json_start:json_end + 1]
    
    @staticmethod
    def parse_skill_extraction_response(json_text: str) -> Optional[Dict]:
        """
        Parse JSON response into skill categories
        
        Args:
            json_text: JSON string from LLM
            
        Returns:
            Dict with tech_stack, technical_skill, soft_skill lists, or None if invalid
        """
        try:
            parsed = json.loads(json_text)
            
            return {
                "tech_stack": parsed.get("tech_stack", []) or [],
                "technical_skill": parsed.get("technical_skill", []) or [],
                "soft_skill": parsed.get("soft_skill", []) or []
            }
        except (json.JSONDecodeError, ValueError):
            return None
    
    @staticmethod
    def parse_batch_response(json_text: str, job_ids: List[int]) -> Dict[int, Dict]:
        """
        Parse batch extraction response
        
        Args:
            json_text: JSON string from LLM
            job_ids: List of job IDs in batch
            
        Returns:
            Dict mapping job_id to skills
        """
        empty_result = {job_id: {"tech_stack": [], "technical_skill": [], "soft_skill": []} 
                       for job_id in job_ids}
        
        try:
            payload = json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            return empty_result
        
        if not isinstance(payload, dict):
            return empty_result
        
        result = {}
        for job_id in job_ids:
            item = payload.get(str(job_id))
            
            if not isinstance(item, dict):
                result[job_id] = {"tech_stack": [], "technical_skill": [], "soft_skill": []}
                continue
            
            result[job_id] = {
                "tech_stack": item.get("tech_stack", []) or [],
                "technical_skill": item.get("technical_skill", []) or [],
                "soft_skill": item.get("soft_skill", []) or []
            }
        
        return result


class ErrorClassifier:
    """Classifies errors to determine appropriate retry strategy"""
    
    @staticmethod
    def is_rate_limit_error(error: Exception) -> bool:
        """Check if error is rate limit related"""
        error_msg = str(error).lower()
        rate_limit_indicators = ["429", "rate_limit", "too many requests", "quota"]
        return any(indicator in error_msg for indicator in rate_limit_indicators)
    
    @staticmethod
    def is_timeout_error(error: Exception) -> bool:
        """Check if error is timeout related"""
        return isinstance(error, TimeoutError) or "timeout" in str(error).lower()
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """Determine if error warrants a retry"""
        return ErrorClassifier.is_rate_limit_error(error) or ErrorClassifier.is_timeout_error(error)


class SkillExtractionResult:
    """
    Encapsulates skill extraction result
    Applies value object pattern for clean data handling
    """
    
    EMPTY_RESULT = {
        "tech_stack": [],
        "technical_skill": [],
        "soft_skill": []
    }
    
    def __init__(self, skills: Optional[Dict] = None):
        self.skills = skills or self.EMPTY_RESULT.copy()
    
    @staticmethod
    def empty() -> "SkillExtractionResult":
        """Create empty result"""
        return SkillExtractionResult()
    
    def is_empty(self) -> bool:
        """Check if all skill categories are empty"""
        return all(
            not self.skills.get(key, [])
            for key in ["tech_stack", "technical_skill", "soft_skill"]
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.skills.copy()


def validate_job_description(job_description: str, min_length: int = 50) -> bool:
    """
    Validate job description is suitable for processing
    
    Args:
        job_description: Text to validate
        min_length: Minimum required length
        
    Returns:
        True if valid, False otherwise
    """
    return bool(job_description and len(job_description) >= min_length)


def log_retry_attempt(attempt: int, max_retries: int, delay: int, reason: str) -> None:
    """
    Log retry attempt information
    
    Args:
        attempt: Current attempt number (0-based)
        max_retries: Total retry attempts
        delay: Delay before next attempt (seconds)
        reason: Reason for retry
    """
    print(f"    [{reason}] Attempt {attempt + 1}/{max_retries}, "
          f"waiting {delay} seconds...")
