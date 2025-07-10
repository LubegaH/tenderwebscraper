"""
Utility functions for the SHA Website Crawler.
Focused on tender monitoring and business opportunity discovery.
"""
import logging
import re
import urllib.parse
from typing import List
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


def create_cache_key(url: str, buzzwords: List[str]) -> str:
    """Create a unique cache key for URL and buzzwords combination."""
    return f"{url}:{','.join(sorted(buzzwords))}"


def extract_domain(url: str) -> str:
    """Extract domain from URL for robots.txt checking."""
    try:
        parsed_url = urllib.parse.urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
    except Exception as e:
        logger.warning(f"Failed to parse domain from {url}: {e}")
        return url


def find_buzzwords_in_text(text: str, buzzwords: List[str]) -> List[str]:
    """
    Find buzzwords in text using case-insensitive word boundary matching.
    Optimized for tender and business opportunity keywords.
    """
    if not text or not buzzwords:
        return []
    
    found_words = []
    for word in buzzwords:
        if word and re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
            found_words.append(word)
    
    return found_words


def check_robots_txt(url: str, user_agent: str = "SHA-WebCrawler") -> bool:
    """
    Check if URL can be crawled according to robots.txt.
    Returns True if crawling is allowed or if robots.txt check fails.
    """
    try:
        domain = extract_domain(url)
        
        rp = RobotFileParser()
        rp.set_url(f"{domain}/robots.txt")
        rp.read()
        
        return rp.can_fetch(user_agent, url)
        
    except Exception as e:
        logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
        # Default to allowing if robots.txt check fails
        return True


def validate_url_list(urls: List[str]) -> List[str]:
    """Validate and clean a list of URLs."""
    if not urls:
        return []
    
    valid_urls = []
    for url in urls:
        if isinstance(url, str):
            cleaned_url = url.strip()
            if cleaned_url:
                valid_urls.append(cleaned_url)
    
    return valid_urls


def validate_buzzwords_list(buzzwords: List[str]) -> List[str]:
    """Validate and clean a list of buzzwords."""
    if not buzzwords:
        return []
    
    valid_words = []
    for word in buzzwords:
        if isinstance(word, str):
            cleaned_word = word.strip()
            if cleaned_word:
                valid_words.append(cleaned_word)
    
    return valid_words


def get_user_friendly_error(error_code: str, error_message: str = None) -> str:
    """Convert error codes to user-friendly messages for tender monitoring context."""
    error_messages = {
        'VALIDATION_ERROR': 'Invalid input - please check your URLs and buzzwords',
        'NETWORK_ERROR': 'Unable to reach website - check URL or try again later',
        'ROBOTS_BLOCKED': 'Website blocks crawling - access denied by robots.txt',
        'TIMEOUT_ERROR': 'Request timed out - website may be slow or unavailable',
        'RATE_LIMIT_ERROR': 'Too many requests - please wait before trying again',
        'CRAWLER_ERROR': 'Processing error - please try again or contact support'
    }
    
    user_message = error_messages.get(error_code, 'Unknown error occurred')
    
    if error_message:
        return f"{user_message}: {error_message}"
    
    return user_message


def log_crawl_summary(results: List[dict]) -> None:
    """Log a summary of crawl results for monitoring and debugging."""
    if not results:
        logger.info("No crawl results to summarize")
        return
    
    total = len(results)
    successful = len([r for r in results if not r.get('error')])
    failed = total - successful
    with_buzzwords = len([r for r in results if r.get('found') and len(r['found']) > 0])
    
    logger.info(f"Crawl summary: {total} URLs processed, {successful} successful, "
                f"{failed} failed, {with_buzzwords} found buzzwords")
    
    # Log error breakdown for debugging
    if failed > 0:
        error_counts = {}
        for result in results:
            error_code = result.get('error_code')
            if error_code:
                error_counts[error_code] = error_counts.get(error_code, 0) + 1
        
        error_summary = ', '.join([f"{code}: {count}" for code, count in error_counts.items()])
        logger.info(f"Error breakdown: {error_summary}")