"""
Enhanced LinkedIn Company URL Extraction with multiple strategies.

Handles various LinkedIn page layouts, link formats, and validation.
Designed to replace/augment the basic extract_linkedin_company_url() helper.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ExtractedURL:
    """Result of URL extraction attempt."""
    url: Optional[str] = None
    strategy: str = "unknown"  # direct_link, structured_data, text_parse, fallback
    confidence: float = 0.0   # 0.0 - 1.0
    source_element: str = ""  # Where this was found (for debugging)
    raw_value: Optional[str] = None  # Original value before canonicalization
    
    def __bool__(self) -> bool:
        """URL is considered extracted if we have a URL and reasonable confidence."""
        return bool(self.url and self.confidence > 0.5)


class LinkedInCompanyURLExtractor:
    """
    Multi-strategy extractor for LinkedIn company URLs from job pages.
    
    Strategies (in priority order):
    1. Direct link scan: find href="/company/..." in page HTML
    2. Structured data: parse JSON-LD metadata (especially for page title)
    3. Text parsing: look for "linkedin.com/company/" in page text
    4. Fallback: use existing helper (for backward compat)
    
    Design:
    - Each strategy returns ExtractedURL with confidence score
    - Higher confidence URLs are preferred
    - All results are canonicalized (https://www.linkedin.com/company/<slug>/)
    """
    
    # LinkedIn company URL patterns
    LINKEDIN_COMPANY_URL_PATTERN = re.compile(
        r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/[\w\-_.%]+',
        re.IGNORECASE
    )
    
    # Patterns to extract company info from metadata
    COMPANY_PATTERNS = [
        re.compile(r'/company/([\w\-_.]+)/?', re.IGNORECASE),
    ]
    
    def __init__(self, page_html: str):
        """
        Initialize extractor with HTML content.
        
        Args:
            page_html: Full HTML of a LinkedIn job posting page
        """
        self.html = page_html
        self.soup = BeautifulSoup(page_html, 'html.parser') if page_html else None
    
    def extract(self) -> ExtractedURL:
        """
        Run all extraction strategies and return best result.
        
        Returns:
            ExtractedURL with highest confidence, or empty ExtractedURL if failed
        """
        results: list[ExtractedURL] = []
        
        # Strategy 1: Direct link scan
        if self.soup:
            direct = self._extract_from_direct_links()
            if direct:
                results.append(direct)
        
        # Strategy 2: Structured data (JSON-LD, OpenGraph, etc)
        if self.soup:
            structured = self._extract_from_structured_data()
            if structured:
                results.append(structured)
        
        # Strategy 3: Text parsing
        if self.html:
            text_result = self._extract_from_text()
            if text_result:
                results.append(text_result)
        
        # Return highest confidence result
        if results:
            best = max(results, key=lambda x: x.confidence)
            if best.confidence > 0.5:
                return best
        
        # Fallback: Return empty result
        return ExtractedURL()
    
    def _extract_from_direct_links(self) -> Optional[ExtractedURL]:
        """
        Strategy 1: Scan HTML for href="/company/..." links.
        
        This is most reliable because it's what's actually clickable on the page.
        """
        if not self.soup:
            return None
        
        # Look for anchor tags with company URL in href
        for link in self.soup.find_all('a', href=True):
            href = link.get('href', '')
            if not href:
                continue
            
            # Try to extract canonical LinkedIn company URL
            canonical = self._canonicalize_url(href)
            if canonical:
                # Extra high confidence for direct links in HTML
                return ExtractedURL(
                    url=canonical,
                    strategy='direct_link',
                    confidence=0.95,
                    source_element=f'<a href="{href}">',
                    raw_value=href,
                )
        
        return None
    
    def _extract_from_structured_data(self) -> Optional[ExtractedURL]:
        """
        Strategy 2: Look for structured data (JSON-LD, OpenGraph meta tags).
        
        Metadata often contains company info in standardized format.
        """
        if not self.soup:
            return None
        
        # Look for JSON-LD data
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '{}')
                url = self._extract_from_jsonld(data)
                if url:
                    return ExtractedURL(
                        url=url,
                        strategy='structured_data',
                        confidence=0.85,
                        source_element='<script type="application/ld+json">',
                        raw_value=url,
                    )
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Look for OpenGraph meta tags
        og_result = self._extract_from_og_tags()
        if og_result:
            return og_result
        
        return None
    
    def _extract_from_jsonld(self, data: dict | list) -> Optional[str]:
        """Extract LinkedIn company URL from JSON-LD structure."""
        if isinstance(data, list):
            for item in data:
                result = self._extract_from_jsonld(item)
                if result:
                    return result
            return None
        
        if not isinstance(data, dict):
            return None
        
        # Look in common LinkedIn schema properties
        for key in ('url', 'hiringOrganization', 'organizer'):
            if key not in data:
                continue
            
            value = data[key]
            if isinstance(value, dict):
                result = self._extract_from_jsonld(value)
                if result:
                    return result
            elif isinstance(value, str):
                canonical = self._canonicalize_url(value)
                if canonical:
                    return canonical
        
        return None
    
    def _extract_from_og_tags(self) -> Optional[ExtractedURL]:
        """Extract from Open Graph meta tags."""
        if not self.soup:
            return None
        
        # OG:URL might have company info
        og_url = self.soup.find('meta', property='og:url')
        if og_url:
            url = og_url.get('content', '')
            canonical = self._canonicalize_url(url)
            if canonical:
                return ExtractedURL(
                    url=canonical,
                    strategy='og_meta',
                    confidence=0.70,
                    source_element='<meta property="og:url">',
                    raw_value=url,
                )
        
        return None
    
    def _extract_from_text(self) -> Optional[ExtractedURL]:
        """
        Strategy 3: Scan page text for LinkedIn company URLs.
        
        Fallback for when links aren't easily parseable.
        """
        # Find all potential LinkedIn company URLs in HTML
        matches = self.LINKEDIN_COMPANY_URL_PATTERN.findall(self.html)
        
        if not matches:
            return None
        
        # Use first match (usually highest on page)
        raw_url = matches[0]
        canonical = self._canonicalize_url(raw_url)
        
        if canonical:
            return ExtractedURL(
                url=canonical,
                strategy='text_parse',
                confidence=0.70,
                source_element='Found in page text',
                raw_value=raw_url,
            )
        
        return None
    
    @staticmethod
    def _canonicalize_url(url: str) -> Optional[str]:
        """
        Normalize LinkedIn company URL to canonical format.
        
        Input variations:
        - https://linkedin.com/company/shopee/
        - //linkedin.com/company/shopee?foo=bar
        - /company/shopee/ (relative)
        - linkedin.com/company/shopee-temp?lipi=abc
        
        Output:
        - https://www.linkedin.com/company/shopee/
        """
        if not url:
            return None
        
        # Decode URL encoding
        decoded = unquote(url)
        
        # Extract /company/ path if present
        match = re.search(
            r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/([\w\-_.]+)',
            decoded,
            re.IGNORECASE
        )
        
        if not match:
            # Try relative path
            if '/company/' in decoded:
                match = re.search(r'/company/([\w\-_.]+)', decoded)
                if match:
                    slug = match.group(1).strip('/?')
                    if slug:
                        return f"https://www.linkedin.com/company/{slug}/"
            return None
        
        slug = match.group(1).strip('/?')
        if not slug:
            return None
        
        # Canonical format: always www + https + trailing slash
        return f"https://www.linkedin.com/company/{slug}/"
    
    @staticmethod
    def extract_company_slug(company_url: str) -> Optional[str]:
        """Extract slug from LinkedIn company URL."""
        if not company_url:
            return None
        
        parsed = urlparse(company_url)
        if not parsed.path.startswith('/company/'):
            return None
        
        slug = parsed.path.rstrip('/').split('/company/')[-1].strip()
        return slug if slug else None


def extract_linkedin_company_url_enhanced(html_content: str) -> Optional[str]:
    """
    Convenience function for backward compatibility.
    
    Usage:
        url = extract_linkedin_company_url_enhanced(page_html)
    
    Args:
        html_content: HTML of LinkedIn job posting page
    
    Returns:
        Canonical LinkedIn company URL or None
    """
    if not html_content:
        return None
    
    extractor = LinkedInCompanyURLExtractor(html_content)
    result = extractor.extract()
    return result.url if result else None


# Keep old function for compatibility but mark as deprecated
def extract_linkedin_company_url_legacy(url: str) -> Optional[str]:
    """
    Legacy extraction from raw URL string.
    
    DEPRECATED: Use LinkedInCompanyURLExtractor on full HTML instead.
    This was old code that only looked at a single URL, not page context.
    """
    if not url:
        return None
    
    decoded_url = unquote(url)
    match = re.search(
        r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/[\w\-_/%.]+",
        decoded_url,
        re.I
    )
    
    if not match:
        return None
    
    parsed = urlparse(match.group(0))
    path = parsed.path.rstrip("/")
    if not path.startswith("/company/"):
        return None
    
    return f"https://www.linkedin.com{path}/"
