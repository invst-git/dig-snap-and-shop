from flask import Flask, render_template, request, jsonify
import os
import vision_handler
import search_handler
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes - needed for mobile access via ngrok
CORS(app, resources={r"/*": {"origins": "*"}})
# Simple in-memory visitor counter
VISIT_COUNT = 0

def increment_visit_count():
    global VISIT_COUNT
    VISIT_COUNT += 1
    return VISIT_COUNT

@app.route('/')
def index():
    count = increment_visit_count()
    return render_template('index.html', visit_count=count)

@app.route('/api/identify', methods=['POST'])
def identify():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save temporarily
    temp_path = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(temp_path)

    try:
        query = vision_handler.get_product_query(temp_path)
        return jsonify({'query': query})
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    country = request.args.get('country', 'us')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    results = search_handler.search_products(query, country)
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
