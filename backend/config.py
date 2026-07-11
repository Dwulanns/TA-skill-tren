"""
Application Configuration
Loads settings from .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "8000"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.3"))
GROQ_TOP_P = float(os.getenv("GROQ_TOP_P", "0.9"))

# LLM Retry Configuration
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_BASE_RETRY_DELAY = int(os.getenv("LLM_BASE_RETRY_DELAY", "2"))

# Skill Extraction Settings
SKILL_CHAR_LIMIT_PER_JOB = int(os.getenv("SKILL_CHAR_LIMIT_PER_JOB", "4000"))

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Scraping Configuration
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
MAX_JOBS_PER_SITE = int(os.getenv("MAX_JOBS_PER_SITE", "200"))
RATE_LIMIT_DELAY = int(os.getenv("RATE_LIMIT_DELAY", "2"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
