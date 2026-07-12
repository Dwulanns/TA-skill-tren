"""
Centralized Constants Module
Contains all magic numbers, strings, and configuration constants used across the application.
Follows the principle: One place for one thing (DRY - Don't Repeat Yourself)
"""

# ============================================================================
# API CONFIGURATION
# ============================================================================
ALLOWED_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3004",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3004",
    "http://127.0.0.1:5173",
    
      # Production
    "https://ta-skill-tren-o4zl.vercel.app",
    "https://ta-skill-tren.vercel.app",
]

CORS_CONFIG = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# ============================================================================
# API DOCUMENTATION
# ============================================================================
API_TITLE = "Job Skills Trend API"
API_DESCRIPTION = "API untuk visualisasi tren kebutuhan kompetensi di bidang Data & AI"
API_VERSION = "2.0.0"

# ============================================================================
# GROQ LLM CONFIGURATION
# ============================================================================
GROQ_DEFAULT_MODEL = "llama-3.1-8b-instant"
GROQ_SYSTEM_PROMPT = "Extract skills from job description and return ONLY valid JSON."

# Retry and timeout settings for LLM
SKILL_EXTRACTION_TIMEOUT = 45  # seconds
SKILL_EXTRACTION_MAX_RETRIES = 3
SKILL_EXTRACTION_BASE_RETRY_DELAY = 30  # seconds
SKILL_EXTRACTION_RETRY_MULTIPLIER = 3

# Temperature and token settings for LLM
SKILL_EXTRACTION_TEMPERATURE = 0.1
SKILL_EXTRACTION_MAX_TOKENS = 800
SKILL_EXTRACTION_TOP_P = 0.9

# Character limit for job description processing
SKILL_CHAR_LIMIT_PER_JOB_DEFAULT = 4000

# ============================================================================
# WEB SCRAPER CONFIGURATION
# ============================================================================
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
SCRAPER_REQUEST_TIMEOUT = 10  # seconds
SCRAPER_RATE_LIMIT_DELAY = 2  # seconds between requests
SCRAPER_RANDOM_DELAY_RANGE = (1, 3)  # seconds, for randomization
SCRAPER_DEFAULT_LOCATION = "Indonesia"
SCRAPER_MAX_JOBS_PER_KEYWORD = 200
SCRAPER_REQUEST_RETRIES = 3

# Skill filtering for Data & AI roles
DATA_AI_KEYWORDS = [
    "data scientist", "data engineer", "data analyst", "data analyst engineer",
    "machine learning", "ml engineer", "ai engineer", "artificial intelligence",
    "deep learning", "big data", "computer vision", "nlp",
    "natural language processing", "business intelligence", "analytics",
    "data mining", "data pipeline", "etl", "data warehouse",
    "data architect", "data specialist", "analytics engineer"
]

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
JWT_ALGORITHM = "HS256"
PASSWORD_HASH_ITERATIONS = 100000

# Authentication error messages
AUTH_ERROR_INVALID_CREDENTIALS = "Invalid email or password"
AUTH_ERROR_INACTIVE_ACCOUNT = "Admin account is inactive"
AUTH_ERROR_EMAIL_EXISTS = "Email already registered"
AUTH_ERROR_USERNAME_EXISTS = "Username already taken"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_DIR = "logs"
LOG_FILE_PATH = f"{LOG_DIR}/app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL_DEFAULT = "INFO"
LOGGER_NAME = "SkillTrend"

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DB_ECHO_SQL = False  # Set to True for debugging SQL queries
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20
DB_POOL_RECYCLE = 3600  # Recycle connections after 1 hour

# Timezone
DB_TIMEZONE_UTC_OFFSET = 7  # WIB (Western Indonesian Time) = UTC+7

# ============================================================================
# SKILL PROCESSING CONFIGURATION
# ============================================================================
SKILL_TYPES = {
    "tech_stack": "Tech Stack",
    "technical_skill": "Technical Skill",
    "soft_skill": "Soft Skill"
}

MIN_JOB_DESCRIPTION_LENGTH = 50  # Minimum characters for processing

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_GROQ_API_KEY_NOT_FOUND = "GROQ_API_KEY tidak ditemukan di .env file"
ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded after retries"
ERROR_MAX_TIMEOUT_REACHED = "Max timeout retries reached"
ERROR_GENERIC_SKILL_EXTRACTION = "Error during skill extraction"

# HTTP Status codes (for reference)
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500

# ============================================================================
# PAGINATION CONFIGURATION
# ============================================================================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# ============================================================================
# OUTPUT FORMATTING
# ============================================================================
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_PROCESSING = "🔄"
EMOJI_DELETE = "🗑️"
EMOJI_CHECK = "✓"
EMOJI_ROCKET = "🚀"
EMOJI_FIRE = "🔥"
