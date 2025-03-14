
# app.py - Backend using Flask
# from asyncio import Lock, Queue
import os
from queue import Empty
from flask import Flask, render_template, request, jsonify
import requests
import backoff
from bs4 import BeautifulSoup
import re
import time
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed

from cachetools import TTLCache
from ratelimit import limits, sleep_and_retry
from validators import url as validate_url


# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('crawler.log'), logging.StreamHandler()])

logger = logging.getLogger(__name__)

# Initialize Flask app with security headers
app = Flask(__name__)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response


@dataclass
class CrawlRequest:
    url: str
    buzzwords: List[str]
    retries: int = 3
    max_retries: int = 3
    timeout: int = 30

@dataclass
class CrawlResult:
    url: str
    found: List[str]
    error: str = None
    status_code: Optional[int] = None
    retry_count: int = 0

class SHAWebCrawler:
    def __init__(
            self,
            max_workers: int = 10,
            queue_size: int = 1000,
            request_timeout: int = 30,
            max_retries: int = 3):
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHA-WebCrawler/1.0 (+https://example.com/bot)'
        })

        # Thread pool and queue configuration
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.request_queue = Queue(maxsize=queue_size)
        self.result_queue = Queue()

        # Configuration
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        # Caches and locks
        self.url_cache = TTLCache(maxsize=1000, ttl=3600)
        self.robots_cache = TTLCache(maxsize=100, ttl=3600)
        self.domain_locks = {}
        self.domain_locks_lock = Lock()


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

    # Handles making HTTP requests with rate limiting
    @sleep_and_retry
    @limits(calls=10, period=60) # Rate limit: 10 requests per minute
    def fetch_url(self, url: str) -> requests.Response:
        return self.session.get(url, timeout=self.request_timeout)
    
    
    def check_robots_txt(self, url: str) -> bool:
        """Check if URL can be crawled according to robots.txt."""
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            # base_url = f"{parsed_url.scheme}: //{parsed_url.netloc}"

            with self.get_domain_lock(domain):
                if domain in self.robots_cache:
                    return self.robots_cache[domain].can_fetch("SHA-WebCrawler", url)
                rp = RobotFileParser()
                rp.set_url(f"{domain}/robots.txt")
                rp.read()
                self.robots_cache[domain] = rp
                return rp.can_fetch("SHA-WebCrawler", url)

        except Exception as e:
            logging.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True # Defaults to allowing if robots.txt check fails

# Scrapes a single URL, Validates URL, checks cache, respects robots.txt, Returns a CrawlResult object

    def process_request(self, request: CrawlRequest) -> CrawlResult:
        """Process a single crawl request with retries and error handling"""
        try:
            # URL validation
            if not validate_url(request.url):
                return CrawlResult(
                    url=request.url,
                    found=[],
                    error="Invalid URL format"
                )

            # Check cache
            cache_key = f"{request.url}:{','.join(sorted(request.buzzwords))}"
            if cache_key in self.url_cache:
                return self.url_cache[cache_key]

            # Check robots.txt
            if not self.check_robots_txt(request.url):
                return CrawlResult(
                    url=request.url,
                    found=[],
                    error="Access denied by robots.txt"
                )

            # Fetch and parse content
            response = self.fetch_url(request.url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ')
            
            # Find buzzwords (case-insensitive)
            found_words = [
                word for word in request.buzzwords 
                if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)
            ]
            
            result = CrawlResult(
                url=request.url,
                found=found_words,
                status_code=response.status_code,
                retry_count=request.retries
            )
            
            self.url_cache[cache_key] = result
            return result

        except requests.RequestException as e:
            if request.retries < request.max_retries:
                request.retries += 1
                return self.process_request(request)
            return CrawlResult(
                url=request.url,
                found=[],
                error=f"Request failed: {str(e)}",
                retry_count=request.retries
            )
        except Exception as e:
            return CrawlResult(
                url=request.url,
                found=[],
                error=f"Unexpected error: {str(e)}",
                retry_count=request.retries
            )



    def crawl_urls(self, urls: List[str], buzzwords: List[str]) -> List[Dict[str, Any]]:
        """Crawl multiple URLs concurrently with improved handling."""
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
                    request = self.request_queue.get_nowait()
                    future = self.executor.submit(self.process_request, request)
                    futures.append(future)
                except Empty:
                    break

            # Collect results as they complete
            for future in as_completed(futures, timeout=300):  # 5-minute total timeout
                try:
                    result = future.result()
                    results.append({
                        'url': result.url,
                        'found': result.found,
                        'error': result.error,
                        'status_code': result.status_code,
                        'retries': result.retry_count
                    })
                except TimeoutError:
                    results.append({
                        'url': 'unknown',
                        'found': [],
                        'error': 'Request timed out',
                        'status_code': None,
                        'retries': 0
                    })
                except Exception as e:
                    results.append({
                        'url': 'unknown',
                        'found': [],
                        'error': f"Processing error: {str(e)}",
                        'status_code': None,
                        'retries': 0
                    })

        finally:
            # Clean up
            for future in futures:
                future.cancel()

        return results

# Initiallize the crawler
crawler = SHAWebCrawler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        urls = data.get('urls', [])
        buzzwords = data.get('buzzwords', [])

        # Debug logging
        # print("Received URLs:", urls)
        # print("Received buzzwords:", buzzwords)

        # Input validation
        if not urls or not buzzwords:
            return jsonify({'error': 'URLs and buzzwords are required'}), 400
        if len(urls) > 50:
            return jsonify({'error': 'Maximum 50 URLs allowed'}), 400

        # Process buzzwords
        buzzwords = [word.strip() for word in buzzwords if word.strip()]
        
        # Crawl URLs
        results = crawler.crawl_urls(urls, buzzwords)
        return jsonify(results)

    except Exception as e:
        logging.error(f"Error in crawl endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # app.run(debug=False, host='0.0.0.0', port=port)
    app.run(debug=True, port=port)

