"""
Admin Utilities Module
Provides helper classes and utilities for admin API operations.
"""

from datetime import datetime
from typing import Optional, Callable, List
import io
import json


class OutputCapture:
    """
    Captures stdout/stderr output line by line with timestamps.
    
    Useful for streaming real-time process output to frontend.
    Applies callback for each line for WebSocket or streaming responses.
    """
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Initialize output capture
        
        Args:
            callback: Optional function called for each captured line
        """
        self.lines: List[str] = []
        self.callback = callback
    
    def write(self, message: str) -> None:
        """
        Write and capture output message
        
        Args:
            message: Output message to capture
        """
        if not message or message == '\n':
            return
        
        # Add timestamp to message
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message.strip()}"
        
        # Store line
        self.lines.append(line)
        
        # Call callback if provided
        if self.callback:
            self.callback(line)
    
    def flush(self) -> None:
        """Flush output buffer (no-op for in-memory capture)"""
        pass
    
    def get_lines(self) -> List[str]:
        """Get all captured lines"""
        return self.lines.copy()
    
    def get_text(self) -> str:
        """Get all captured lines as single text"""
        return "\n".join(self.lines)
    
    def clear(self) -> None:
        """Clear all captured lines"""
        self.lines.clear()


class AdminState:
    """
    Manages admin process state (scraping, extracting, etc.)
    
    Encapsulates state tracking to follow SRP principle.
    """
    
    def __init__(self):
        """Initialize admin state"""
        self.is_scraping = False
        self.is_extracting = False
        self.current_process: Optional[str] = None
        self.last_output: List[str] = []
        self.scrape_monitor = None
        self.extract_monitor = None

    def __getitem__(self, key: str):
        """Backward-compatible dict-style access for existing admin code."""
        if key == "scraping":
            return self.is_scraping
        if key == "extracting":
            return self.is_extracting
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self, key: str, value) -> None:
        """Backward-compatible dict-style mutation for existing admin code."""
        if key == "scraping":
            self.is_scraping = bool(value)
            return
        if key == "extracting":
            self.is_extracting = bool(value)
            return
        if hasattr(self, key):
            setattr(self, key, value)
            return
        raise KeyError(key)
    
    def start_scraping(self) -> None:
        """Mark scraping as started"""
        self.is_scraping = True
        self.current_process = "scraping"
        self.last_output.clear()
    
    def stop_scraping(self) -> None:
        """Mark scraping as stopped"""
        self.is_scraping = False
        if self.current_process == "scraping":
            self.current_process = None
    
    def start_extracting(self) -> None:
        """Mark extracting as started"""
        self.is_extracting = True
        self.current_process = "extracting"
        self.last_output.clear()
    
    def stop_extracting(self) -> None:
        """Mark extracting as stopped"""
        self.is_extracting = False
        if self.current_process == "extracting":
            self.current_process = None
    
    def is_busy(self) -> bool:
        """Check if any process is running"""
        return self.is_scraping or self.is_extracting
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            "is_scraping": self.is_scraping,
            "is_extracting": self.is_extracting,
            "current_process": self.current_process,
            "is_busy": self.is_busy(),
        }


class KeywordValidator:
    """Validates keyword operations"""
    
    MIN_KEYWORD_LENGTH = 1
    MAX_KEYWORD_LENGTH = 100
    
    @staticmethod
    def validate_keyword(keyword: str) -> None:
        """
        Validate keyword format
        
        Args:
            keyword: Keyword to validate
            
        Raises:
            ValueError: If keyword is invalid
        """
        if not keyword or not keyword.strip():
            raise ValueError("Keyword cannot be empty")
        
        keyword_clean = keyword.strip()
        
        if len(keyword_clean) < KeywordValidator.MIN_KEYWORD_LENGTH:
            raise ValueError(f"Keyword too short (min: {KeywordValidator.MIN_KEYWORD_LENGTH})")
        
        if len(keyword_clean) > KeywordValidator.MAX_KEYWORD_LENGTH:
            raise ValueError(f"Keyword too long (max: {KeywordValidator.MAX_KEYWORD_LENGTH})")
    
    @staticmethod
    def normalize_keyword(keyword: str) -> str:
        """
        Normalize keyword (trim whitespace)
        
        Args:
            keyword: Raw keyword
            
        Returns:
            Normalized keyword
        """
        return keyword.strip()
