
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



# Initialize Flask app with security headers
app = Flask(__name__)

# Function to scrape the URL and look for buzzwords
def scrape_url(url, buzzwords):
    try:
        response = requests.get(url, timeout=10)  # Added timeout to avoid long waits on unresponsive servers
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ')
            found_words = [word for word in buzzwords if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)]
            if found_words:
                return {'url': url, 'found': found_words}
            else:
                return {'url': url, 'found': []}  # No buzzwords found
        else:
            return {'url': url, 'error': 'Unable to fetch the page.'}
    except requests.RequestException as e:
        return {'url': url, 'error': f"Error: {str(e)}"}

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

