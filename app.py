"""
Flask application for SHA Website Crawler - Tender Monitoring System

A specialized web application for business opportunity and tender discovery.
Clean, modular architecture with comprehensive error handling.
"""
import os
import logging
from flask import Flask, render_template, request, jsonify

# Import our modular crawler
from crawler import SHAWebCrawler, ValidationError, CrawlerError

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler('crawler.log'), 
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response


@app.route('/')
def index():
    """Serve the main tender monitoring interface."""
    return render_template('index.html')


@app.route('/crawl', methods=['POST'])
def crawl():
    """Process crawl request with comprehensive error handling for tender monitoring."""
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                'error': 'Invalid content type - JSON required',
                'error_code': 'VALIDATION_ERROR'
            }), 400

        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({
                'error': 'Invalid JSON format in request',
                'error_code': 'VALIDATION_ERROR'
            }), 400
            
        if not data:
            return jsonify({
                'error': 'No JSON data provided in request',
                'error_code': 'VALIDATION_ERROR'
            }), 400

        urls = data.get('urls', [])
        buzzwords = data.get('buzzwords', [])

        # Input validation with specific error messages
        if not urls:
            return jsonify({
                'error': 'URLs list is required and cannot be empty',
                'error_code': 'VALIDATION_ERROR'
            }), 400
            
        if not buzzwords:
            return jsonify({
                'error': 'Buzzwords list is required and cannot be empty',
                'error_code': 'VALIDATION_ERROR'
            }), 400
            
        if not isinstance(urls, list):
            return jsonify({
                'error': 'URLs must be provided as a list',
                'error_code': 'VALIDATION_ERROR'
            }), 400
            
        if not isinstance(buzzwords, list):
            return jsonify({
                'error': 'Buzzwords must be provided as a list',
                'error_code': 'VALIDATION_ERROR'
            }), 400

        # Check URL limits (important for Render.com memory constraints)
        if len(urls) > 30:
            return jsonify({
                'error': f'Maximum 30 URLs allowed, received {len(urls)}',
                'error_code': 'VALIDATION_ERROR'
            }), 400

        # Process and validate buzzwords
        buzzwords = [word.strip() for word in buzzwords if isinstance(word, str) and word.strip()]
        if not buzzwords:
            return jsonify({
                'error': 'No valid buzzwords provided after filtering',
                'error_code': 'VALIDATION_ERROR'
            }), 400

        # Log request for debugging and monitoring
        logger.info(f"Processing tender crawl request: {len(urls)} URLs, {len(buzzwords)} buzzwords")
        
        # Use modular crawler with context manager for proper resource cleanup
        with SHAWebCrawler(
            max_workers=3,  # Optimized for Render.com
            queue_size=50,
            request_timeout=15,
            max_retries=2
        ) as crawler:
            results = crawler.crawl_urls(urls, buzzwords)
            
            # Log results summary for monitoring
            successful = len([r for r in results if not r.get('error')])
            failed = len(results) - successful
            with_opportunities = len([r for r in results if r.get('found') and len(r['found']) > 0])
            
            logger.info(f"Tender crawl completed: {successful} successful, {failed} failed, "
                       f"{with_opportunities} potential opportunities found")
            
            return jsonify(results)

    except ValidationError as e:
        logger.warning(f"Validation error in crawl endpoint: {e.message}")
        return jsonify({
            'error': e.message,
            'error_code': e.error_code
        }), 400
        
    except CrawlerError as e:
        logger.error(f"Crawler error in crawl endpoint: {e.message}")
        return jsonify({
            'error': e.message,
            'error_code': e.error_code
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in crawl endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error - please try again later',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'service': 'SHA Website Crawler - Tender Monitoring',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Check if we're in development mode
    if os.environ.get('FLASK_ENV') == 'development':
        logger.info("Starting development server for tender monitoring")
        app.run(debug=True, port=port)
    else:
        # Use appropriate production server based on platform
        import platform
        if platform.system() == 'Windows':
            from waitress import serve
            logger.info(f"Starting Windows production server on port {port}")
            serve(app, host='0.0.0.0', port=port)
        else:
            import subprocess
            logger.info(f"Starting Linux production server with gunicorn on port {port}")
            subprocess.run([
                'gunicorn',
                '--config=gunicorn_config.py',
                '-b', f'0.0.0.0:{port}',
                'app:app'
            ])