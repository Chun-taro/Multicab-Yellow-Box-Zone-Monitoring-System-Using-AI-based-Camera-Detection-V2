from flask import Flask, request, jsonify, send_from_directory
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
from utils.helpers import setup_logging
import threading
import os
from config.config import config

from flask_cors import CORS

app = Flask(__name__, 
            static_folder=os.path.join(os.getcwd(), 'frontend/dist'),
            static_url_path='',
            template_folder=os.path.join(os.getcwd(), 'frontend/dist'))
CORS(app) # Enable CORS for all routes
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Serve static files if they exist."""
    static_dir = os.path.join(os.getcwd(), app.static_folder)
    if path != "" and os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    return send_from_directory(static_dir, 'index.html')

@app.errorhandler(404)
def handle_404(e):
    """Fallback for any 404 to support React Router (SPA)."""
    static_dir = os.path.join(os.getcwd(), app.static_folder)
    return send_from_directory(static_dir, 'index.html')

@app.route('/violations/<path:filename>')
def serve_violations(filename):
    """Serve violation images from the static/violations directory."""
    return send_from_directory(os.path.join('static', 'violations'), filename)

setup_logging()

@app.route('/set_camera', methods=['POST'])
def set_camera():
    data = request.json
    if not data or 'source' not in data:
        return jsonify({'error': 'No camera source provided'}), 400
    
    config.camera_source = data['source']
    # You can optionally save to a persistent file here if needed
    return jsonify({'success': True, 'message': f'Camera source updated to {data["source"]}'})

if __name__ == '__main__':
    # The reloader can cause issues in a multi-threaded app, especially with libraries
    # that manage their own event loops or resources (like a camera thread).
    # Disabling it prevents crashes on file changes during development.
    app.run(debug=True, use_reloader=False)
