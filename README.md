**SHA Website Crawler**
A powerful web crawler that searches websites for specified buzzwords, built with Python Flask and modern JavaScript.

**Features**
- Multi-URL Crawling: Process multiple URLs simultaneously
- Buzzword Detection: Search for specific keywords across websites
- Robots.txt Compliance: Respects website crawling policies
- Rate Limiting: Prevents overloading target servers
- Concurrent Processing: Uses thread pools for efficient crawling
- Real-time Progress Tracking: Visual feedback during crawling operations
- Comprehensive Results: Detailed statistics and findings display

**Installation**
**Prerequisites**
- Python 3.7+
- pip (Python package manager)

**Setup**
- Clone the repository:


```git clone https://github.com/yourusername/sha-website-crawler.git```

```cd sha-website-crawler```

**2. Create a virtual environment (recommended):**


```python -m venv venv```

```source venv/bin/activate  # On Windows: venv\Scripts\activate```

**3. Install dependencies:**

```pip install -r requirements.txt```



**Usage**
1. Start the application:

```python app.py```


2. Open your browser and navigate to:

```http://localhost:5000```

3. Enter URLs (one per line) and buzzwords (comma-separated) in the form.

4. Click "Crawl" to start the process.

5. View real-time progress and results.

**Configuration**
You can modify the following parameters in  ```app.py```:


- max_workers: Number of concurrent crawling threads (default: 10)
- queue_size: Maximum queue size for pending requests (default: 1000)
- request_timeout: HTTP request timeout in seconds (default: 30)
- max_retries: Maximum number of retry attempts (default: 3)

For production deployment, set ```debug=False``` and consider using a WSGI server like Gunicorn:

```python
if __name__ == '__main__':
 port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
```


    


**Project Structure**

```python
sha-website-crawler/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── static/
│   └── styles.css         # CSS styles
├── templates/
│   └── index.html         # HTML template
└── crawler.log            # Log file
```


**Dependencies**
- Flask: Web framework
- Requests: HTTP client
- BeautifulSoup4: HTML parsing
- Backoff: Retry mechanism
- Cachetools: Caching utilities
- Ratelimit: Rate limiting
- Validators: URL validation

**Security Features**

- Content Security Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection


**License**
MIT License

**Contributing**

1. Fork the repository
2. Create your feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add some amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

**Acknowledgements**

- [Flask Documentation](https://flask.palletsprojects.com/en/stable/)
- [BeautifulSoup Documentation](https://pypi.org/project/beautifulsoup4/)
- [Requests Documentation](https://requests.readthedocs.io/en/latest/)
