if __name__ == "__main__":
    print("Error: This file is part of the Flask application and cannot be run directly.")
    print("Please run 'python app.py' or 'python run_desktop.py' from the project root instead.")
    import sys
    sys.exit(1)

from flask import Blueprint, render_template, Response, request, redirect, url_for, jsonify
from database.database import Database
from utils.camera import CameraHandler
from config.config import config
import cv2
import numpy as np
import torch
import os
import time
from datetime import datetime
import sys
import math
import warnings
import csv
import re
import threading
import itertools
from typing import List, Dict, Any

from typing import List, Dict, Any

dashboard_bp = Blueprint('dashboard', __name__)
db = Database()
camera_source = 1  # Default to OBS

# Global event to signal new violations for long polling (Moved to utils/events.py)
from utils.events import new_violation_event

# Person tracking dictionaries (for detecting load/unload operations)
person_bboxes = {}  # {frame_num: [(x1, y1, x2, y2, centroid_x, centroid_y), ...]}
persons_in_vehicle = {}  # {obj_id: True/False} - tracks if a person is detected inside vehicle

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    return math.hypot(point1[0] - point2[0], point1[1] - point2[1])

def is_person_inside_bbox(person_center, bbox):
    """Check if person is inside vehicle bounding box."""
    x1, y1, x2, y2 = bbox
    px, py = person_center
    return x1 <= px <= x2 and y1 <= py <= y2

def is_person_near_vehicle(person_center, vehicle_bbox, distance_threshold=100):
    """
    Check if person is near vehicle (loading/unloading).
    Uses distance to the NEAREST POINT on the vehicle bounding box, not the center.
    """
    px, py = person_center
    vx1, vy1, vx2, vy2 = vehicle_bbox
    
    # Calculate nearest point on the rectangle to the person
    nearest_x = max(vx1, min(px, vx2))
    nearest_y = max(vy1, min(py, vy2))
    
    dx = px - nearest_x
    dy = py - nearest_y
    
    distance = math.sqrt(dx*dx + dy*dy)
    
    return distance <= distance_threshold

def process_violations(raw_data) -> List[Dict[str, Any]]:
    """Helper to convert database tuples to dictionaries for templates."""
    processed: List[Dict[str, Any]] = []
    if not raw_data:
        return processed
    for row in raw_data:
        item: Dict[str, Any] = {}
        # If row is already a dict-like object (e.g. sqlite3.Row), use it
        if hasattr(row, 'keys'):
            item = dict(row)
        # If row is a tuple/list, convert to dict
        elif isinstance(row, (list, tuple)):
            # Map tuple to dict assuming order: id, label, timestamp, image_path
            if len(row) > 0: item['id'] = row[0]
            if len(row) > 1: item['label'] = row[1]
            if len(row) > 2: item['timestamp'] = row[2]
            if len(row) > 3: item['image_path'] = row[3]
        
        processed.append(item)
    return processed





@dashboard_bp.route('/api/recent_violations')
def api_recent_violations():
    # Retrieve all violations as a list of dictionaries
    all_violations: List[Dict[str, Any]] = process_violations(db.get_all_violations())
    # Use itertools.islice for safe slicing that satisfies strict type checkers
    return jsonify(list(itertools.islice(all_violations, 10)))

@dashboard_bp.route('/api/realtime_stats')
def api_realtime_stats():
    """Get real-time monitoring counts and FPS from the singleton service."""
    return jsonify(monitoring_service.get_realtime_stats())

@dashboard_bp.route('/api/stats')
def api_stats():
    """Analytics and Reports Data"""
    # Get stats for charts
    by_type = db.count_violations_by_type()
    by_type_data = { (row[0] if row[0] is not None else "Unknown"): row[1] for row in by_type }
    
    daily_trend = db.get_daily_trend(7)
    trend_data = []
    for row in reversed(daily_trend):
        trend_data.append({
            'date': row[0],
            'count': row[1]
        })
    
    total_violations = sum(by_type_data.values())
    
    # Count saved videos in camera/ directory
    camera_dir = os.path.join(os.getcwd(), 'camera')
    saved_videos_count = 0
    if os.path.exists(camera_dir):
        saved_videos_count = len([f for f in os.listdir(camera_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))])
    
    return jsonify({
        'by_type': by_type_data,
        'trend': trend_data,
        'total_violations': total_violations,
        'saved_videos': saved_videos_count
    })

@dashboard_bp.route('/api/config')
def api_config():
    """System Configuration Data"""
    return jsonify({
        'camera_source': config.camera_source,
        'model_path': config.MODEL_PATH,
        'confidence_threshold': config.CONFIDENCE_THRESHOLD,
        'yellow_box_zone': config.YELLOW_BOX_ZONE
    })


@dashboard_bp.route('/api/wait_for_violation')
def wait_for_violation():
    """
    This is a long-polling endpoint. It holds the client's request open
    until a new violation is detected or a timeout occurs.
    Using a 5s timeout prevents lingering thread exhaustion when switching pages.
    """
    event_was_set = new_violation_event.wait(timeout=5)
    
    if event_was_set:
        new_violation_event.clear()  # Reset the event for the next violation
        return jsonify({'update': True})
    else:
        return jsonify({'update': False}) # Timed out, no new violation

# Global detector variable to avoid reloading on every request
from ai_model.detect import VehicleDetector

detector = None

def get_detector():
    """Initialize YOLOv8 detector"""
    global detector
    if detector is None:
        model_path = os.path.join(os.getcwd(), config.MODEL_PATH)
        detector = VehicleDetector(
            model_path=model_path,
            conf_thres=config.CONFIDENCE_THRESHOLD
        )
        print(f"✓ YOLOv8 detector loaded from {model_path}")
    return detector


# Import the more robust CentroidTracker
from ai_model.tracker import CentroidTracker

# Import the singleton monitoring service
from utils.monitoring_service import monitoring_service

def generate_frames():
    """
    Generator that provides processed frames from the shared MonitoringService.
    Catches client disconnects cleanly to prevent thread accumulation when changing pages.
    """
    try:
        while True:
            frame_bytes = monitoring_service.get_frame()
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.033)  # Cap stream output to ~30 FPS per client
            else:
                time.sleep(0.1)
    except (GeneratorExit, ConnectionResetError, BrokenPipeError, OSError):
        # Client navigated away or closed the video feed connection
        pass


@dashboard_bp.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


