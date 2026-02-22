import cv2
import numpy as np
from scipy.spatial import distance as dist

class CentroidTracker:
    def __init__(self, max_disappeared=50, max_distance=150):
        self.next_object_id = 0
        self.objects = {}  # Stores {objectID: (centroid, bbox)}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance  # Maximum distance for matching (pixels)

    def register(self, centroid, bbox):
        self.objects[self.next_object_id] = (centroid, bbox)
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]

    def _compute_5_points(self, bbox):
        startX, startY, endX, endY = bbox
        return np.array([
            [startX, startY],                           # Top-Left
            [endX, startY],                             # Top-Right
            [(startX + endX) / 2.0, (startY + endY) / 2.0], # Center
            [startX, endY],                             # Bottom-Left
            [endX, endY]                                # Bottom-Right
        ])

    def update(self, rects):
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
