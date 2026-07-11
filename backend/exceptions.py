"""
Custom Exception Classes for SkillTrend Application

Provides specific exception types for different error scenarios.
All exceptions inherit from SkillTrendException for consistent error handling.
"""

# ============================================================================
# BASE EXCEPTION
# ============================================================================

class SkillTrendException(Exception):
    """
    Base exception class for all SkillTrend application errors.
    
    All other exceptions should inherit from this to ensure consistent
    error handling and logging across the application.
    
    Example:
        >>> raise SkillTrendException("Something went wrong")
    """
    pass


# ============================================================================
# DATABASE EXCEPTIONS
# ============================================================================

class DatabaseException(SkillTrendException):
    """
    Raised when database operations fail.
    
    Covers connection issues, query failures, transaction errors, etc.
    
    Example:
        >>> raise DatabaseException("Failed to connect to database")
    """
    pass


class DataNotFoundError(DatabaseException):
    """Raised when requested data is not found in database"""
    pass


class DataIntegrityError(DatabaseException):
    """Raised when database integrity constraints are violated"""
    pass


# ============================================================================
# API EXCEPTIONS
# ============================================================================

class APIException(SkillTrendException):
    """
    Raised when API operations fail.
    
    Covers HTTP errors, invalid requests, etc.
    
    Example:
        >>> raise APIException("Invalid request body")
    """
    pass


class InvalidRequestError(APIException):
    """Raised when API request is invalid"""
    pass


# ============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTIONS
# ============================================================================

class AuthenticationException(SkillTrendException):
    """
    Raised when authentication fails.
    
    Covers invalid credentials, missing tokens, etc.
    
    Example:
        >>> raise AuthenticationException("Invalid credentials")
    """
    pass


class AuthorizationException(SkillTrendException):
    """
    Raised when user lacks required permissions.
    
    Example:
        >>> raise AuthorizationException("Insufficient permissions")
    """
    pass


# ============================================================================
# EXTERNAL SERVICE EXCEPTIONS
# ============================================================================

class GroqAPIException(SkillTrendException):
    """
    Raised when Groq API calls fail.
    
    Covers API connectivity, authentication, and response errors.
    
    Example:
        >>> raise GroqAPIException("Failed to call Groq API")
    """
    pass


class RateLimitException(GroqAPIException):
    """
    Raised when API rate limit is exceeded.
    
    Indicates the caller should retry after appropriate delay.
    
    Example:
        >>> raise RateLimitException("Rate limit exceeded, retry after 30s")
    """
    pass


class TimeoutException(GroqAPIException):
    """Raised when API call times out"""
    pass


# ============================================================================
# DATA VALIDATION EXCEPTIONS
# ============================================================================

class ValidationException(SkillTrendException):
    """
    Raised when data validation fails.
    
    Covers schema validation, format validation, etc.
    
    Example:
        >>> raise ValidationException("Email format is invalid")
    """
    pass


class SchemaValidationError(ValidationException):
    """Raised when data doesn't match expected schema"""
    pass


class FormatValidationError(ValidationException):
    """Raised when data format is invalid"""
    pass


# ============================================================================
# WEB SCRAPING EXCEPTIONS
# ============================================================================

class ScraperException(SkillTrendException):
    """
    Raised when web scraping fails.
    
    Covers network errors, parsing failures, etc.
    
    Example:
        >>> raise ScraperException("Failed to scrape website")
    """
    pass


class NetworkException(ScraperException):
    """Raised when network request fails"""
    pass


class ParsingException(ScraperException):
    """Raised when HTML parsing fails"""
    pass


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================

class ConfigurationException(SkillTrendException):
    """
    Raised when configuration is invalid.
    
    Covers missing env vars, invalid config values, etc.
    
    Example:
        >>> raise ConfigurationException("GROQ_API_KEY not set")
    """
    pass


class MissingConfigError(ConfigurationException):
    """Raised when required configuration is missing"""
    pass


class InvalidConfigError(ConfigurationException):
    """Raised when configuration value is invalid"""
    pass


class SkillNormalizationException(SkillTrendException):
    """Raised when skill normalization fails"""
    pass
