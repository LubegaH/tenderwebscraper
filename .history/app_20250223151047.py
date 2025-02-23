
# app.py - Backend using Flask
import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time
import logging
import urllib.parse
from typing import List, Dict, Any
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
    response.headers['Content-Security-Policy'] = "default-src 'self"
    return response

# Cache configuration
url_cache = TTLCache(maxsize=100, ttl=3600)
robots_cache = TTLCache(maxsize=100, ttl=3600)

@dataclass
class CrawlResult:
    url: str
    found: List[str]
    error: str = None

class WebCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHA-WebCrawler/1.0 (+https://example.com/bot)'
        })
        self.executor = ThreadPoolExecutor(max_workers=5)
    # Handles making HTTP requests with rate limiting
    @sleep_and_retry
    @limits(calls=10, period=60) # Rate limit: 10 requests per minute
    def fetch_url(self, url: str) -> requests.Response:
        return self.session.get(url, timeout=10)
    
    # Check if a URL can be crawled according to the site's robots.txt file
    # 
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

# Function to scrape the URL and look for buzzwords
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

crawler = WebCrawler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.get_json()
    urls = data.get('urls', [])
    buzzwords = data.get('buzzwords', [])
    
    # Ensure buzzwords are in a list format
    if isinstance(buzzwords, str):
        buzzwords = [word.strip() for word in buzzwords.split(',')]
    
    results = []
    for url in urls:
        result = scrape_url(url, buzzwords)
        results.append(result)
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
    # app.run(debug=True, port=port)

