import cv2
import numpy as np
from scipy.spatial import distance as dist


def compute_iou(boxA, boxB):
    """Compute Intersection over Union (IoU) of two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
    boxBArea = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])
    unionArea = float(boxAArea + boxBArea - interArea)

    if unionArea <= 0:
        return 0.0
    return interArea / unionArea


class CentroidTracker:
    """
    Hybrid IoU + Kalman Filter Tracker (ByteTrack inspired).
    Uses 2-stage Hungarian matching:
      - Stage 1: High-confidence Bounding Box IoU matching.
      - Stage 2: 5-Point Anchor / Centroid Distance matching fallback.
    """
    def __init__(self, max_disappeared=50, max_distance=150, min_iou=0.2):
        self.next_object_id = 0
        self.objects = {}  # Stores {objectID: (centroid, bbox)}
        self.disappeared = {}
        self.kf_trackers = {}  # Stores {objectID: KalmanFilter}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.min_iou = min_iou

    def _init_kalman(self, centroid):
        """Initialize a 2D constant-velocity Kalman Filter for a vehicle."""
        kf = cv2.KalmanFilter(4, 2)
        kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1

        kf.statePre = np.array([[centroid[0]], [centroid[1]], [0], [0]], np.float32)
        kf.statePost = np.array([[centroid[0]], [centroid[1]], [0], [0]], np.float32)
        return kf

    def register(self, centroid, bbox):
        self.objects[self.next_object_id] = (centroid, bbox)
        self.disappeared[self.next_object_id] = 0
        self.kf_trackers[self.next_object_id] = self._init_kalman(centroid)
        self.next_object_id += 1

    def deregister(self, object_id):
        self.objects.pop(object_id, None)
        self.disappeared.pop(object_id, None)
        self.kf_trackers.pop(object_id, None)

    def _compute_5_points(self, bbox):
        startX, startY, endX, endY = bbox
        return np.array([
            [startX, startY],                               # Top-Left
            [endX, startY],                                 # Top-Right
            [(startX + endX) / 2.0, (startY + endY) / 2.0], # Center
            [startX, endY],                                 # Bottom-Left
            [endX, endY]                                    # Bottom-Right
        ])

    def update(self, rects):
        # 1. Kalman Prediction step for all active trackers
        for obj_id, kf in self.kf_trackers.items():
            prediction = kf.predict()
            
            # Predict updated position if missed in recent frame
            if self.disappeared.get(obj_id, 0) > 0:
                old_centroid, old_bbox = self.objects[obj_id]
                new_cx, new_cy = int(prediction[0, 0]), int(prediction[1, 0])
                dx = new_cx - old_centroid[0]
                dy = new_cy - old_centroid[1]
                new_bbox = [old_bbox[0] + dx, old_bbox[1] + dy, old_bbox[2] + dx, old_bbox[3] + dy]
                self.objects[obj_id] = ((new_cx, new_cy), new_bbox)

        # 2. No detections in current frame
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects.copy()

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for i, (startX, startY, endX, endY) in enumerate(rects):
            input_centroids[i] = (int((startX + endX) / 2.0), int((startY + endY) / 2.0))

        # Register all if no existing objects
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i], rects[i])
            return self.objects.copy()

        object_ids = list(self.objects.keys())
        used_rows = set()
        used_cols = set()

        # --- STAGE 1: IoU Matching ---
        iou_matrix = np.zeros((len(object_ids), len(rects)), dtype=np.float32)
        for r, obj_id in enumerate(object_ids):
            _, obj_bbox = self.objects[obj_id]
            for c, rect in enumerate(rects):
                iou_matrix[r, c] = compute_iou(obj_bbox, rect)

        # Greedy IoU matching (highest IoU first)
        sorted_indices = np.unravel_index(np.argsort(-iou_matrix, axis=None), iou_matrix.shape)
        for r, c in zip(sorted_indices[0], sorted_indices[1]):
            if r in used_rows or c in used_cols:
                continue
            if iou_matrix[r, c] < self.min_iou:
                break
            
            obj_id = object_ids[r]
            self.objects[obj_id] = (input_centroids[c], rects[c])
            self.disappeared[obj_id] = 0
            
            # Kalman Correction step
            meas = np.array([[input_centroids[c][0]], [input_centroids[c][1]]], np.float32)
            self.kf_trackers[obj_id].correct(meas)
            
            used_rows.add(r)
            used_cols.add(c)

        # --- STAGE 2: 5-Point Distance Matching Fallback for Unmatched Objects ---
        unmatched_rows = [r for r in range(len(object_ids)) if r not in used_rows]
        unmatched_cols = [c for c in range(len(rects)) if c not in used_cols]

        if unmatched_rows and unmatched_cols:
            dist_matrix = np.zeros((len(unmatched_rows), len(unmatched_cols)), dtype=np.float32)
            for i, r in enumerate(unmatched_rows):
                obj_id = object_ids[r]
                _, obj_bbox = self.objects[obj_id]
                obj_5pts = self._compute_5_points(obj_bbox)

                for j, c in enumerate(unmatched_cols):
                    rect = rects[c]
                    rect_5pts = self._compute_5_points(rect)
                    pt_distances = np.linalg.norm(obj_5pts - rect_5pts, axis=1)
                    dist_matrix[i, j] = np.mean(np.sort(pt_distances)[:2])

            rows = dist_matrix.min(axis=1).argsort()
            cols = dist_matrix.argmin(axis=1)[rows]

            for row_idx, col_idx in zip(rows, cols):
                r = unmatched_rows[row_idx]
                c = unmatched_cols[col_idx]
                if r in used_rows or c in used_cols:
                    continue
                if dist_matrix[row_idx, col_idx] > self.max_distance:
                    continue

                obj_id = object_ids[r]
                self.objects[obj_id] = (input_centroids[c], rects[c])
                self.disappeared[obj_id] = 0

                meas = np.array([[input_centroids[c][0]], [input_centroids[c][1]]], np.float32)
                self.kf_trackers[obj_id].correct(meas)

                used_rows.add(r)
                used_cols.add(c)

        # Handle remaining unmatched objects and new detections
        unused_rows = set(range(len(object_ids))).difference(used_rows)
        unused_cols = set(range(len(rects))).difference(used_cols)

        for r in unused_rows:
            obj_id = object_ids[r]
            self.disappeared[obj_id] += 1
            if self.disappeared[obj_id] > self.max_disappeared:
                self.deregister(obj_id)

        for c in unused_cols:
            self.register(input_centroids[c], rects[c])

        return self.objects.copy()

    def get_current_objects(self):
        """Get current tracked objects without modifying state."""
        return self.objects.copy()


