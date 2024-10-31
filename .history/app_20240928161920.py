# app.py - Backend using Flask
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Function to scrape the URL and look for buzzwords
def scrape_url(url, buzzwords):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ')
            found_words = []
            for word in buzzwords:
                if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                    found_words.append(word)
            return {'url': url, 'found': found_words}
        else:
            return {'url': url, 'error': 'Unable to fetch the page.'}
    except requests.RequestException as e:
        return {'url': url, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    # urls = request.form.getlist('urls')
    # buzzwords = request.form.get('buzzwords').split(',')
    data = request.get_json()
    urls = data.get('urls', [])
    buzzwords = data.get('buzzwords', '').split(',')
    results = []
    for url in urls:
        result = scrape_url(url, [word.strip() for word in buzzwords])
        results.append(result)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)