import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image 
import io
from semantic_search import AnimeImageSearch

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the search engine
searcher = AnimeImageSearch()

# Configure image directories
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
THUMBNAILS_DIR = os.path.join(os.path.dirname(__file__), "thumbnails")

# Create thumbnails directory if it doesn't exist
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """Create a thumbnail for an image if it doesn't exist"""
    if not os.path.exists(thumbnail_path):
        with Image.open(image_path) as img:
            img.thumbnail(size)
            img.save(thumbnail_path, "JPEG")

@app.route('/search/text', methods=['POST'])
def text_search():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        # Get optional parameters with defaults
        top_k = data.get('top_k', 5)
        threshold = data.get('threshold', 0.0)

        # Perform text search
        results = searcher.search(data['query'], top_k=top_k, threshold=threshold)
        
        # Format results
        formatted_results = []
        for result in results:
            # Create thumbnail if it doesn't exist
            image_id = result['image_id']
            image_path = os.path.join(IMAGES_DIR, f"{image_id}.jpg")
            thumbnail_path = os.path.join(THUMBNAILS_DIR, f"{image_id}.jpg")
            
            if os.path.exists(image_path):
                create_thumbnail(image_path, thumbnail_path)
                
            formatted_results.append({
                'name': result['jikan_data']['name'] if result.get('jikan_data') else result['character_name'],
                'score': result['similarity_score'],
                'id': f"{image_id}.jpg",
                'jikan_data': result.get('jikan_data')
            })

        return jsonify({'results': formatted_results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search/image', methods=['POST'])
def image_search():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get optional parameters with defaults
        top_k = int(request.form.get('top_k', 5))
        threshold = float(request.form.get('threshold', 0.0))

        # Read and process the image
        image_bytes = file.read()
        results = searcher.search_by_image(image_bytes, top_k=top_k, threshold=threshold)
        
        # Format results
        formatted_results = []
        for result in results:
            image_id = result['image_id']
            image_path = os.path.join(IMAGES_DIR, f"{image_id}.jpg")
            thumbnail_path = os.path.join(THUMBNAILS_DIR, f"{image_id}.jpg")
            
            if os.path.exists(image_path):
                create_thumbnail(image_path, thumbnail_path)
                
            formatted_results.append({
                'name': result['jikan_data']['name'] if result.get('jikan_data') else result['character_name'],
                'score': result['similarity_score'],
                'id': f"{image_id}.jpg",
                'jikan_data': result.get('jikan_data')
            })

        return jsonify({'results': formatted_results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory(THUMBNAILS_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
