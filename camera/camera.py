import cv2
import threading
import time
from config.config import config

class CameraHandler:
    def __init__(self, source=None):
        if source is None:
            self.source = config.camera_source
        else:
            self.source = source
        self.cap = None
        self.frame = None
        self.ret = False
        self.stopped = False
        self.thread = None
        self.use_placeholder = False

    def start(self):
        # Set buffer size to 1 to reduce latency
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            self.use_placeholder = True
            return
            
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Optionally set internal dimensions if camera supports it
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        
        self.stopped = False
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True
        self.thread.start()

    def _update(self):
        """Background thread to continuously grab frames"""
        while not self.stopped:
            if self.cap is not None and self.cap.isOpened():
                self.ret, self.frame = self.cap.read()
            else:
                self.ret = False
                time.sleep(0.1)

    def read_frame(self):
        """Returns the most recent frame captured by the thread"""
        if self.use_placeholder:
            return None
        return self.frame

    def stop(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
