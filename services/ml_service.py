"""ML Service - Abstracts card detection pipeline"""
from typing import List, Tuple, Optional
import logging
import numpy as np
from pathlib import Path
from core.domain import DetectedCard

logger = logging.getLogger(__name__)


class MLService:
    """High-level ML detection service"""
    
    def __init__(self, detector=None, classifier=None):
        self.detector = detector
        self.classifier = classifier
        self.is_available = detector is not None and classifier is not None
    
    @classmethod
    def from_weights(cls, yolo_path: str, resnet_path: str, device: str = "cpu"):
        """Factory method to load models from weights"""
        try:
            from ml.detector import TableCardDetector, CardClassifierResNet

            if not Path(yolo_path).exists() or not Path(resnet_path).exists():
                logger.warning("Model weights not found")
                return cls(None, None)

            detector = TableCardDetector(yolo_path, device)
            classifier = CardClassifierResNet(resnet_path, device)

            # Warmup models with dummy inference (important for GPU)
            logger.info("Warming up models...")
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            try:
                _ = detector.predict(dummy_frame, confidence_threshold=0.9)
                dummy_crop = np.zeros((224, 224, 3), dtype=np.uint8)
                _ = classifier.classify_batch([dummy_crop])  # Test batch path
                logger.info("✅ Model warmup completed")
            except Exception as e:
                logger.warning(f"Model warmup failed (non-critical): {e}")

            logger.info("ML models loaded successfully")
            return cls(detector, classifier)

        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            return cls(None, None)
    
    def detect_and_classify(self, frame: np.ndarray, 
                           confidence_threshold: float = 0.4) -> Tuple[List[DetectedCard], List[DetectedCard]]:
        """Detect and classify cards, return (player_cards, board_cards)"""
        
        if not self.is_available:
            logger.warning("ML models not available")
            return [], []
        
        try:
            # Detection
            detections = self.detector.predict(frame, confidence_threshold=confidence_threshold)
            
            # Separate by type
            player_detections = [d for d in detections if d.kind == "player"]
            board_detections = [d for d in detections if d.kind == "board"]
            
            # Classify
            classified_player = self._classify_detections(player_detections, frame)
            classified_board = self._classify_detections(board_detections, frame)
            
            logger.info(f"Detected {len(classified_player)} player, {len(classified_board)} board cards")
            return classified_player, classified_board
            
        except Exception as e:
            logger.error(f"Detection/classification error: {e}")
            return [], []
    
    def _classify_detections(self, detections: List[DetectedCard],
                            frame: np.ndarray) -> List[DetectedCard]:
        """Classify a list of detections using batch inference (5-7x faster)"""
        if not detections:
            return []

        # Extract all crops first
        crops = []
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            crop = frame[y1:y2, x1:x2]
            crops.append(crop)

        # Batch classification - single forward pass for all cards!
        results = self.classifier.classify_batch(crops)

        # Apply results to detections
        classified = []
        for detection, (card_label, confidence) in zip(detections, results):
            if confidence > 0.2 and card_label != "unknown":
                detection.classification = card_label
                classified.append(detection)

        return classified
