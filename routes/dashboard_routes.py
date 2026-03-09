if __name__ == "__main__":
    print("Error: This file is part of the Flask application and cannot be run directly.")
    print("Please run 'python app.py' or 'python run_desktop.py' from the project root instead.")
    import sys
    sys.exit(1)

from flask import Blueprint, render_template, Response, request, redirect, url_for, jsonify
from database.database import Database
from app_utils.camera import CameraHandler
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

# Global event to signal new violations for long polling
new_violation_event = threading.Event()

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

@dashboard_bp.route('/')
def dashboard():
    violations = process_violations(db.get_all_violations())
    return render_template('dashboard.html', violations=violations)

@dashboard_bp.route('/logs')
def logs():
    violations = process_violations(db.get_all_violations())
    return render_template('logs.html', violations=violations)

@dashboard_bp.route('/api/recent_violations')
def api_recent_violations():
    # Retrieve all violations as a list of dictionaries
    all_violations: List[Dict[str, Any]] = process_violations(db.get_all_violations())
    # Use itertools.islice for safe slicing that satisfies strict type checkers
    return jsonify(list(itertools.islice(all_violations, 10)))

@dashboard_bp.route('/zone_setup')
def zone_setup():
    return render_template('zone_setup.html')

@dashboard_bp.route('/api/wait_for_violation')
def wait_for_violation():
    """
    This is a long-polling endpoint. It holds the client's request open
    until a new violation is detected or a timeout occurs.
    """
    # Wait for the event to be set, with a timeout (e.g., 30 seconds)
    event_was_set = new_violation_event.wait(timeout=30)
    
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

def generate_frames():
    camera = CameraHandler()
    detector = None
    detector_error = None
    try:
        detector = get_detector()
    except Exception as e:
        detector_error = str(e)
        print(f"Warning: AI Detector failed to load: {e}")

    # Check if camera opened successfully
    if camera.use_placeholder:
        print(f"Camera error: Unable to open source. Using placeholder.")
        # Create a placeholder frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "Camera not available", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        placeholder = buffer.tobytes()
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')

    # Load Yellow Box Zone from the central configuration
    yellow_zone = np.array(config.YELLOW_BOX_ZONE, np.int32).reshape((-1, 1, 2))

    # Optimization: Create a bounding box for the zone to crop the frame for detection.
    # This significantly speeds up processing by running the AI model on a smaller image.
    x_coords = yellow_zone[:, :, 0]
    y_coords = yellow_zone[:, :, 1]
    zone_x_min, zone_x_max = np.min(x_coords), np.max(x_coords)
    zone_y_min, zone_y_max = np.min(y_coords), np.max(y_coords)

    # Setup for saving violations
    save_dir = os.path.join("static", "violations")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Initialize Tracker
    # Use the more robust CentroidTracker for better performance and accuracy
    # Initialize the centroid tracker with increased max_disappeared
    # Higher value = tracker keeps vehicle IDs longer when temporarily not detected
    # max_distance increased to 150 to handle larger jumps in high-res frames
    tracker = CentroidTracker(max_disappeared=40, max_distance=150)
    
    vehicle_timers: Dict[int, float] = {}   # {id: start_time}
    movement_start_pos: Dict[int, tuple] = {} # {id: (time, cx, cy)}
    is_stopped_map: Dict[int, bool] = {} # {id: bool}
    violated_ids: set = set()  # Set of IDs that have already triggered a violation
    vehicle_types: Dict[int, str] = {}    # {id: vehicle_type}
    vehicle_loading_status: Dict[int, float] = {} # {id: last_loading_timestamp}
    # Removed all_detections - drawing vehicles directly on detection frames instead
    resolution_checked = False
    
    # FPS optimization parameters
    frame_skip: int = int(getattr(config, 'FRAME_SKIP', 2))  # Process every Nth frame (1=all, 2=every other, etc)
    frame_count: int = 0
    jpeg_quality: int = int(getattr(config, 'JPEG_QUALITY', 70))  # Lower = faster, higher = better quality
    
    # FPS calculation variables
    fps_frames = 0
    fps_last_time = time.time()
    fps_current = 0

    while True:
        frame = camera.read_frame()
        if frame is None:
            break
        
        frame_count += 1
        current_time = time.time()
        
        # Update FPS counter
        # Update FPS counter
        fps_frames += 1
        if current_time - fps_last_time >= 1.0:
            fps_current = fps_frames
            fps_frames = 0
            fps_last_time = current_time
        
        if not resolution_checked:
            h_debug, w_debug = frame.shape[:2]
            print(f"DEBUG: Current Frame Resolution: {w_debug}x{h_debug}")
            max_x = np.max(yellow_zone[:, :, 0])
            max_y = np.max(yellow_zone[:, :, 1])
            if max_x > w_debug or max_y > h_debug:
                print(f"CRITICAL WARNING: Yellow Zone points (Max: {max_x},{max_y}) are OUTSIDE the frame ({w_debug}x{h_debug}).")
                print("The zone will NOT work. Please update config.py FRAME_WIDTH/HEIGHT to match your coordinates.")
            resolution_checked = True

        # Check for dynamic zone updates from config
        current_config_zone = config.YELLOW_BOX_ZONE
        # Simple update check: checks if the first point matches. 
        # For more robustness we could compare the whole list, but this is fast.
        if len(current_config_zone) > 0 and (yellow_zone[0,0,0] != current_config_zone[0][0] or yellow_zone[0,0,1] != current_config_zone[0][1]):
             yellow_zone = np.array(current_config_zone, np.int32).reshape((-1, 1, 2))
             # Update validation bounds
             x_coords = yellow_zone[:, :, 0]
             y_coords = yellow_zone[:, :, 1]
             # Force resolution re-check next frame if needed, but mainly just update the drawing 
        
        # Draw the Yellow Box Zone on every frame
        cv2.polylines(frame, [yellow_zone], isClosed=True, color=(0, 255, 255), thickness=2)
        
        # Only run AI model every Nth frame to boost FPS
        # Tracking state carries over to skipped frames
        if detector and (frame_count % frame_skip) == 0:
            # AI Detection (runs every frame_skip frames)
            detections_for_tracker = [] # List of [x, y, w, h, label]

            # Run YOLOv8 detection on the FULL frame to detect all vehicles on screen
            # No need to convert BGR to RGB - ultralytics handles this internally
            detections_raw = detector.detect(frame)
            
            # YOLOv8 class names (COCO dataset)
            class_names = {
                0: 'person', 2: 'car', 3: 'motorcycle',
                5: 'bus', 7: 'truck'
            }
            
            # Convert class IDs to class names and track detections
            bbox_to_label = {}
            person_count: int = 0
            vehicle_count: int = 0
            current_persons = []  # Store person detections for proximity checks
            
            for detection in detections_raw:
                cls_id = detection['class']
                conf = detection['confidence']
                
                # Skip if not a vehicle or person class
                if cls_id not in class_names:
                    continue
                    
                label = class_names[cls_id]
                
                # VEHICLE FALLBACK: If AI thinks it's a truck or bus (or generic vehicle), 
                # map it to 'car' as requested by the user for multicab consistency.
                if label in ['truck', 'bus', 'vehicle']:
                    label = 'car'
                    
                x1, y1, x2, y2 = detection['bbox']
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Calculate centroid and roof point for zone checking
                obj_cx = int((x1 + x2) / 2)
                obj_cy = int((y1 + y2) / 2)
                obj_stable_cx = int((x1 + x2) / 2)
                obj_stable_cy = int(y1 + (y2 - y1) * 0.2)
                
                is_center_in = cv2.pointPolygonTest(yellow_zone, (obj_cx, obj_cy), False) >= 0
                is_roof_in = cv2.pointPolygonTest(yellow_zone, (obj_stable_cx, obj_stable_cy), False) >= 0
                is_in_zone = is_center_in or is_roof_in
                
                if label == 'person':
                    # STRICT CONFIDENCE CHECK for People
                    # Lowered from 0.65 to 0.45 based on user feedback (some valid persons were missed)
                    # This balance avoids total ghosts while catching real people
                    if conf < 0.45:
                         continue
                    
                    # DISTANCE FILTER: Ignore people far from the yellow zone
                    # Calculate distance from the polygon (Positive=Inside, Negative=Outside)
                    dist_to_zone = cv2.pointPolygonTest(yellow_zone, (obj_cx, obj_cy), True)
                    
                    # If person is more than 250 pixels OUTSIDE the zone, ignore them
                    if dist_to_zone < -250:
                        continue
                         
                    person_count += 1
                    current_persons.append((x1, y1, x2, y2, obj_cx, obj_cy))
                    
                    # DRAW PERSON: Visual feedback for user
                    # Cyan color for persons (0, 255, 255) in BGR is Yellow, let's use Magenta/Pink (255, 0, 255) or Green
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                    cv2.putText(frame, f"Person {conf:.2f}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                    
                    # Store person for later proximity check with vehicles
                    # Will draw if within 1 meter of a multicab (loading/unloading)
                elif label in ['car', 'truck', 'bus', 'motorcycle']:
                    vehicle_count += 1
                    # ONLY track vehicles that are in the yellow box
                    # (User requested to revert to in-zone only tracking)
                    if is_in_zone:
                        rect = (x1, y1, x2, y2)
                        detections_for_tracker.append(rect)
                        bbox_to_label[rect] = label

            # 2. Update Tracker
            tracked_objects_map = tracker.update(detections_for_tracker)
        else:
            # Use existing tracked objects when not processing frame
            tracked_objects_map = tracker.get_current_objects()
            person_count = 0
            vehicle_count = 0
        
        current_frame_ids = set()
        
        # 3. Process Tracked Vehicles
        for obj_id, (centroid, bbox) in tracked_objects_map.items():
            # Check disappeared status
            disappeared_count = tracker.disappeared.get(obj_id, 0)
            
            # --- FLICKER PREVENTION VS GHOST SUPPRESSION ---
            # If object has disappeared (not matched to detection this frame):
            # 1. Don't process for violations (it's effectively 'stationary' because it's stale data)
            # 2. Don't draw it if it's been gone too long (prevent double outline with new ID)
            if disappeared_count > 0:
                # If it's been gone for a while, just skip it entirely to prevent double outlines
                # This should be less than max_disappeared to show the 'ghost' for a bit
                if disappeared_count > 15:
                    continue
                
                # If it's recently gone, we might draw it for smoothness, 
                # but we MUST NOT count it as a violation or update its "stopped" timer.
                # Just mark it as 'not stopped' so invalid timers don't tick.
                is_stopped_ghost = False
                
                # IMPORTANT: While disappeared, we don't update the timer.
                # However, we DO keep the ID in current_frame_ids so the state isn't deleted yet.
                current_frame_ids.add(obj_id)
            else:
                is_stopped_ghost = None # Process normally
                current_frame_ids.add(obj_id)

            x1, y1, x2, y2 = bbox
            w, h = x2 - x1, y2 - y1
            # Re-associate the label using the bounding box
            label = bbox_to_label.get(tuple(bbox), 'vehicle') if (frame_count % frame_skip) == 0 else vehicle_types.get(obj_id, 'vehicle')

            # Calculate center point and explicitly cast to standard Python integers.
            # This prevents a cv2.error caused by passing numpy integer types to OpenCV functions.
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            
            # Use top-center for movement tracking because it's more stable when vehicles are occluded from the bottom
            stable_cx = int((x1 + x2) / 2)
            stable_cy = int(y1 + (y2 - y1) * 0.2)
            
            # Hybrid Zone Check: Vehicle is "In Zone" if either Center or Roof is inside.
            is_center_in = cv2.pointPolygonTest(yellow_zone, (cx, cy), False) >= 0
            is_roof_in = cv2.pointPolygonTest(yellow_zone, (stable_cx, stable_cy), False) >= 0
            is_in_zone = is_center_in or is_roof_in
            
            # VISUAL FILTER: 
            # ZONE FOCUS: If the vehicle is outside the zone, we track it internally but don't draw it.
            should_draw = is_in_zone
            
            # Check if Stopped (compare with position 1 second ago)
            current_time = time.time()
            if obj_id not in movement_start_pos:
                movement_start_pos[obj_id] = (current_time, stable_cx, stable_cy)
                is_stopped_map[obj_id] = False # Assume moving initially
            
            start_t, start_x, start_y = movement_start_pos[obj_id]
            if current_time - start_t >= 1.0:
                # CRITICAL FIX: If object is disappeared (ghost), force it to be NOT stopped
                if is_stopped_ghost is not None:
                     is_stopped_map[obj_id] = False
                else:
                    dist_moved = math.hypot(stable_cx - start_x, stable_cy - start_y)
                    if dist_moved < 15: # Increased from 8 to 15 to tolerate bounding box jiggle from occlusion
                        is_stopped_map[obj_id] = True
                    else:
                        is_stopped_map[obj_id] = False
                
                # Reset reference
                movement_start_pos[obj_id] = (current_time, stable_cx, stable_cy)
            is_stopped = is_stopped_map.get(obj_id, False)

            # --- CHECK FOR PEOPLE IN VEHICLE (Violation Detection) ---
            # Loop over each person detected
            person_nearby = False
            person_inside = False
            
            # If the vehicle is currently "disappeared" (occluded), skip violation logic
            # and interaction logic to avoid false triggers or state corruption.
            if is_stopped_ghost is not None:
                continue

            # Using persistence for loading status to avoid flickering
            # vehicle_loading_status tracks {obj_id: last_loading_timestamp}
            
            if current_persons:
                for px1, py1, px2, py2, pcx, pcy in current_persons:
                    # ONLY consider people on the RIGHT side of the vehicle's center
                    # because the real sidewalk is on the right. People on the left are in the street.
                    if pcx > stable_cx:
                        # Check proximity to this vehicle
                        vehicle_bbox = (x1, y1, x2, y2)
                        
                        # Check if person is inside vehicle bbox (got in)
                        if x1 <= pcx <= x2 and y1 <= pcy <= y2:
                            person_inside = True
                        
                        # Check if person is near vehicle (loading/unloading - 60px ≈ 0.6 meter)
                        elif is_person_near_vehicle((pcx, pcy), vehicle_bbox, distance_threshold=60):
                            person_nearby = True
            
            # Update Persistent Loading Status
            if person_nearby or person_inside:
                vehicle_loading_status[obj_id] = current_time
            
            # Check if currently considered "loading" (within last 3 seconds)
            last_loading_time = vehicle_loading_status.get(obj_id, 0)
            is_loading_active = (current_time - last_loading_time) < 3.0

            # --- State Management & Violation Triggering ---
            time_limit = getattr(config, 'STOP_TIME_LIMIT', 15)

            # Condition to start/continue timer: in zone, stopped, and a vehicle.
            if is_in_zone and label != 'person':
                timer_active = False
                
                # Check start/continue conditions
                if obj_id in vehicle_timers:
                    # If loading is active, reset/stop the timer
                    if is_loading_active:
                        vehicle_timers.pop(obj_id, None)
                        timer_active = False
                    else:
                        timer_active = True # Continue counting
                elif is_stopped and not is_loading_active:
                    timer_active = True # Start counting from stop
                
                if timer_active:
                    if obj_id not in vehicle_timers:
                        # New timer start
                        vehicle_timers[obj_id] = time.time()
                        vehicle_types[obj_id] = label

                    # Calculate elapsed
                    elapsed = time.time() - vehicle_timers[obj_id]
                    
                    # If time limit is exceeded, mark as violator (if not already marked)
                    if elapsed >= time_limit and obj_id not in violated_ids:
                        violated_ids.add(obj_id)
                        # --- CAPTURE AND SAVE VIOLATION (RUNS ONCE) ---
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Save cropped image (closer view) for easier identification
                        h_img, w_img, _ = frame.shape
                        pad = 50  # Padding around the vehicle
                        crop_x1, crop_y1 = max(0, x1 - pad), max(0, y1 - pad)
                        crop_x2, crop_y2 = min(w_img, x2 + pad), min(h_img, y2 + pad)
                        cropped_img = frame[crop_y1:crop_y2, crop_x1:crop_x2].copy()
                        
                        # Draw violation marker on the cropped image for clear identification
                        # Calculate relative coordinates for the crop
                        rel_x1, rel_y1 = x1 - crop_x1, y1 - crop_y1
                        rel_x2, rel_y2 = x2 - crop_x1, y2 - crop_y1
                        
                        # Draw red rectangle and "VIOLATION" text
                        cv2.rectangle(cropped_img, (rel_x1, rel_y1), (rel_x2, rel_y2), (0, 0, 255), 2)
                        cv2.putText(cropped_img, "VIOLATION", (rel_x1, rel_y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Get vehicle type
                        vehicle_type = vehicle_types.get(obj_id, label)

                        filename = os.path.join(save_dir, f"violation_{timestamp}_{label}_{obj_id}.jpg")
                        cv2.imwrite(filename, cropped_img)
                        print(f"Violation saved: {filename}")
                        
                        # Save record to database
                        try:
                            db_image_path = f"violations/violation_{timestamp}_{label}_{obj_id}.jpg"
                            db_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Use vehicle type as label
                            db_label = vehicle_type

                            # Save to CSV
                            csv_path = os.path.join(save_dir, "violation_log.csv")
                            file_exists = os.path.isfile(csv_path)
                            try:
                                with open(csv_path, mode='a', newline='') as f:
                                    writer = csv.writer(f)
                                    if not file_exists:
                                        writer.writerow(['Timestamp', 'Vehicle Type', 'Evidence'])
                                    writer.writerow([db_timestamp, vehicle_type, db_image_path])
                            except Exception as e:
                                print(f"CSV Error: {e}")

                            # Ensure your Database class has an insert_violation method
                            if hasattr(db, 'insert_violation'):
                                # Prepare image blob
                                ret, buffer = cv2.imencode('.jpg', cropped_img)
                                image_blob = buffer.tobytes() if ret else None
                                
                                # Create detection ID from timestamp and tracking object ID
                                detection_id = f"{timestamp}_{obj_id}"
                                
                                # Insert with enhanced parameters
                                db.insert_violation(
                                    vehicle_type=vehicle_type,
                                    timestamp=db_timestamp,
                                    image_path=db_image_path,
                                    image_blob=image_blob,
                                    detection_id=detection_id,
                                    stop_duration=elapsed,
                                    confidence=0.0,  # TODO: maintain confidence mapping
                                    notes=f"Object ID: {obj_id}, Stopped for {elapsed:.1f}s"
                                )

                        except Exception as e:
                            print(f"Database error: {e}")
                        
                        # After the violation is processed, set the event to notify long-poll clients
                        new_violation_event.set()
                else:
                     # In zone but running and not previously stopped -> No timer
                     pass

            else:
                 # Not in zone -> Clear timer
                 if obj_id in vehicle_timers:
                     vehicle_timers.pop(obj_id, None)

            # --- Drawing Logic ---
            if should_draw:
                # 1. Check if it's a confirmed, persistent violator
                if obj_id in violated_ids:
                    color = (0, 0, 255) # Red for violation
                    cv2.putText(frame, "VIOLATION", (x1, y1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                # 2. Else, Check if it's in a warning state (stopped in zone, timer running)
                elif obj_id in vehicle_timers:
                    elapsed = time.time() - vehicle_timers[obj_id]
                    remaining = int(time_limit - elapsed)
                    color = (0, 165, 255) # Orange for warning
                    cv2.putText(frame, f"{remaining}s", (x1, y1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                # 3. Otherwise, it's a safe vehicle
                else:
                    color = (255, 0, 0) # Blue for safe

                # Draw the bounding box with the determined color
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                label_text = f"{label} ID:{obj_id}"
                cv2.putText(frame, label_text, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                # Draw tracking anchor points (Dual Sensing: Roof and Center)
                cv2.circle(frame, (stable_cx, stable_cy), 4, (0, 255, 255), -1) # Yellow Roof Dot
                cv2.circle(frame, (cx, cy), 4, (255, 255, 0), -1)             # Cyan Center Dot
            
            tracking_points = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
            for pt in tracking_points:
                cv2.circle(frame, pt, 2, (0, 255, 255), -1) 


        # Cleanup: Remove IDs that are no longer in the frame
        # This prevents memory leaks in the dictionaries
        # using .pop(k, None) is safer/cleaner than del
        for obj_id in list(vehicle_timers.keys()):
            if obj_id not in current_frame_ids:
                vehicle_timers.pop(obj_id, None)
        
        for obj_id in list(movement_start_pos.keys()):
            if obj_id not in current_frame_ids:
                movement_start_pos.pop(obj_id, None)
        
        for obj_id in list(is_stopped_map.keys()):
            if obj_id not in current_frame_ids:
                is_stopped_map.pop(obj_id, None)
        
        for obj_id in list(vehicle_types.keys()):
            if obj_id not in current_frame_ids:
                vehicle_types.pop(obj_id, None)
        
        for obj_id in list(vehicle_loading_status.keys()):
            if obj_id not in current_frame_ids:
                vehicle_loading_status.pop(obj_id, None)
        
        for obj_id in list(persons_in_vehicle.keys()):
            if obj_id not in current_frame_ids:
                persons_in_vehicle.pop(obj_id, None)
        
        for obj_id in list(violated_ids):
            if obj_id not in current_frame_ids:
                violated_ids.discard(obj_id)

        
        
        # Display counts on screen
        cv2.putText(frame, f"People: {person_count} Vehicles: {vehicle_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        if detector_error:
            # Draw error message on frame if detector failed
            cv2.putText(frame, "AI Error: " + detector_error, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Display FPS on frame
        cv2.putText(frame, f"FPS: {fps_current}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # --- OPTIMIZED JPEG ENCODING ---
        # Use quality setting to balance speed and image quality
        # Lower quality = faster encoding and smaller file size
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        if not ret:
            continue  # Skip frame if encoding fails
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@dashboard_bp.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

