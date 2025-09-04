"""
Flask server for web search fallback service
This will be deployed to Railway
"""

import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Your Serper API key (will be set as environment variable in Railway)
SERPER_API_KEY = os.environ.get('SERPER_API_KEY', 'a03b827c8ecd74cdde702867ed4bd7b9efd6a72e')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "websearch"})

@app.route('/websearch', methods=['POST'])
def web_search():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        query = data.get('query', '').strip()
        num_results = data.get('num_results', 5)
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        web_results = search_with_serper(query, num_results)
        
        response = {
            "query": query,
            "results": web_results,
            "count": len(web_results),
            "source": "web_search"
        }

        return jsonify(response)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def search_with_serper(query: str, num_results: int = 5):
    if not SERPER_API_KEY:
        return []
    
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": min(num_results, 10)}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        web_results = []
        
        for result in data.get("organic", []):
            web_results.append({
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "url": result.get("link", ""),
                "displayUrl": result.get("displayLink", "")
            })
        
        return web_results
        
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        return []

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)