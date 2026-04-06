from flask import Flask, request, jsonify
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
from app_utils.helpers import setup_logging
import threading
from config.config import config

app = Flask(__name__)
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')

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
