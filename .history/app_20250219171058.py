import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

app = Flask(__name__)

def parse_keywords(buzzwords):
    # Parse keywords for AND/OR
    if 'AND' in buzzwords:
        keywords = [word.strip() for word in buzzwords.split('AND')]
        operator = 'AND'
    elif 'OR' in buzzwords:
        keywords = [word.strip() for word in buzzwords.split('OR')]
        operator = 'OR'
    else:
        keywords = [buzzwords]
        operator = 'OR'
    return keywords, operator

# Function to scrape the URL and filter by keywords and date
def scrape_url(url, buzzwords, start_date=None, end_date=None):
    keywords, operator = parse_keywords(buzzwords)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ')

            # Attempt to find the date using multiple selectors
            date_selectors = [
                {'tag': 'span', 'class': 'date'},
                {'tag': 'div', 'class': 'tender-date'},
                {'tag': 'p', 'class': 'posted-date'}
            ]

            pub_date = None
            for selector in date_selectors:
                date_element = soup.find(selector['tag'], class_=selector['class'])
                if date_element:
                    date_text = date_element.text.strip()
                    pub_date = parse_date(date_text)
                    if pub_date:
                        break

            # Logging the start and end dates provided by the user
            logging.debug(f"Start Date: {start_date}, End Date: {end_date}")

            # If no date is found or cannot be parsed, skip date filtering
            if pub_date:
                # Convert input date strings to datetime objects for comparison
                if start_date and pub_date < datetime.strptime(start_date, '%Y-%m-%d'):
                    return {'url': url, 'error': 'Date is outside the specified range'}
                if end_date and pub_date > datetime.strptime(end_date, '%Y-%m-%d'):
                    return {'url': url, 'error': 'Date is outside the specified range'}

            # Keyword filtering (same as before)
            if operator == 'AND':
                found_words = [word for word in keywords if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)]
                if len(found_words) == len(keywords):  # All keywords must be found
                    return {'url': url, 'found': found_words}
            else:  # OR search
                found_words = [word for word in keywords if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)]
                if found_words:  # Any keyword can be found
                    return {'url': url, 'found': found_words}

            return {'url': url, 'found': []}  # No keywords found
        else:
            return {'url': url, 'error': 'Unable to fetch the page.'}
    except requests.RequestException as e:
        return {'url': url, 'error': str(e)}

def parse_date(date_text):
    """Try parsing date with multiple formats to support dynamic date formats."""
    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%B %d, %Y']  # Add formats as needed
    for fmt in date_formats:
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            continue
    return None  # Return None if no format matches

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.get_json()
    urls = data.get('urls', [])
    buzzwords = data.get('buzzwords', "")
    start_date = data.get('startDate', None)
    end_date = data.get('endDate', None)

    results = []
    for url in urls:
        result = scrape_url(url, buzzwords, start_date, end_date)
        results.append(result)
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # app.run(debug=False, host='0.0.0.0', port=port)
    app.run(debug=True, port=port)
    


# # app.py - Backend using Flask
# import os
# from flask import Flask, render_template, request, jsonify
# import requests
# from bs4 import BeautifulSoup
# import re

# app = Flask(__name__)

# # Function to scrape the URL and look for buzzwords
# def scrape_url(url, buzzwords):
#     try:
#         response = requests.get(url, timeout=10)  # Added timeout to avoid long waits on unresponsive servers
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
#             text = soup.get_text(separator=' ')
#             found_words = [word for word in buzzwords if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)]
#             if found_words:
#                 return {'url': url, 'found': found_words}
#             else:
#                 return {'url': url, 'found': []}  # No buzzwords found
#         else:
#             return {'url': url, 'error': 'Unable to fetch the page.'}
#     except requests.RequestException as e:
#         return {'url': url, 'error': f"Error: {str(e)}"}

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/crawl', methods=['POST'])
# def crawl():
#     data = request.get_json()
#     urls = data.get('urls', [])
#     buzzwords = data.get('buzzwords', [])
    
#     # Ensure buzzwords are in a list format
#     if isinstance(buzzwords, str):
#         buzzwords = [word.strip() for word in buzzwords.split(',')]
    
#     results = []
#     for url in urls:
#         result = scrape_url(url, buzzwords)
#         results.append(result)
#     return jsonify(results)

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     # app.run(debug=False, host='0.0.0.0', port=port)
#     app.run(debug=True, port=port)

