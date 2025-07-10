"""
SHA Website Crawler - Tender Monitoring Module

A specialized web crawler for business opportunity and tender discovery.
Optimized for production deployment with comprehensive error handling,
resource management, and modular architecture.

Usage:
    from crawler import SHAWebCrawler
    
    with SHAWebCrawler() as crawler:
        results = crawler.crawl_urls(urls, buzzwords)
"""

from .core import SHAWebCrawler
from .models import (
    CrawlRequest,
    CrawlResult,
    CrawlerError,
    ValidationError,
    NetworkError,
    RobotsTxtError,
    TimeoutError,
    RateLimitError
)
from .utils import (
    create_cache_key,
    extract_domain,
    find_buzzwords_in_text,
    check_robots_txt,
    validate_url_list,
    validate_buzzwords_list,
    get_user_friendly_error,
    log_crawl_summary
)

__version__ = "1.0.0"
__author__ = "SHA Website Crawler Team"
__description__ = "Tender monitoring and business opportunity discovery crawler"

# Export main classes and functions
__all__ = [
    # Core crawler
    'SHAWebCrawler',
    
    # Data models
    'CrawlRequest',
    'CrawlResult',
    
    # Exceptions
    'CrawlerError',
    'ValidationError', 
    'NetworkError',
    'RobotsTxtError',
    'TimeoutError',
    'RateLimitError',
    
    # Utilities
    'create_cache_key',
    'extract_domain',
    'find_buzzwords_in_text',
    'check_robots_txt',
    'validate_url_list',
    'validate_buzzwords_list',
    'get_user_friendly_error',
    'log_crawl_summary'
]