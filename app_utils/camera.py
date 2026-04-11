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
        self._lock = threading.Lock()
        self.open()

    def open(self):
        with self._lock:
            # If already opening the SAME source, don't start a duplicate thread
            if hasattr(self, '_opening_source') and self._opening_source == self.source and self._is_opening:
                return False
            
            self.close_internal()
            self._is_opening = True
            self._opening_source = self.source
            self.stopped = False
            self.use_placeholder = False # Reset to show "Connecting..." feedback
            
            # Start connection in a background thread to avoid blocking the main app
            self._connection_thread = threading.Thread(target=self._establish_connection, daemon=True)
            self._connection_thread.start()
            return True

    def _establish_connection(self):
        """Internal method to establish camera connection without blocking."""
        source = self.source
        
        # Apply FFmpeg optimizations ONLY for network streams
        is_network_stream = str(source).startswith(('rtsp://', 'http://', 'https://'))
        if is_network_stream:
            # Optimized flags: avoid huge buffers for real-time latency
            # stimeout;5000000 sets a 5-second timeout for the connection (in microseconds)
            # Use tcp transport for faster error detection and more reliable handshake
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|timeout;5000000|stimeout;5000000'
            os.environ['OPENCV_VIDEOIO_FFMPEG_TIMEOUT_MS'] = '5000'
            os.environ['OPENCV_FFMPEG_READ_TIMEOUT_MS'] = '5000'
        else:
            # CLEAR options for local files or webcams to ensure system defaults
            os.environ.pop('OPENCV_FFMPEG_CAPTURE_OPTIONS', None)
            os.environ.pop('OPENCV_VIDEOIO_FFMPEG_TIMEOUT_MS', None)
            os.environ.pop('OPENCV_FFMPEG_READ_TIMEOUT_MS', None)

        cap = None
        try:
            # Try to see if source is an integer (webcam)
            idx = int(source)
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(idx)
        except (ValueError, TypeError):
            # Source is a string (RTSP URL or file)
            # Use FFMPEG backend for reliability if available, fallback to ANY
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            if not cap or not cap.isOpened():
                 cap = cv2.VideoCapture(source)

        with self._lock:
            # Verify if this is still the source the user wants (handles rapid switching)
            if self._opening_source != source:
                logging.info("Source changed during connection, discarding stale cap for %s", source)
                if cap:
                    cap.release()
                return

            self._is_opening = False
            if cap is not None and cap.isOpened():
                # Success
                if is_network_stream:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                self.cap = cap
                
                # Detect original FPS or use default for timing
                self.original_fps = cap.get(cv2.CAP_PROP_FPS)
                if self.original_fps <= 0 or self.original_fps > 120:
                    self.original_fps = getattr(config, 'FPS', 30)
                
                self.use_placeholder = False
                self.frame = None
                self.ret = False
                self.thread = threading.Thread(target=self._update, args=())
                self.thread.daemon = True
                self.thread.start()
                logging.info("✓ Successfully connected to camera source: %s (FPS: %s)", source, self.original_fps)
            else:
                # Failure
                logging.error("✗ Unable to open camera source %s after timeout", source)
                self.use_placeholder = True
                if cap:
                    cap.release()

    def _update(self):
        """Background thread loop to grab frames at correct speed"""
        # Determine if we need manual timing (files/images vs live streams)
        is_video_file = isinstance(self.source, str) and not self.source.startswith(('rtsp', 'http'))
        frame_delay = 1.0 / self.original_fps if is_video_file else 0
        
        while not self.stopped:
            if self.cap is not None and self.cap.isOpened():
                start_time = time.time()
                self.ret, self.frame = self.cap.read()
                
                if self.ret:
                    if is_video_file:
                        # For files, we must manually manage the timing
                        elapsed = time.time() - start_time
                        sleep_time = max(0, frame_delay - elapsed)
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                else:
                    # If it's a video file, loop it
                    if is_video_file:
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

    def close_internal(self):
        """Internal close method without lock acquisition"""
        self.stopped = True
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def close(self):
        with self._lock:
            self.close_internal()

    def stop(self):
        self.close()