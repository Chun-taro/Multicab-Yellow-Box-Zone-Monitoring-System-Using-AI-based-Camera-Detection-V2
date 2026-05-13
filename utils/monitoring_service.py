import cv2
import numpy as np
import threading
import time
import os
import logging
from datetime import datetime
from config.config import config
from utils.camera import CameraHandler
from ai_model.detect import VehicleDetector
from ai_model.tracker import CentroidTracker
from ai_model.lpr import lpr_reader, crop_plate_region
from database.database import Database
import math
import csv

class MonitoringService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MonitoringService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.camera = None
        self.tracker = None
        self.db = Database()
        
        # Asynchronous AI Model Loading to prevent blocking system startup
        self.detector = None
        self.ai_loading = True
        self.ai_error = None
        
        logging.info("Initializing AI Model pre-loader (YOLOv8)...")
        threading.Thread(target=self._load_model_async, daemon=True).start()
        
        self.latest_frame = None
        self.last_access_time = 0
        self.is_running = False
        self.thread = None
        self.stop_event = threading.Event()
        
        # Tracking State
        self.vehicle_timers = {}
        self.movement_start_pos = {}
        self.is_stopped_map = {}
        self.violated_ids = set()
        self.vehicle_types = {}
        self.vehicle_loading_status = {}
        
        self.fps_current = 0
        self.fps_ai = 0
        self.person_count = 0
        self.vehicle_count = 0
        
        # Zone tracking for dynamic updates
        self.zone_coords = None
        self.yellow_zone = None
        self._check_zone_update()
        
        # New State for Async AI tracking
        self.current_persons = []
        self.tracked_objects_map = {}
        self.bbox_to_label = {}
        
        # Initialize placeholder frame for immediate feedback
        self._set_placeholder_frame("Initializing system...")
        
        self._initialized = True
        logging.info("MonitoringService singleton initialized")

    def _load_model_async(self):
        """Loads the AI model and LPR in a background thread."""
        try:
            model_path = os.path.join(os.getcwd(), config.MODEL_PATH)
            self.detector = VehicleDetector(
                model_path=model_path,
                conf_thres=config.CONFIDENCE_THRESHOLD
            )
            self.ai_loading = False
            logging.info("✓ AI Model loaded and ready (Background Thread)")
        except Exception as e:
            self.ai_error = str(e)
            self.ai_loading = False
            logging.error(f"Detector failed to load in background: {e}")
        
        # Initialize LPR in same background thread (after YOLO to avoid resource contention)
        try:
            lpr_reader.initialize()
        except Exception as e:
            logging.warning(f"LPR initialization failed (non-critical): {e}")

    def start(self):
        """Starts the monitoring thread if not already running."""
        with self._lock:
            if not self.is_running:
                logging.info("Starting monitoring threads...")
                self.stop_event.clear()
                self.is_running = True
                
                # Main Video Thread (30 FPS)
                self.thread = threading.Thread(target=self._run_loop, daemon=True)
                self.thread.start()
                
                # AI Inference Thread (Decoupled)
                self.ai_thread = threading.Thread(target=self._ai_loop, daemon=True)
                self.ai_thread.start()

    def stop(self):
        """Stops the monitoring thread and releases resources."""
        with self._lock:
            if self.is_running:
                logging.info("Stopping monitoring thread...")
                self.is_running = False
                self.stop_event.set()
                if self.thread:
                    self.thread.join(timeout=1.0)
                if hasattr(self, 'ai_thread') and self.ai_thread:
                    self.ai_thread.join(timeout=1.0)
                
                if self.camera:
                    self.camera.close()
                    self.camera = None
                
                self.detector = None # Let GC handle it
                logging.info("Monitoring thread stopped")

    def get_frame(self):
        """Called by Flask clients to get the latest processed frame."""
        self.last_access_time = time.time()
        
        if not self.is_running:
            self.start()
            
        return self.latest_frame

    def _run_loop(self):
        """The main AI detection and frame processing loop."""
        try:
            # Initialize Camera
            self.camera = CameraHandler()
            
            # AI Detector is already pre-loaded in __init__
            if self.detector is None:
                 logging.error("AI Detector not found. Attempting reload...")
                 # Fallback reload logic if needed
                
            # Initialize Tracker
            self.tracker = CentroidTracker(max_disappeared=15, max_distance=200)
            
            # Initial zone trigger
            self._check_zone_update()
            
            # Constants
            frame_skip = int(getattr(config, 'FRAME_SKIP', 2))
            jpeg_quality = int(getattr(config, 'JPEG_QUALITY', 70))
            time_limit = getattr(config, 'STOP_TIME_LIMIT', 15)
            save_dir = os.path.join("static", "violations")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            frame_count = 0
            fps_frames = 0
            fps_last_time = time.time()
            
            current_persons = []
            
            # Keep-alive timeout (shut down if no one is watching)
            IDLE_TIMEOUT = 10 # seconds

            while not self.stop_event.is_set():
                # Check for idle timeout
                if time.time() - self.last_access_time > IDLE_TIMEOUT:
                    logging.info("No active viewers detected. Service entering idle mode.")
                    break

                # Frame capture
                frame = self.camera.read_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Check for camera change
                if str(self.camera.source) != str(config.camera_source):
                    logging.info(f"Camera source changed to {config.camera_source}. Resetting...")
                    self.camera.source = config.camera_source
                    self.camera.open()
                
                frame_count += 1
                current_time = time.time()
                
                # Update Video FPS
                fps_frames += 1
                if current_time - fps_last_time >= 1.0:
                    self.fps_current = fps_frames
                    fps_frames = 0
                    fps_last_time = current_time
                
                # Periodic zone update check
                if frame_count % 30 == 0:
                    self._check_zone_update()
                
                # DRAWING (Fast 30 FPS Stream)
                if self.yellow_zone is not None:
                    cv2.polylines(frame, [self.yellow_zone], isClosed=True, color=(0, 255, 255), thickness=2)
                
                # Draw latest detections from the AI thread using a snapshot for thread safety
                current_detections = list(self.tracked_objects_map.items())
                for obj_id, (centroid, bbox) in current_detections:
                    if obj_id not in self.movement_start_pos: continue # Waiting for AI
                    x1, y1, x2, y2 = bbox
                    is_in_zone = False
                    if self.yellow_zone is not None:
                        # Explicitly cast to float for OpenCV compatibility
                        test_pt1 = (float(x1 + (x2 - x1) / 2), float(y1 + (y2 - y1) / 2))
                        test_pt2 = (float(x1 + (x2 - x1) / 2), float(y1 + (y2 - y1) * 0.5))
                        is_in_zone = cv2.pointPolygonTest(self.yellow_zone, test_pt1, False) >= 0 or \
                                     cv2.pointPolygonTest(self.yellow_zone, test_pt2, False) >= 0
                    
                    if not is_in_zone: continue
                    
                    color = (255, 0, 0) # Blue
                    if obj_id in self.violated_ids: color = (0, 0, 255) # Red
                    elif obj_id in self.vehicle_timers:
                        elapsed = time.time() - self.vehicle_timers[obj_id]
                        rem = max(0, int(time_limit - elapsed))
                        cv2.putText(frame, f"{rem}s", (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                        color = (0, 165, 255) # Orange
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                    cv2.putText(frame, f"{self.vehicle_types.get(obj_id, 'car')} ID:{obj_id}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

                for p in self.current_persons:
                    cv2.rectangle(frame, (p[0], p[1]), (p[2], p[3]), (0, 255, 0), 1)
                
                cv2.putText(frame, f"People: {self.person_count} Vehicles: {self.vehicle_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                # Bottom HUD
                h_fps, w_fps = frame.shape[:2]
                cv2.rectangle(frame, (5, h_fps - 40), (220, h_fps - 5), (0, 0, 0), -1)
                cv2.rectangle(frame, (5, h_fps - 40), (220, h_fps - 5), (0, 255, 0), 1)
                cv2.putText(frame, f"Stream: {self.fps_current} FPS | AI: {self.fps_ai} FPS", (15, h_fps - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # JPEG Encoding at high priority
                res, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                if res:
                    self.latest_frame = buffer.tobytes()
                
                # Maintain target FPS to avoid playback being too fast
                target_delay = 1.0 / getattr(config, 'FPS', 30)
                elapsed_loop = time.time() - current_time
                sleep_time = max(0.001, target_delay - elapsed_loop)
                time.sleep(sleep_time) 

        except Exception as e:
            logging.error(f"Error in MonitoringService loop: {e}")
        finally:
            with self._lock:
                self.is_running = False
                if self.camera:
                    self.camera.close()
                    self.camera = None

    def _save_violation(self, frame, bbox, obj_id, label, elapsed):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        x1, y1, x2, y2 = bbox
        h, w, _ = frame.shape
        pad = 50
        cx1, cy1, cx2, cy2 = max(0, x1-pad), max(0, y1-pad), min(w, x2+pad), min(h, y2+pad)
        cropped = frame[cy1:cy2, cx1:cx2].copy()
        cv2.rectangle(cropped, (x1-cx1, y1-cy1), (x2-cx1, y2-cy1), (0, 0, 255), 2)
        cv2.putText(cropped, "VIOLATION", (x1-cx1, y1-cy1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # --- LPR: Read plate from vehicle crop ---
        plate_number = None
        try:
            plate_crop = crop_plate_region(frame, bbox)
            if plate_crop is not None:
                plate_number = lpr_reader.read_plate(plate_crop)
                if plate_number:
                    logging.info(f"LPR detected plate: {plate_number} for vehicle ID {obj_id}")
                    # Overlay plate on violation image
                    cv2.putText(cropped, f"PLATE: {plate_number}",
                                (x1-cx1, y2-cy1+20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        except Exception as e:
            logging.warning(f"LPR failed for vehicle {obj_id}: {e}")
        
        filename = f"violation_{timestamp}_{label}_{obj_id}.jpg"
        save_path = os.path.join("static", "violations", filename)
        cv2.imwrite(save_path, cropped)
        
        db_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_image_path = f"violations/{filename}"
        
        try:
            if hasattr(self.db, 'insert_violation'):
                ret, buffer = cv2.imencode('.jpg', cropped)
                self.db.insert_violation(
                    vehicle_type=label, timestamp=db_timestamp, image_path=db_image_path,
                    image_blob=buffer.tobytes() if ret else None, detection_id=f"{timestamp}_{obj_id}",
                    stop_duration=elapsed, notes=f"Object ID: {obj_id}, Stopped for {elapsed:.1f}s",
                    plate_number=plate_number
                )
            
            from utils.events import new_violation_event
            new_violation_event.set()
        except Exception as e:
            logging.error(f"Failed to save violation to DB: {e}")

    def _ai_loop(self):
        """Asynchronous AI detection loop to prevent visual lag."""
        try:
            # Wait for detector and camera to be ready
            while not self.stop_event.is_set() and (self.detector is None or self.camera is None):
                time.sleep(0.5)
            
            # AI thread will use the class-level self.yellow_zone
            self._check_zone_update()
            time_limit = getattr(config, 'STOP_TIME_LIMIT', 15)
            
            ai_frames = 0
            ai_last_time = time.time()
            
            while not self.stop_event.is_set():
                if not self.is_running: 
                    time.sleep(0.1)
                    continue
                    
                frame = self.camera.read_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                current_time = time.time()
                ai_frames += 1
                if current_time - ai_last_time >= 1.0:
                    self.fps_ai = ai_frames
                    ai_frames = 0
                    ai_last_time = current_time

                # AI Inference (Full frame)
                detections_raw = self.detector.detect(frame)
                
                class_names = {0: 'person', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
                detections_for_tracker = []
                bbox_to_label = {}
                person_count = 0
                vehicle_count = 0
                current_persons = []
                
                for detection in detections_raw:
                    cls_id = detection['class']
                    conf = detection['confidence']
                    if cls_id not in class_names: continue
                    label = class_names[cls_id]
                    if label in ['truck', 'bus', 'vehicle']: label = 'car'
                    x1, y1, x2, y2 = map(int, detection['bbox'])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # 1. Detection logic for vehicles (PRIORITY)
                    if label == 'car':
                        is_in_zone = False
                        if self.yellow_zone is not None:
                            test_pt1 = (float(cx), float(cy))
                            test_pt2 = (float(cx), float(y1 + (y2 - y1) * 0.5))
                            is_in_zone = cv2.pointPolygonTest(self.yellow_zone, test_pt1, False) >= 0 or \
                                         cv2.pointPolygonTest(self.yellow_zone, test_pt2, False) >= 0
                        else:
                            # If no zone is defined, we track everything
                            is_in_zone = True
                        
                        if is_in_zone:
                            vehicle_count += 1
                            rect = (x1, y1, x2, y2)
                            detections_for_tracker.append(rect)
                            bbox_to_label[rect] = label
                    
                    # 2. Detection logic for persons (Suppressed if overlapping with vehicles)
                    elif label == 'person':
                        if conf < 0.45: continue
                        
                        # SIDEWALK FILTER: Only detect persons on the right side of the frame
                        # People on the left are typically enforcers or motorcycle riders
                        frame_w = frame.shape[1]
                        if cx < (frame_w // 2): continue

                        # OVERLAP FILTER: Skip if this person is already inside a vehicle detection
                        is_inside_vehicle = False
                        for v_rect in detections_for_tracker:
                            vx1, vy1, vx2, vy2 = v_rect
                            # If person bbox is 80% inside a vehicle bbox, it's likely a misdetection
                            if x1 > vx1-10 and y1 > vy1-10 and x2 < vx2+10 and y2 < vy2+10:
                                is_inside_vehicle = True
                                break
                        
                        if is_inside_vehicle: continue

                        # Track persons near the zone for loading/unloading detection
                        if self.yellow_zone is not None:
                            dist_to_zone = cv2.pointPolygonTest(self.yellow_zone, (float(cx), float(cy)), True)
                            if dist_to_zone >= -250: # Includes inside (>=0) and nearby (-250 to 0)
                                person_count += 1
                                current_persons.append((x1, y1, x2, y2, cx, cy, conf))
                        else:
                            person_count += 1
                            current_persons.append((x1, y1, x2, y2, cx, cy, conf))

                # Tracking Update
                self.tracked_objects_map = self.tracker.update(detections_for_tracker)
                self.bbox_to_label.update(bbox_to_label)
                self.person_count = person_count
                self.vehicle_count = vehicle_count
                self.current_persons = current_persons

                # VIOLATION LOGIC (Moved to AI thread to prevent main loop slowdown)
                current_frame_ids = set()
                # VIOLATION LOGIC (Working with thread-safe current snap)
                for obj_id, (centroid, bbox) in self.tracked_objects_map.copy().items():
                    if self.tracker.disappeared.get(obj_id, 0) > 15: continue
                    current_frame_ids.add(obj_id)
                    x1, y1, x2, y2 = bbox
                    scx, scy = (x1+x2)//2, (y1+y2)//2
                    
                    if self.yellow_zone is not None:
                        is_in_zone = cv2.pointPolygonTest(self.yellow_zone, (float(scx), float(scy)), False) >= 0
                    else:
                        is_in_zone = False
                    
                    # Stopped Detection
                    if obj_id not in self.movement_start_pos:
                        self.movement_start_pos[obj_id] = (current_time, scx, scy)
                    else:
                        start_t, start_x, start_y = self.movement_start_pos[obj_id]
                        if current_time - start_t >= 1.0:
                            dist = math.hypot(scx - start_x, scy - start_y)
                            self.is_stopped_map[obj_id] = dist < 15
                            self.movement_start_pos[obj_id] = (current_time, scx, scy)
                    
                    # Loading status
                    for p_data in current_persons:
                        pcx, pcy = p_data[4], p_data[5]
                        if pcx > scx:
                            dist = math.sqrt((pcx - max(x1, min(pcx, x2)))**2 + (pcy - max(y1, min(pcy, y2)))**2)
                            if dist < 60 or (x1 <= pcx <= x2 and y1 <= pcy <= y2):
                                self.vehicle_loading_status[obj_id] = current_time
                    
                    # Timer & Violation
                    if is_in_zone:
                        is_loading = (current_time - self.vehicle_loading_status.get(obj_id, 0)) < 3.0
                        is_stopped = self.is_stopped_map.get(obj_id, False)
                        
                        if is_stopped and not is_loading:
                            if obj_id not in self.vehicle_timers: self.vehicle_timers[obj_id] = current_time
                            elapsed = current_time - self.vehicle_timers[obj_id]
                            if elapsed >= time_limit and obj_id not in self.violated_ids:
                                self.violated_ids.add(obj_id)
                                # Pre-encode frame for violation if camera is available
                                self._save_violation(frame, bbox, obj_id, self.vehicle_types.get(obj_id, 'car'), elapsed)
                        else:
                            self.vehicle_timers.pop(obj_id, None)
                    
                    # Periodic local check (optional if shared state is updated by main loop)
                    if ai_frames % 10 == 0:
                        self._check_zone_update()

        except Exception as e:
            logging.error(f"Error in AI loop: {e}")

    def _check_zone_update(self):
        """Checks if the zone configuration has changed and updates the shared state."""
        new_coords = config.YELLOW_BOX_ZONE
        if new_coords != self.zone_coords:
            logging.info("Zone configuration change detected. Updating monitoring area...")
            self.zone_coords = new_coords
            self.yellow_zone = np.array(new_coords, np.int32).reshape((-1, 1, 2))

    def _set_placeholder_frame(self, text):
        """Sets a placeholder frame for UI feedback while camera is starting."""
        w = getattr(config, 'FRAME_WIDTH', 1280)
        h = getattr(config, 'FRAME_HEIGHT', 720)
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        # Gradient background for premium feel
        for i in range(h):
            color = int(20 + (i/h)*30)
            frame[i, :] = (color, color, color)
        
        cv2.putText(frame, text, (w // 3, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        res, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        if res:
            self.latest_frame = buffer.tobytes()

monitoring_service = MonitoringService()
