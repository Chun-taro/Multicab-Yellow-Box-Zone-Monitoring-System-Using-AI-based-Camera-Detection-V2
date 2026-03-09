import cv2
import numpy as np
from scipy.spatial import distance as dist

class CentroidTracker:
    def __init__(self, max_disappeared=50, max_distance=150):
        self.next_object_id = 0
        self.objects = {}  # Stores {objectID: (centroid, bbox)}
        self.disappeared = {}
        self.kf_trackers = {} # Stores {objectID: KalmanFilter}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance  # Maximum distance for matching (pixels)

    def _init_kalman(self, centroid):
        """Initialize a Kalman Filter for a new object."""
        # state: [x, y, dx, dy]
        kf = cv2.KalmanFilter(4, 2)
        kf.measurementMatrix = np.array([[1,0,0,0], [0,1,0,0]], np.float32)
        kf.transitionMatrix = np.array([[1,0,1,0], [0,1,0,1], [0,0,1,0], [0,0,0,1]], np.float32)
        kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        
        # Initial state
        kf.statePre = np.array([[centroid[0]], [centroid[1]], [0], [0]], np.float32)
        kf.statePost = np.array([[centroid[0]], [centroid[1]], [0], [0]], np.float32)
        return kf

    def register(self, centroid, bbox):
        self.objects[self.next_object_id] = (centroid, bbox)
        self.disappeared[self.next_object_id] = 0
        self.kf_trackers[self.next_object_id] = self._init_kalman(centroid)
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.kf_trackers:
            del self.kf_trackers[object_id]

    def _compute_5_points(self, bbox):
        startX, startY, endX, endY = bbox
        return np.array([
            [startX, startY],                           # Top-Left
            [endX, startY],                             # Top-Right
            [(startX + endX) / 2.0, startY + (endY - startY) * 0.2], # Top-Center (Roof)
            [startX, endY],                             # Bottom-Left
            [endX, endY]                                # Bottom-Right
        ])

    def update(self, rects):
        # 1. Prediction step for all tracked objects
        for obj_id, kf in self.kf_trackers.items():
            prediction = kf.predict()
            
            # If object is disappeared, update its centroid with prediction
            if self.disappeared[obj_id] > 0:
                old_centroid, old_bbox = self.objects[obj_id]
                new_cx, new_cy = int(prediction[0, 0]), int(prediction[1, 0])
                
                # Shift bbox based on prediction movement
                dx = new_cx - old_centroid[0]
                dy = new_cy - old_centroid[1]
                new_bbox = [old_bbox[0] + dx, old_bbox[1] + dy, old_bbox[2] + dx, old_bbox[3] + dy]
                
                self.objects[obj_id] = ((new_cx, new_cy), new_bbox)

        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int(startY + (endY - startY) * 0.2)
            input_centroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i], rects[i])
        else:
            object_ids = list(self.objects.keys())
            
            # Compute distance matrix D based on 5-point tracking anchor matching
            D = np.zeros((len(object_ids), len(rects)))
            
            for row, obj_id in enumerate(object_ids):
                _, obj_bbox = self.objects[obj_id]
                obj_5pts = self._compute_5_points(obj_bbox)
                
                for col, rect in enumerate(rects):
                    rect_5pts = self._compute_5_points(rect)
                    
                    # Calculate Euclidian distances between the 5 corresponding points
                    pt_distances = np.linalg.norm(obj_5pts - rect_5pts, axis=1)
                    
                    # Take average distance of the 2 most stable (closest) points.
                    # This allows the tracker to ignore up to 3 points that jump wildly during occlusion.
                    track_dist = np.mean(np.sort(pt_distances)[:2])
                    
                    D[row, col] = track_dist

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                # Check if the distance is within acceptable threshold
                # This prevents assigning new IDs when vehicle moves too much
                if D[row, col] > self.max_distance:
                    continue
                
                object_id = object_ids[row]
                # Update with the new centroid and bounding box
                self.objects[object_id] = (input_centroids[col], rects[col])
                self.disappeared[object_id] = 0
                
                # Kalman Correction step
                meas = np.array([[input_centroids[col][0]], [input_centroids[col][1]]], np.float32)
                self.kf_trackers[object_id].correct(meas)
                
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    self.register(input_centroids[col], rects[col])

        return self.objects

    def get_current_objects(self):
        """Get current tracked objects without modifying state (useful for frame skipping)."""
        return self.objects

