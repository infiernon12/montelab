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
        """Classify a list of detections"""
        classified = []
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            crop = frame[y1:y2, x1:x2]
            
            if crop.size > 0:
                card_label, confidence = self.classifier.classify_crop(crop)
                if confidence > 0.2:
                    detection.classification = card_label
                    classified.append(detection)
        
        return classified
