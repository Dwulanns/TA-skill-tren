"""
URL Validation with fast/slow paths.

Fast path: Slug-based validation (no HTTP)
Slow path: Full page fetch + content validation

Designed to be used in both scraper (during extraction) and enricher
(when validating URLs before using them for scraping).
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CompanyURLValidator:
    """
    Two-tier validation for LinkedIn company URLs.
    
    Fast validation (no network):
    - Check if slug format is valid
    - Check if company name tokens appear in slug
    
    Slow validation (with network):
    - Fetch page and check HTTP status
    - Parse page content
    - Verify company name appears on page
    """
    
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    
    BLOCKED_STATUS_CODES = {403, 429, 999}
    
    LIMITED_PAGE_MARKERS = (
        "join linkedin",
        "sign in",
        "security verification",
        "let's do a quick security check",
        "challenge",
        "captcha",
    )
    
    def __init__(self, timeout: int = 15, retries: int = 2):
        """
        Initialize validator.
        
        Args:
            timeout: HTTP request timeout in seconds
            retries: Number of retries for blocked responses
        """
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
    
    def validate_fast(
        self,
        company_url: str,
        company_name: str,
    ) -> bool:
        """
        Fast validation using slug matching (no network).
        
        Args:
            company_url: LinkedIn company URL to validate
            company_name: Company name to match against
        
        Returns:
            True if slug looks plausible for this company
        """
        if not company_url or not company_name:
            return False
        
        # Extract slug from URL
        slug = self._extract_slug(company_url)
        if not slug:
            return False
        
        return self._slug_matches_company_name(slug, company_name)
    
    def validate_slow(
        self,
        company_url: str,
        company_name: str,
    ) -> bool:
        """
        Full validation with network request.
        
        Fetches the company page and checks content.
        
        Args:
            company_url: LinkedIn company URL to validate
            company_name: Company name to match against
        
        Returns:
            True if page loads and contains company name
        """
        if not company_url:
            return False
        
        # First try fast path
        if not self.validate_fast(company_url, company_name):
            return False
        
        # Then fetch page
        response = self._fetch_with_retry(company_url)
        if not response:
            return False
        
        # Check if page is blocked
        if response.status_code in self.BLOCKED_STATUS_CODES:
            # Assume blocked pages are valid if slug matches
            return self.validate_fast(company_url, company_name)
        
        if response.status_code != 200:
            return False
        
        # Parse page content
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = self._normalize_text(soup.get_text(' ', strip=True))
        except Exception as e:
            logger.warning(f"Failed to parse {company_url}: {e}")
            return False
        
        # Check if page looks like a login wall
        if self._is_limited_page(page_text):
            # Assume blocked pages are valid if slug matches
            return self.validate_fast(company_url, company_name)
        
        # Check if company name appears on page
        return self._company_name_on_page(company_name, page_text)
    
    @staticmethod
    def _extract_slug(company_url: str) -> Optional[str]:
        """Extract slug from LinkedIn company URL."""
        if not company_url:
            return None
        
        parsed = urlparse(company_url)
        if not parsed.path.startswith('/company/'):
            return None
        
        slug = parsed.path.rstrip('/').split('/company/')[-1].strip()
        return slug if slug else None
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Decode HTML entities, replace special dashes
        text = text.replace('\u2013', '-').replace('\u2014', '-')
        text = text.replace('\xa0', ' ')
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    @staticmethod
    def _slug_matches_company_name(slug: str, company_name: str) -> bool:
        """Check if slug contains company name tokens."""
        if not slug or not company_name:
            return False
        
        slug_normalized = slug.lower().replace('-', ' ').replace('_', ' ')
        name_normalized = CompanyURLValidator._normalize_text(company_name)
        
        # Extract tokens from company name (skip common suffixes)
        name_tokens = re.split(r'\s+', name_normalized)
        name_tokens = [
            t for t in name_tokens
            if len(t) > 1 and t not in {'inc', 'ltd', 'llc', 'corp', 'corporation', 'co', 'sa', 'gmbh', 'pt'}
        ]
        
        if not name_tokens:
            return True  # Can't reject if we have no tokens
        
        # Check if most tokens appear in slug
        matches = sum(1 for token in name_tokens if token in slug_normalized)
        return matches >= max(1, len(name_tokens) - 1)
    
    @staticmethod
    def _is_limited_page(page_text: str) -> bool:
        """Check if page looks like a blocked/login page."""
        if not page_text:
            return True
        
        normalized = CompanyURLValidator._normalize_text(page_text)
        
        if not normalized or len(normalized) < 120:
            return True
        
        if any(marker in normalized for marker in CompanyURLValidator.LIMITED_PAGE_MARKERS):
            return True
        
        return False
    
    @staticmethod
    def _company_name_on_page(company_name: str, page_text: str) -> bool:
        """Check if company name appears on page."""
        if not company_name or not page_text:
            return False
        
        # Get main tokens from company name
        name_tokens = re.split(r'\s+', CompanyURLValidator._normalize_text(company_name))
        name_tokens = [t for t in name_tokens if len(t) > 2]
        
        if not name_tokens:
            return True  # Can't check if no substantial tokens
        
        # Check if tokens appear in page text
        matches = sum(1 for token in name_tokens if token in page_text)
        return matches >= max(1, len(name_tokens) - 1)
    
    def _fetch_with_retry(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic for blocked responses."""
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                
                # Not blocked, return immediately
                if response.status_code not in self.BLOCKED_STATUS_CODES:
                    return response
                
                # Blocked, retry with backoff
                if attempt < self.retries - 1:
                    import time
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                
                # Last attempt, return anyway
                return response
                
            except requests.RequestException as e:
                logger.debug(f"Request failed for {url}: {e}")
                if attempt < self.retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        return None


class ValidationResult:
    """Result of a validation attempt."""
    
    def __init__(
        self,
        is_valid: bool,
        method: str = "unknown",  # 'fast' or 'slow'
        reason: str = "",
        http_status: Optional[int] = None,
    ):
        self.is_valid = is_valid
        self.method = method
        self.reason = reason
        self.http_status = http_status
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.is_valid}, method={self.method}, reason={self.reason!r})"


def validate_company_url(
    company_url: str,
    company_name: str,
    fast_only: bool = False,
) -> ValidationResult:
    """
    Convenience function for URL validation.
    
    Args:
        company_url: LinkedIn company URL to validate
        company_name: Company name to match against
        fast_only: If True, only do fast validation (no network)
    
    Returns:
        ValidationResult with details
    """
    if not company_url or not company_name:
        return ValidationResult(False, reason="Missing URL or company name")
    
    validator = CompanyURLValidator()
    
    # Try fast path first
    if validator.validate_fast(company_url, company_name):
        if fast_only:
            return ValidationResult(
                True,
                method='fast',
                reason='Slug matches company name'
            )
        
        # Try slow path
        if validator.validate_slow(company_url, company_name):
            return ValidationResult(
                True,
                method='slow',
                reason='Page content matches'
            )
    
    return ValidationResult(
        False,
        method='fast' if fast_only else 'slow',
        reason='Validation failed'
    )
