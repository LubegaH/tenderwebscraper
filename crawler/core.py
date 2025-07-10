"""
Core crawler implementation for SHA Website Crawler.
Optimized for tender monitoring and business opportunity discovery.
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from threading import Lock
from typing import List, Dict, Any

import backoff
import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache
from ratelimit import limits, sleep_and_retry
from validators import url as validate_url

from .models import CrawlRequest, CrawlResult, NetworkError, ValidationError
from .utils import (
    create_cache_key, extract_domain, find_buzzwords_in_text, 
    check_robots_txt, log_crawl_summary
)

logger = logging.getLogger(__name__)


class SHAWebCrawler:
    """
    Web crawler optimized for tender monitoring and business opportunity discovery.
    
    Features:
    - Concurrent processing with proper resource management
    - Robots.txt compliance and rate limiting
    - Comprehensive error handling and retry logic
    - Memory-efficient caching with TTL
    - Production-ready for Render.com deployment
    """
    
    def __init__(
            self,
            max_workers: int = 3,  # Optimized for Render.com
            queue_size: int = 50,  # Reduced for memory efficiency
            request_timeout: int = 15,  # Faster timeouts
            max_retries: int = 2):  # Efficient retry strategy
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHA-WebCrawler/1.0 (+https://example.com/bot)'
        })

        # Thread pool and queue configuration
        self.max_workers = max_workers
        self.executor = None  # Will be created in context manager
        self.request_queue = Queue(maxsize=queue_size)
        self.result_queue = Queue()

        # Configuration
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        # Caches and locks with size limits for memory management
        self.url_cache = TTLCache(maxsize=200, ttl=1800)  # 30 min cache
        self.robots_cache = TTLCache(maxsize=50, ttl=1800)
        self.domain_locks = {}
        self.domain_locks_lock = Lock()
        self._closed = False

    def __enter__(self):
        """Context manager entry - initialize thread pool."""
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()

    def cleanup(self):
        """Cleanup all resources to prevent memory leaks."""
        if self._closed:
            return
            
        self._closed = True
        
        # Shutdown thread pool executor
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
            
        # Close HTTP session
        if self.session:
            self.session.close()
            
        # Clear caches to free memory
        self.url_cache.clear()
        self.robots_cache.clear()
        
        # Clear domain locks
        with self.domain_locks_lock:
            self.domain_locks.clear()

    def get_domain_lock(self, domain: str) -> Lock:
        """Get or create a lock for a specific domain."""
        with self.domain_locks_lock:
            if domain not in self.domain_locks:
                self.domain_locks[domain] = Lock()
            return self.domain_locks[domain]
    
    @backoff.on_exception(
            backoff.expo,
            (requests.exceptions.RequestException, TimeoutError),
            max_tries=3,
            max_time=30
    )
    @sleep_and_retry
    @limits(calls=10, period=60)  # Rate limit: 10 requests per minute
    def fetch_url(self, url: str) -> requests.Response:
        """Fetch URL with rate limiting and exponential backoff."""
        return self.session.get(url, timeout=self.request_timeout)
    
    def check_robots_txt(self, url: str) -> bool:
        """Check if URL can be crawled according to robots.txt with caching."""
        try:
            domain = extract_domain(url)

            with self.get_domain_lock(domain):
                if domain in self.robots_cache:
                    return self.robots_cache[domain].can_fetch("SHA-WebCrawler", url)
                
                # Use utility function for robots.txt checking
                can_fetch = check_robots_txt(url, "SHA-WebCrawler")
                
                # Cache the result (store the RobotFileParser if needed for detailed checking)
                # For now, we'll cache a simple boolean result
                class SimpleRobotResult:
                    def __init__(self, result):
                        self.result = result
                    def can_fetch(self, user_agent, url):
                        return self.result
                
                self.robots_cache[domain] = SimpleRobotResult(can_fetch)
                return can_fetch

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True  # Default to allowing if robots.txt check fails

    def process_request(self, request: CrawlRequest) -> CrawlResult:
        """Process a single crawl request with comprehensive error handling."""
        try:
            # URL validation
            if not validate_url(request.url):
                return CrawlResult(
                    url=request.url,
                    found=[],
                    error="Invalid URL format - must be a valid HTTP/HTTPS URL",
                    error_code="VALIDATION_ERROR"
                )

            # Check cache
            cache_key = create_cache_key(request.url, request.buzzwords)
            if cache_key in self.url_cache:
                cached_result = self.url_cache[cache_key]
                logger.info(f"Cache hit for {request.url}")
                return cached_result

            # Check robots.txt
            if not self.check_robots_txt(request.url):
                return CrawlResult(
                    url=request.url,
                    found=[],
                    error="Access denied by robots.txt - site disallows crawling",
                    error_code="ROBOTS_BLOCKED"
                )

            # Fetch and parse content
            response = self.fetch_url(request.url)
            response.raise_for_status()
            
            # Validate response content
            if not response.text:
                return CrawlResult(
                    url=request.url,
                    found=[],
                    error="Empty response content",
                    error_code="NETWORK_ERROR",
                    status_code=response.status_code
                )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ')
            
            # Find buzzwords using utility function
            found_words = find_buzzwords_in_text(text, request.buzzwords)
            
            result = CrawlResult(
                url=request.url,
                found=found_words,
                status_code=response.status_code,
                retry_count=request.retries
            )
            
            # Cache successful results
            self.url_cache[cache_key] = result
            logger.info(f"Successfully processed {request.url} - found {len(found_words)} buzzwords")
            return result

        except requests.exceptions.Timeout as e:
            if request.retries < request.max_retries:
                request.retries += 1
                logger.warning(f"Timeout for {request.url}, retrying ({request.retries}/{request.max_retries})")
                return self.process_request(request)
            return CrawlResult(
                url=request.url,
                found=[],
                error=f"Request timeout after {request.max_retries} retries",
                error_code="TIMEOUT_ERROR",
                retry_count=request.retries
            )
        
        except requests.exceptions.ConnectionError as e:
            if request.retries < request.max_retries:
                request.retries += 1
                logger.warning(f"Connection error for {request.url}, retrying ({request.retries}/{request.max_retries})")
                return self.process_request(request)
            return CrawlResult(
                url=request.url,
                found=[],
                error=f"Connection failed - unable to reach server",
                error_code="NETWORK_ERROR",
                retry_count=request.retries
            )
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            if status_code == 403:
                error_msg = "Access forbidden - server denied request"
            elif status_code == 404:
                error_msg = "Page not found"
            elif status_code == 429:
                error_msg = "Rate limit exceeded"
            elif status_code and status_code >= 500:
                error_msg = "Server error - try again later"
            else:
                error_msg = f"HTTP error {status_code}"
                
            return CrawlResult(
                url=request.url,
                found=[],
                error=error_msg,
                error_code="NETWORK_ERROR",
                status_code=status_code,
                retry_count=request.retries
            )
        
        except requests.RequestException as e:
            if request.retries < request.max_retries:
                request.retries += 1
                logger.warning(f"Request error for {request.url}, retrying ({request.retries}/{request.max_retries})")
                return self.process_request(request)
            return CrawlResult(
                url=request.url,
                found=[],
                error=f"Network request failed: {str(e)[:100]}",
                error_code="NETWORK_ERROR",
                retry_count=request.retries
            )
        
        except Exception as e:
            logger.error(f"Unexpected error processing {request.url}: {str(e)}")
            return CrawlResult(
                url=request.url,
                found=[],
                error=f"Processing failed: {str(e)[:100]}",
                error_code="CRAWLER_ERROR",
                retry_count=request.retries
            )

    def crawl_urls(self, urls: List[str], buzzwords: List[str]) -> List[Dict[str, Any]]:
        """Crawl multiple URLs concurrently with improved handling."""
        if self._closed:
            raise RuntimeError("Crawler has been closed")
            
        # Limit the number of URLs to process at once (optimized for Render.com)
        max_urls = min(len(urls), 15)
        urls = urls[:max_urls]
        
        # Ensure executor is available
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Submit all requests to the queue
        for url in urls:
            request = CrawlRequest(
                url=url.strip(),
                buzzwords=buzzwords,
                max_retries=self.max_retries,
                timeout=self.request_timeout
            )
            self.request_queue.put(request)

        # Process requests concurrently
        futures = []
        results = []
        
        try:
            # Submit tasks to thread pool
            while not self.request_queue.empty():
                try:
                    request = self.request_queue.get(block=False)
                    future = self.executor.submit(self.process_request, request)
                    futures.append(future)
                except Empty:
                    break

            # Collect results as they complete
            for future in as_completed(futures, timeout=180):  # 3-minute total timeout
                try:
                    result = future.result()
                    results.append({
                        'url': result.url,
                        'found': result.found,
                        'error': result.error,
                        'error_code': result.error_code,
                        'status_code': result.status_code,
                        'retries': result.retry_count
                    })
                except TimeoutError:
                    results.append({
                        'url': 'unknown',
                        'found': [],
                        'error': 'Request timed out - processing took too long',
                        'error_code': 'TIMEOUT_ERROR',
                        'status_code': None,
                        'retries': 0
                    })
                except Exception as e:
                    logger.error(f"Future processing error: {str(e)}")
                    results.append({
                        'url': 'unknown',
                        'found': [],
                        'error': f"Processing error: {str(e)[:100]}",
                        'error_code': 'CRAWLER_ERROR',
                        'status_code': None,
                        'retries': 0
                    })

        finally:
            # Clean up futures to prevent resource leaks
            for future in futures:
                if not future.done():
                    future.cancel()

        # Log summary for monitoring
        log_crawl_summary(results)
        
        return results