#!/usr/bin/env python3
"""
Unit tests for LinkedIn URL extraction and validation.

Run with:
    pytest backend/tests/test_linkedin_url_extraction.py -v
    pytest backend/tests/test_linkedin_url_extraction.py::test_* -v

"""

import pytest
from scraper.company.linkedin_url_extractor import (
    LinkedInCompanyURLExtractor,
    extract_linkedin_company_url_enhanced,
)
from scraper.company.company_url_validator import (
    CompanyURLValidator,
    validate_company_url,
)


# ============================================================================
# Test fixtures
# ============================================================================

HTML_WITH_COMPANY_LINK = """
<html>
<body>
    <div class="job-header">
        <h1>Data Engineer</h1>
        <a href="https://www.linkedin.com/company/shopee/">Shopee</a>
        <span>Singapore</span>
    </div>
</body>
</html>
"""

HTML_WITHOUT_COMPANY_LINK = """
<html>
<body>
    <div class="job-header">
        <h1>Software Engineer</h1>
        <span>Company Name Hidden</span>
    </div>
</body>
</html>
"""

HTML_WITH_RELATIVE_COMPANY_LINK = """
<html>
<body>
    <a href="/company/google/">Google</a>
</body>
</html>
"""

HTML_WITH_ENCODED_COMPANY_LINK = """
<html>
<body>
    <a href="https://www.linkedin.com/company/shopee-indonesia?lipi=abc123">Shopee Indonesia</a>
</body>
</html>
"""

HTML_WITH_JSONLD = """
<html>
<body>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "hiringOrganization": {
            "@type": "Organization",
            "name": "IBM",
            "url": "https://www.linkedin.com/company/ibm/"
        }
    }
    </script>
</body>
</html>
"""


# ============================================================================
# Test extraction
# ============================================================================

class TestLinkedInCompanyURLExtractor:
    """Test LinkedInCompanyURLExtractor."""
    
    def test_extract_direct_link(self):
        """Test extraction of direct company link."""
        extractor = LinkedInCompanyURLExtractor(HTML_WITH_COMPANY_LINK)
        result = extractor.extract()
        
        assert result.url == "https://www.linkedin.com/company/shopee/"
        assert result.strategy == "direct_link"
        assert result.confidence > 0.9
    
    def test_extract_relative_link(self):
        """Test extraction of relative company link."""
        extractor = LinkedInCompanyURLExtractor(HTML_WITH_RELATIVE_COMPANY_LINK)
        result = extractor.extract()
        
        assert result.url == "https://www.linkedin.com/company/google/"
        assert result.strategy == "direct_link"
    
    def test_extract_encoded_link(self):
        """Test extraction of URL-encoded company link."""
        extractor = LinkedInCompanyURLExtractor(HTML_WITH_ENCODED_COMPANY_LINK)
        result = extractor.extract()
        
        # Should extract slug correctly even with query params
        assert result.url == "https://www.linkedin.com/company/shopee/"
        assert result.strategy == "direct_link"
    
    def test_extract_from_jsonld(self):
        """Test extraction from JSON-LD structured data."""
        extractor = LinkedInCompanyURLExtractor(HTML_WITH_JSONLD)
        result = extractor.extract()
        
        assert result.url == "https://www.linkedin.com/company/ibm/"
        assert result.strategy == "structured_data"
    
    def test_extract_no_url(self):
        """Test extraction when no company URL present."""
        extractor = LinkedInCompanyURLExtractor(HTML_WITHOUT_COMPANY_LINK)
        result = extractor.extract()
        
        assert result.url is None
        assert result.confidence < 0.5
    
    def test_canonicalize_url(self):
        """Test URL canonicalization."""
        test_cases = [
            ("https://www.linkedin.com/company/shopee/", "https://www.linkedin.com/company/shopee/"),
            ("https://linkedin.com/company/shopee", "https://www.linkedin.com/company/shopee/"),
            ("/company/shopee/", "https://www.linkedin.com/company/shopee/"),
            ("https://www.linkedin.com/company/shopee?lipi=abc", "https://www.linkedin.com/company/shopee/"),
            ("//linkedin.com/company/google/", "https://www.linkedin.com/company/google/"),
        ]
        
        for input_url, expected in test_cases:
            result = LinkedInCompanyURLExtractor._canonicalize_url(input_url)
            assert result == expected, f"Failed for {input_url}"
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = extract_linkedin_company_url_enhanced(HTML_WITH_COMPANY_LINK)
        assert result == "https://www.linkedin.com/company/shopee/"


# ============================================================================
# Test validation
# ============================================================================

class TestCompanyURLValidator:
    """Test CompanyURLValidator."""
    
    def test_slug_matches_company_name_exact(self):
        """Test slug matching with exact company name."""
        slug = "google"
        company_name = "Google Inc"
        
        assert CompanyURLValidator._slug_matches_company_name(slug, company_name)
    
    def test_slug_matches_company_name_partial(self):
        """Test slug matching with partial company name."""
        slug = "shopee"
        company_name = "Shopee Indonesia"
        
        assert CompanyURLValidator._slug_matches_company_name(slug, company_name)
    
    def test_slug_matches_company_name_hyphenated(self):
        """Test slug matching with hyphenated slug."""
        slug = "microsoft-azure"
        company_name = "Microsoft Azure"
        
        assert CompanyURLValidator._slug_matches_company_name(slug, company_name)
    
    def test_slug_doesnt_match(self):
        """Test slug matching with non-matching slug."""
        slug = "xyz-random"
        company_name = "Google Inc"
        
        assert not CompanyURLValidator._slug_matches_company_name(slug, company_name)
    
    def test_validate_fast(self):
        """Test fast validation."""
        validator = CompanyURLValidator()
        
        url = "https://www.linkedin.com/company/shopee/"
        company_name = "Shopee Indonesia"
        
        assert validator.validate_fast(url, company_name)
    
    def test_validate_fast_fails_on_bad_slug(self):
        """Test fast validation fails on bad slug."""
        validator = CompanyURLValidator()
        
        url = "https://www.linkedin.com/company/xyz-random/"
        company_name = "Google Inc"
        
        assert not validator.validate_fast(url, company_name)
    
    def test_validate_company_url_function(self):
        """Test convenience validation function."""
        url = "https://www.linkedin.com/company/shopee/"
        company_name = "Shopee Indonesia"
        
        result = validate_company_url(url, company_name, fast_only=True)
        
        assert result.is_valid
        assert result.method == "fast"
    
    def test_normalize_text(self):
        """Test text normalization."""
        test_cases = [
            ("Google Inc.", "google inc."),
            ("  SHOPEE   Indonesia  ", "shopee   indonesia"),
            ("Microsoft-Azure", "microsoft-azure"),
        ]
        
        for input_text, expected in test_cases:
            result = CompanyURLValidator._normalize_text(input_text)
            assert result == expected, f"Failed for {input_text}"


# ============================================================================
# Integration tests
# ============================================================================

class TestIntegration:
    """Integration tests combining extraction and validation."""
    
    def test_extract_and_validate(self):
        """Test full flow: extract URL then validate."""
        # Extract
        extractor = LinkedInCompanyURLExtractor(HTML_WITH_COMPANY_LINK)
        extracted = extractor.extract()
        
        assert extracted.url is not None
        
        # Validate
        validator = CompanyURLValidator()
        is_valid = validator.validate_fast(extracted.url, "Shopee Indonesia")
        
        assert is_valid
    
    def test_extraction_strategies_priority(self):
        """Test that direct links are preferred over structured data."""
        # This HTML has both direct link and JSON-LD
        html = HTML_WITH_COMPANY_LINK + """
        <script type="application/ld+json">
        {
            "hiringOrganization": {
                "url": "https://www.linkedin.com/company/ibm/"
            }
        }
        </script>
        """
        
        extractor = LinkedInCompanyURLExtractor(html)
        result = extractor.extract()
        
        # Should prefer direct link (higher confidence)
        assert result.url == "https://www.linkedin.com/company/shopee/"
        assert result.strategy == "direct_link"


# ============================================================================
# Edge cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_html(self):
        """Test with empty HTML."""
        extractor = LinkedInCompanyURLExtractor("")
        result = extractor.extract()
        
        assert result.url is None
    
    def test_malformed_jsonld(self):
        """Test with malformed JSON-LD."""
        html = """
        <script type="application/ld+json">
        {invalid json
        </script>
        """
        
        extractor = LinkedInCompanyURLExtractor(html)
        result = extractor.extract()
        
        # Should not crash
        assert result is not None
    
    def test_multiple_company_links(self):
        """Test with multiple company links."""
        html = """
        <a href="/company/google/">Google</a>
        <a href="/company/shopee/">Shopee</a>
        """
        
        extractor = LinkedInCompanyURLExtractor(html)
        result = extractor.extract()
        
        # Should extract first one
        assert result.url == "https://www.linkedin.com/company/google/"
    
    def test_special_characters_in_url(self):
        """Test with special characters in URL."""
        html = """
        <a href="/company/company-name-with-dashes/">Company Name</a>
        """
        
        extractor = LinkedInCompanyURLExtractor(html)
        result = extractor.extract()
        
        assert result.url == "https://www.linkedin.com/company/company-name-with-dashes/"


# ============================================================================
# Performance
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""
    
    def test_extraction_speed(self):
        """Test that extraction is reasonably fast."""
        import time
        
        extractor = LinkedInCompanyURLExtractor(HTML_WITH_COMPANY_LINK)
        
        start = time.time()
        for _ in range(100):
            extractor.extract()
        elapsed = time.time() - start
        
        # Should extract 100 URLs in < 1 second
        assert elapsed < 1.0, f"Extraction too slow: {elapsed:.2f}s for 100 items"
    
    def test_validation_speed(self):
        """Test that fast validation is reasonably fast."""
        import time
        
        validator = CompanyURLValidator()
        url = "https://www.linkedin.com/company/shopee/"
        company_name = "Shopee Indonesia"
        
        start = time.time()
        for _ in range(1000):
            validator.validate_fast(url, company_name)
        elapsed = time.time() - start
        
        # Should validate 1000 URLs in < 0.5 seconds
        assert elapsed < 0.5, f"Validation too slow: {elapsed:.3f}s for 1000 items"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
