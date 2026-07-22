import os
import logging

try:
    import torch
    from ultralytics import YOLO
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False


class VehicleDetector:
    """
    Optimized YOLOv8 Vehicle Detector with GPU auto-detection,
    FP16 half-precision support, and fallback capabilities.
    """
    def __init__(self, model_path, conf_thres=0.5):
        if not TORCH_AVAILABLE:
            raise ImportError("Ultralytics/PyTorch not available. Install via 'pip install ultralytics torch'")
        
        self.conf_thres = conf_thres
        self.model_path = model_path
        
        # Detect CUDA GPU availability
        if torch.cuda.is_available():
            self.device = 0
            self.half = True
            logging.info(f"✓ AI Detector using GPU (CUDA: {torch.cuda.get_device_name(0)}) with FP16 half precision")
        else:
            self.device = 'cpu'
            self.half = False
            logging.info("ℹ AI Detector using CPU mode")

        # Load YOLO model
        self.model = YOLO(self.model_path)
        
        # Warmup model
        try:
            self.model.to(self.device)
        except Exception as e:
            logging.warning(f"Could not move model to {self.device}: {e}. Defaulting to CPU.")
            self.device = 'cpu'
            self.half = False

    def detect(self, frame):
        """
        Perform vehicle and person detection on a single video frame.
        
        Args:
            frame (numpy.ndarray): Input BGR image frame
            
        Returns:
            list[dict]: List of detection dictionaries with 'bbox', 'confidence', and 'class'
        """
        if frame is None or frame.size == 0:
            return []

        # Inference with YOLOv8
        # iou=0.3 & agnostic_nms=True prevent double-bounding boxes for overlapping classes (e.g. truck + car)
        results = self.model(
            frame, 
            conf=self.conf_thres, 
            iou=0.3, 
            agnostic_nms=True, 
            verbose=False, 
            imgsz=640,
            device=self.device,
            half=self.half if self.device != 'cpu' else False
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
            
            xyxy_arr = boxes.xyxy.cpu().numpy()
            conf_arr = boxes.conf.cpu().numpy()
            cls_arr = boxes.cls.cpu().numpy()

            for i in range(len(boxes)):
                detections.append({
                    'bbox': [int(x) for x in xyxy_arr[i]],
                    'confidence': float(conf_arr[i]),
                    'class': int(cls_arr[i])
                })
        return detections

