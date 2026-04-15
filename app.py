from flask import Flask, request, jsonify, send_from_directory
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
from app_utils.helpers import setup_logging
import threading
import os
from config.config import config

from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Enable CORS for all routes
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')

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
