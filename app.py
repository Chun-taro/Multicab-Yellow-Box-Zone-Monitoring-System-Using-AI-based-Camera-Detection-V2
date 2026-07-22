from utils.helpers import setup_logging
setup_logging()

from flask import Flask, request, jsonify, send_from_directory
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
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
    """Serve React frontend static files or fallback to index.html for SPA routing."""
    static_dir = os.path.join(os.getcwd(), app.static_folder)
    index_file = os.path.join(static_dir, 'index.html')
    
    if not os.path.exists(index_file):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Frontend Build Required</title>
            <style>
                body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 2rem; border-radius: 12px; border: 1px solid #334155; max-width: 500px; text-align: center; }
                h2 { color: #38bdf8; margin-top: 0; }
                code { background: #0f172a; padding: 4px 8px; border-radius: 4px; color: #f43f5e; font-family: monospace; }
                pre { background: #0f172a; padding: 1rem; border-radius: 6px; text-align: left; color: #a5f3fc; overflow-x: auto; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>React Frontend Not Built</h2>
                <p>The production frontend bundle was not found in <code>frontend/dist</code>.</p>
                <p><strong>To fix this on a new clone, run:</strong></p>
                <pre>cd frontend&#10;npm install&#10;npm run build</pre>
                <p>Or run Vite dev server in parallel: <code>npm run dev</code></p>
            </div>
        </body>
        </html>
        """, 404

    if path != "" and os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    return send_from_directory(static_dir, 'index.html')

@app.errorhandler(404)
def handle_404(e):
    """Fallback for any 404 to support React Router (SPA)."""
    static_dir = os.path.join(os.getcwd(), app.static_folder)
    index_file = os.path.join(static_dir, 'index.html')
    if os.path.exists(index_file):
        return send_from_directory(static_dir, 'index.html')
    return serve_react('')

@app.route('/violations/<path:filename>')
def serve_violations(filename):
    """Serve violation images from the static/violations directory."""
    return send_from_directory(os.path.join('static', 'violations'), filename)



@app.route('/set_camera', methods=['POST'])
def set_camera():
    data = request.json
    if not data or 'source' not in data:
        return jsonify({'error': 'No camera source provided'}), 400
    
    config.camera_source = data['source']
    # You can optionally save to a persistent file here if needed
    return jsonify({'success': True, 'message': f'Camera source updated to {data["source"]}'})

@app.route('/api/test_videos', methods=['GET'])
def list_test_videos():
    camera_dir = os.path.join(os.getcwd(), 'camera')
    if not os.path.exists(camera_dir):
        return jsonify([])
    
    videos = [f for f in os.listdir(camera_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    return jsonify(videos)

from werkzeug.utils import secure_filename

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        camera_dir = os.path.join(os.getcwd(), 'camera')
        if not os.path.exists(camera_dir):
            os.makedirs(camera_dir)
            
        file_path = os.path.join(camera_dir, filename)
        file.save(file_path)
        return jsonify({'success': True, 'filename': filename})

if __name__ == '__main__':
    # The reloader can cause issues in a multi-threaded app, especially with libraries
    # that manage their own event loops or resources (like a camera thread).
    # Disabling it prevents crashes on file changes during development.
    app.run(debug=True, use_reloader=False)
