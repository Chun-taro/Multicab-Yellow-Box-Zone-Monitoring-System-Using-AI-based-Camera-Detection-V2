"""
License Plate Recognition (LPR) module using EasyOCR.
Enhanced 2-Stage Pipeline: Image Preprocessing + OCR with Philippine Plate Pattern Validation.
"""
import re
import logging
import cv2
import numpy as np

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not installed. LPR will be disabled. Run: pip install easyocr")


def preprocess_plate_crop(crop):
    """
    Stage 1: Preprocess plate region using CLAHE, Bilateral Filter, and Bilinear Upscaling
    to enhance text contrast and character edges for OCR.
    """
    if crop is None or crop.size == 0:
        return None

    # Convert to grayscale
    if len(crop.shape) == 3:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop

    # Upscale small crops for better OCR recognition
    h, w = gray.shape[:2]
    if w < 120 or h < 40:
        gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    # Bilateral filter to reduce image noise while keeping sharp edges
    denoised = cv2.bilateralFilter(gray, 11, 17, 17)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    return enhanced


def validate_philippine_plate(text):
    """
    Stage 2: Validate extracted plate string against Philippine LTO registration patterns.
    Standard formats:
      - 3 letters + 3-4 numbers (e.g. ABC 1234, NGA 543)
      - 2 letters + 4-5 numbers (Motorcycles / Commercial: AB 12345)
      - 4 numbers + 2 letters (Special plates: 1234 AB)
    """
    if not text:
        return None

    # Clean non-alphanumeric characters
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())

    if len(cleaned) < 3 or len(cleaned) > 10:
        return None

    # Strict Philippine plate regex matches
    ph_patterns = [
        r'^[A-Z]{3}\d{3,4}$',   # Standard Private/Public Vehicles: ABC1234 or ABC123
        r'^[A-Z]{2}\d{4,5}$',   # Commercial / Motorcycles: AB12345
        r'^\d{4}[A-Z]{2}$',     # Government / Special Series: 1234AB
        r'^[A-Z]\d{5,6}$',      # Vintage / Fleet: A123456
    ]

    for pattern in ph_patterns:
        if re.match(pattern, cleaned):
            return cleaned

    # Generic Fallback: length between 4 and 8 alphanumeric characters
    if 4 <= len(cleaned) <= 8 and any(c.isalpha() for c in cleaned) and any(c.isdigit() for c in cleaned):
        return cleaned

    return None


class LicensePlateReader:
    """
    Wraps EasyOCR to extract license plate text from vehicle crops.
    Initialized lazily in a background thread to avoid delaying startup.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reader = None
            cls._instance._ready = False
        return cls._instance

    def initialize(self):
        """Load the EasyOCR model (call this in background thread)."""
        if not EASYOCR_AVAILABLE or self._ready:
            return
        try:
            # English reader with GPU detection
            import torch
            use_gpu = torch.cuda.is_available()
            self._reader = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)
            self._ready = True
            logging.info(f"✓ LPR (EasyOCR) model loaded and ready (GPU Enabled: {use_gpu}).")
        except Exception as e:
            logging.error(f"LPR failed to initialize: {e}")

    def read_plate(self, frame_crop):
        """
        Read license plate text from a cropped vehicle region using 2-stage enhancement.

        Args:
            frame_crop: numpy array of the cropped vehicle region

        Returns:
            str: Validated plate number (e.g. 'ABC1234') or None if unreadable.
        """
        if not self._ready or self._reader is None:
            return None
        if frame_crop is None or frame_crop.size == 0:
            return None

        # Pass 1: Try direct OCR on raw crop
        try:
            results = self._reader.readtext(frame_crop, detail=0, paragraph=False)
            if results:
                raw_text = ' '.join(results).upper().strip()
                validated = validate_philippine_plate(raw_text)
                if validated:
                    return validated
        except Exception as e:
            logging.debug(f"Pass 1 LPR failed: {e}")

        # Pass 2: Try OCR on CLAHE enhanced + denoised crop
        try:
            enhanced_crop = preprocess_plate_crop(frame_crop)
            if enhanced_crop is not None:
                results_enhanced = self._reader.readtext(enhanced_crop, detail=0, paragraph=False)
                if results_enhanced:
                    raw_text_enh = ' '.join(results_enhanced).upper().strip()
                    validated_enh = validate_philippine_plate(raw_text_enh)
                    if validated_enh:
                        return validated_enh
        except Exception as e:
            logging.warning(f"Pass 2 LPR read error: {e}")

        return None


def crop_plate_region(frame, bbox):
    """
    Crop lower 40% region of vehicle bounding box where license plate is positioned.

    Args:
        frame: Full video frame (numpy array)
        bbox: (x1, y1, x2, y2) vehicle bounding box

    Returns:
        numpy array: Cropped plate region
    """
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]

    # Use bottom 40% of vehicle bbox
    plate_y1 = int(y1 + (y2 - y1) * 0.6)
    plate_y2 = min(y2 + 10, h)
    plate_x1 = max(0, x1 - 5)
    plate_x2 = min(w, x2 + 5)

    if plate_y1 >= plate_y2 or plate_x1 >= plate_x2:
        return None

    return frame[plate_y1:plate_y2, plate_x1:plate_x2]


# Singleton instance
lpr_reader = LicensePlateReader()

