import cv2
import numpy as np
import logging
import threading
import time
import os
from config.config import config

class CameraHandler:
    def __init__(self):
        self.source = config.camera_source
        self.cap = None
        self.frame = None
        self.ret = False
        self.stopped = False
        self.thread = None
        self.use_placeholder = False
        self.open()

    def open(self):
        self.close()
        
        # Apply FFmpeg optimizations
        is_network_stream = str(self.source).startswith(('rtsp://', 'http://', 'https://'))
        if is_network_stream:
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'fflags;nobuffer|flags;low_delay'

        try:
            # Try to see if source is an integer (webcam)
            idx = int(self.source)
            self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(idx)
        except (ValueError, TypeError):
            # Source is a string (RTSP URL or file)
            self.cap = cv2.VideoCapture(self.source)

        if self.cap is not None and self.cap.isOpened():
            if is_network_stream:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.use_placeholder = False
            self.stopped = False
            self.thread = threading.Thread(target=self._update, args=())
            self.thread.daemon = True
            self.thread.start()
            logging.info("Opened camera source %s with threading", self.source)
            return True
        else:
            logging.error("Unable to open camera source %s, using placeholder", self.source)
            self.use_placeholder = True
            return False

    def _update(self):
        """Background thread loop to grab frames"""
        while not self.stopped:
            if self.cap is not None and self.cap.isOpened():
                self.ret, self.frame = self.cap.read()
                if not self.ret:
                    # If it's a video file, loop it
                    if isinstance(self.source, str) and not self.source.startswith('rtsp'):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    else:
                        time.sleep(0.01) # Small sleep to prevent CPU spiking on failed read
            else:
                time.sleep(0.1)

    def read_frame(self):
        """Returns the most recent frame and handles resizing to config dimensions"""
        if self.use_placeholder or self.frame is None:
            return self.get_placeholder_frame()

        # Resize frame to match config
        h = getattr(config, 'FRAME_HEIGHT', 480)
        w = getattr(config, 'FRAME_WIDTH', 640)
        return cv2.resize(self.frame, (w, h))

    def get_placeholder_frame(self):
        w = getattr(config, 'FRAME_WIDTH', 640)
        h = getattr(config, 'FRAME_HEIGHT', 480)
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        text = "Connecting to camera..." if not self.use_placeholder else "Camera unavailable"
        cv2.putText(frame, text, (w // 4, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return frame

    def close(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def stop(self):
        self.close()