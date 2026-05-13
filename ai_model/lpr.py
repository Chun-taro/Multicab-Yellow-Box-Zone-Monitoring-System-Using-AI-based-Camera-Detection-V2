"""
License Plate Recognition (LPR) module using EasyOCR.
Reads text from a cropped vehicle image region and returns a cleaned plate number.
"""
import re
import logging

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not installed. LPR will be disabled. Run: pip install easyocr")


class LicensePlateReader:
    """
    Wraps EasyOCR to extract license plate text from a vehicle crop.
    Initialized lazily to avoid delaying system startup.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reader = None
            cls._instance._ready = False
        return cls._instance

    def initialize(self):
        """Load the EasyOCR model (call this in a background thread)."""
        if not EASYOCR_AVAILABLE:
            return
        if self._ready:
            return
        try:
            # English reader, GPU enabled
            self._reader = easyocr.Reader(['en'], gpu=True, verbose=False)
            self._ready = True
            logging.info("✓ LPR (EasyOCR) model loaded and ready.")
        except Exception as e:
            logging.error(f"LPR failed to initialize: {e}")

    def read_plate(self, frame_crop):
        """
        Read license plate text from a cropped image frame.

        Args:
            frame_crop: numpy array of the cropped region (vehicle bbox, lower half)

        Returns:
            str: Cleaned plate number (e.g. 'ABC1234') or None if unreadable.
        """
        if not self._ready or self._reader is None:
            return None
        if frame_crop is None or frame_crop.size == 0:
            return None

        try:
            results = self._reader.readtext(frame_crop, detail=0, paragraph=False)
            if not results:
                return None

            # Combine all detected text segments
            raw_text = ' '.join(results).upper().strip()

            # Clean: keep only alphanumeric characters
            cleaned = re.sub(r'[^A-Z0-9]', '', raw_text)

            # Validate: Philippine plates are typically 3 letters + 3-4 digits (e.g. ABC1234)
            # Accept any result between 3 and 10 characters
            if 3 <= len(cleaned) <= 10:
                return cleaned

            return None
        except Exception as e:
            logging.warning(f"LPR read error: {e}")
            return None


def crop_plate_region(frame, bbox):
    """
    Crop the lower portion of a vehicle bounding box where the plate is likely located.

    Args:
        frame: Full video frame (numpy array)
        bbox: (x1, y1, x2, y2) vehicle bounding box

    Returns:
        numpy array: Cropped plate region
    """
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]

    # Use bottom 40% of vehicle bbox (plate zone)
    plate_y1 = int(y1 + (y2 - y1) * 0.6)
    plate_y2 = min(y2 + 10, h)  # Slight overshoot to catch low-mounted plates
    plate_x1 = max(0, x1 - 5)
    plate_x2 = min(w, x2 + 5)

    if plate_y1 >= plate_y2 or plate_x1 >= plate_x2:
        return None

    return frame[plate_y1:plate_y2, plate_x1:plate_x2]


# Singleton instance
lpr_reader = LicensePlateReader()
