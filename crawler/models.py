"""
Data models and exceptions for the SHA Website Crawler.
Optimized for tender monitoring and business opportunity discovery.
"""
from dataclasses import dataclass
from typing import List, Optional


# Custom exceptions for better error handling
class CrawlerError(Exception):
    """Base exception for all crawler-related errors."""
    def __init__(self, message: str, error_code: str = "CRAWLER_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(CrawlerError):
    """Raised when input validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NetworkError(CrawlerError):
    """Raised when network-related errors occur."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message, "NETWORK_ERROR")
        self.status_code = status_code


class RobotsTxtError(CrawlerError):
    """Raised when robots.txt denies access."""
    def __init__(self, message: str):
        super().__init__(message, "ROBOTS_BLOCKED")


class TimeoutError(CrawlerError):
    """Raised when requests timeout."""
    def __init__(self, message: str):
        super().__init__(message, "TIMEOUT_ERROR")


class RateLimitError(CrawlerError):
    """Raised when rate limiting is exceeded."""
    def __init__(self, message: str):
        super().__init__(message, "RATE_LIMIT_ERROR")


@dataclass
class CrawlRequest:
    """Represents a single crawl request with retry configuration."""
    url: str
    buzzwords: List[str]
    retries: int = 0
    max_retries: int = 2
    timeout: int = 15


@dataclass
class CrawlResult:
    """Represents the result of crawling a single URL."""
    url: str
    found: List[str]
    error: str = None
    error_code: str = None
    status_code: Optional[int] = None
    retry_count: int = 0
    
    @property
    def is_success(self) -> bool:
        """Check if the crawl was successful."""
        return self.error is None
    
    @property
    def has_buzzwords(self) -> bool:
        """Check if any buzzwords were found."""
        return len(self.found) > 0