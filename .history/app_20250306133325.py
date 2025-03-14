
# app.py - Backend using Flask
from asyncio import Queue
import os
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

# Cache configuration
url_cache = TTLCache(maxsize=100, ttl=3600)
robots_cache = TTLCache(maxsize=100, ttl=3600)

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


    # Handles making HTTP requests with rate limiting
    @sleep_and_retry
    @limits(calls=10, period=60) # Rate limit: 10 requests per minute
    def fetch_url(self, url: str) -> requests.Response:
        return self.session.get(url, timeout=10)
    
    # Check if a URL can be crawled according to the site's robots.txt file
    # Includes caching of robots.txt results
    def check_robots_txt(self, url: str) -> bool:
        try:
            parsed_url = urllib.parse.urlparse(url)
            base_url = f"{parsed_url.scheme}: //{parsed_url.netloc}"

            if base_url in robots_cache:
                rp = robots_cache[base_url]
            else:
                rp = RobotFileParser()
                rp.set_url(f"{base_url}/robots.txt")
                rp.read()
                robots_cache[base_url] = rp

            return rp.can_fetch("SHA-WebCrawler", url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True # Defaults to allowing if robots.txt check fails

# Scrapes a single URL, Validates URL, checks cache, respects robots.txt, Returns a CrawlResult object
    def scrape_url(self, url: str, buzzwords: List[str]) -> CrawlResult:
            try:
                # Validate URL
                if not validate_url(url):
                    return CrawlResult(url=url, found=[], error="Invalid URL format")

                # Check cache
                cache_key = f"{url}:{','.join(sorted(buzzwords))}"
                if cache_key in url_cache:
                    return url_cache[cache_key]

                # Check robots.txt
                if not self.check_robots_txt(url):
                    return CrawlResult(url=url, found=[], error="Access denied by robots.txt")

                # Fetch and parse content
                response = self.fetch_url(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text(separator=' ')
                
                # Find buzzwords (case-insensitive)
                found_words = [
                    word for word in buzzwords 
                    if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)
                ]
                
                result = CrawlResult(url=url, found=found_words)
                url_cache[cache_key] = result
                return result

            except requests.RequestException as e:
                logger.error(f"Request error for {url}: {str(e)}")
                return CrawlResult(url=url, found=[], error=f"Request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {str(e)}")
                return CrawlResult(url=url, found=[], error=f"Unexpected error: {str(e)}")

    # Manages concurrent scraping of multiple URLs
    def crawl_urls(self, urls: List[str], buzzwords: List[str]) -> List[Dict[str, Any]]:
        futures = []
        for url in urls:
            futures.append(
                self.executor.submit(self.scrape_url, url.strip(), buzzwords)
            )
        
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append({
                    'url': result.url,
                    'found': result.found,
                    'error': result.error
                })
            except Exception as e:
                logger.error(f"Error processing future: {str(e)}")
                results.append({
                    'url': 'unknown',
                    'found': [],
                    'error': f"Processing error: {str(e)}"
                })
        
        return results

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
        print("Received URLs:", urls)
        print("Received buzzwords:", buzzwords)

        # Input validation
        if not urls or not buzzwords:
            return jsonify({'error': 'URLs and buzzwords are required'}), 400

        # Process buzzwords
        buzzwords = [word.strip() for word in buzzwords if word.strip()]
        
        # Crawl URLs
        results = crawler.crawl_urls(urls, buzzwords)
        return jsonify(results)

    except Exception as e:
        print("Error in crawl endpoint:", str(e))  # Debug logging
        return jsonify({'error': 'Internal server error'}), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # app.run(debug=False, host='0.0.0.0', port=port)
    app.run(debug=True, port=port)

