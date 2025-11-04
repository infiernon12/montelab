import logging
from pathlib import Path
from typing import List, Tuple
import numpy as np
import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import resnet34
from ultralytics import YOLO

import torch.nn.functional as F
from core.domain import DetectedCard

logger = logging.getLogger(__name__)

class TableCardDetector:
    """YOLO-based card detection with separate zones for player and board cards"""
    
    def __init__(self, weights_path: str, device: str = "cpu"):
        self.device = device
        self.weights_path = weights_path
        logger.info(f"Loading card detector from {weights_path}")
        
        if not Path(weights_path).exists():
            raise FileNotFoundError(f"Model weights not found: {weights_path}")
        
        self.model = YOLO(weights_path)
        self.model.to(device)
        logger.info("Card detector loaded successfully")
    
    def predict(self, frame: np.ndarray, confidence_threshold: float = 0.6) -> List[DetectedCard]:
        """Detect cards with separate optimization for player and board cards"""
        if frame is None or frame.size == 0:
            return []
        
        try:
            results = self.model(frame, verbose=False, conf=confidence_threshold, iou=0.5)
            all_detections = []
            
            frame_height, frame_width = frame.shape[:2]
            
            for result in results:
                if not hasattr(result, 'boxes') or result.boxes is None:
                    continue
                
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    if confidence < confidence_threshold:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cls_id = int(box.cls[0])
                    
                    if x2 <= x1 or y2 <= y1:
                        continue
                    if (x2 - x1) < 20 or (y2 - y1) < 30:
                        continue
                    
                    if x1 < 0 or y1 < 0 or x2 >= frame_width or y2 >= frame_height:
                        continue
                    
                    kind_raw = self.model.names.get(cls_id, "unknown")
                    kind = self._map_class_name(kind_raw)
                    
                    if kind == "unknown":
                        continue
                    
                    detection = DetectedCard(
                        bbox=(x1, y1, x2, y2),
                        kind=kind,
                        score=confidence
                    )
                    all_detections.append(detection)
            
            optimized_detections = self._optimize_card_detections(all_detections, frame_height, frame_width)
            
            logger.info(f"Detected {len(optimized_detections)} cards after optimization")
            return optimized_detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def _optimize_card_detections(self, detections: List[DetectedCard], 
                                frame_height: int, frame_width: int) -> List[DetectedCard]:
        player_cards = [d for d in detections if d.kind == "player"]
        board_cards = [d for d in detections if d.kind == "board"]
        
        optimized_player_cards = self._optimize_player_cards(player_cards, frame_height, frame_width)
        optimized_board_cards = self._optimize_board_cards(board_cards, frame_height, frame_width)
        
        return optimized_player_cards + optimized_board_cards
    
    def _optimize_player_cards(self, player_cards: List[DetectedCard], 
                             frame_height: int, frame_width: int) -> List[DetectedCard]:
        if not player_cards:
            return []
        
        bottom_zone_start = int(frame_height * 0.6)
        center_zone_left = int(frame_width * 0.2)
        center_zone_right = int(frame_width * 0.8)
        
        filtered_cards = []
        
        for card in player_cards:
            x1, y1, x2, y2 = card.bbox
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            in_bottom_zone = center_y >= bottom_zone_start
            in_center_zone = center_zone_left <= center_x <= center_zone_right
            not_too_high = center_y >= int(frame_height * 0.4)
            
            if in_bottom_zone or (in_center_zone and not_too_high):
                filtered_cards.append(card)
        
        if len(filtered_cards) > 2:
            filtered_cards = sorted(filtered_cards, key=lambda x: x.score, reverse=True)[:2]
        
        return filtered_cards
    
    def _optimize_board_cards(self, board_cards: List[DetectedCard], 
                            frame_height: int, frame_width: int) -> List[DetectedCard]:
        if not board_cards:
            return []
        
        center_zone_top = int(frame_height * 0.2)
        center_zone_bottom = int(frame_height * 0.7)
        center_zone_left = int(frame_width * 0.15)
        center_zone_right = int(frame_width * 0.85)
        
        filtered_cards = []
        
        for card in board_cards:
            x1, y1, x2, y2 = card.bbox
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            in_vertical_zone = center_zone_top <= center_y <= center_zone_bottom
            in_horizontal_zone = center_zone_left <= center_x <= center_zone_right
            
            if in_vertical_zone and in_horizontal_zone:
                filtered_cards.append(card)
        
        if len(filtered_cards) > 5:
            filtered_cards = sorted(filtered_cards, key=lambda x: x.score, reverse=True)[:5]
        
        filtered_cards = sorted(filtered_cards, key=lambda x: (x.bbox[0] + x.bbox[2]) // 2)
        
        return filtered_cards
    
    def _map_class_name(self, raw_name: str) -> str:
        name_mapping = {
            "BoardCard": "board",
            "PlayerCard": "player", 
            "board_card": "board",
            "player_card": "player",
            "Board": "board",
            "Player": "player"
        }
        return name_mapping.get(raw_name, raw_name.lower())

class CardClassifierResNet:
    """ResNet-based card classification"""
    
    def __init__(self, weights_path: str, device: str = "cpu"):
        self.device = device
        self.weights_path = weights_path
        logger.info(f"Loading card classifier from {weights_path}")
        
        if not Path(weights_path).exists():
            raise FileNotFoundError(f"Model weights not found: {weights_path}")
        
        self._load_model()
        self._setup_transforms()
        logger.info("Card classifier loaded successfully")
    
    def _load_model(self):
        checkpoint = torch.load(self.weights_path, map_location=self.device)
        
        try:
            from torchvision.models import ResNet34_Weights
            self.model = resnet34(weights=None)
        except ImportError:
            self.model = resnet34(pretrained=False)
        
        num_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 52)
        )
        
        if isinstance(checkpoint, dict):
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            elif 'state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
        else:
            self.model = checkpoint
        
        self.model.to(self.device)
        self.model.eval()
        
        self.class_names = [
            "ace of clubs", "ace of diamonds", "ace of hearts", "ace of spades",
            "eight of clubs", "eight of diamonds", "eight of hearts", "eight of spades",
            "five of clubs", "five of diamonds", "five of hearts", "five of spades",
            "four of clubs", "four of diamonds", "four of hearts", "four of spades",
            "jack of clubs", "jack of diamonds", "jack of hearts", "jack of spades",
            "king of clubs", "king of diamonds", "king of hearts", "king of spades",
            "nine of clubs", "nine of diamonds", "nine of hearts", "nine of spades",
            "queen of clubs", "queen of diamonds", "queen of hearts", "queen of spades",
            "seven of clubs", "seven of diamonds", "seven of hearts", "seven of spades",
            "six of clubs", "six of diamonds", "six of hearts", "six of spades",
            "ten of clubs", "ten of diamonds", "ten of hearts", "ten of spades",
            "three of clubs", "three of diamonds", "three of hearts", "three of spades",
            "two of clubs", "two of diamonds", "two of hearts", "two of spades"
        ]
    
    def _setup_transforms(self):
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def classify_crop(self, crop: np.ndarray) -> Tuple[str, float]:
        if crop is None or crop.size == 0:
            return "unknown", 0.0
        
        try:
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            tensor = self.transform(crop_rgb).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                output = self.model(tensor)
                probs = F.softmax(output, dim=1)
                confidence, index = torch.max(probs, dim=1)
            
            class_idx = index.item()
            confidence_score = confidence.item()
            
            if 0 <= class_idx < len(self.class_names):
                raw_label = self.class_names[class_idx]
                card_label = self._map_class_to_card(raw_label)
                return card_label, confidence_score
            
            return "unknown", confidence_score
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return "unknown", 0.0
    
    def _map_class_to_card(self, raw_label: str) -> str:
        name_mapping = {
            "ace of clubs": "Ac", "ace of diamonds": "Ad", "ace of hearts": "Ah", "ace of spades": "As",
            "king of clubs": "Kc", "king of diamonds": "Kd", "king of hearts": "Kh", "king of spades": "Ks",
            "queen of clubs": "Qc", "queen of diamonds": "Qd", "queen of hearts": "Qh", "queen of spades": "Qs",
            "jack of clubs": "Jc", "jack of diamonds": "Jd", "jack of hearts": "Jh", "jack of spades": "Js",
            "ten of clubs": "Tc", "ten of diamonds": "Td", "ten of hearts": "Th", "ten of spades": "Ts",
            "nine of clubs": "9c", "nine of diamonds": "9d", "nine of hearts": "9h", "nine of spades": "9s",
            "eight of clubs": "8c", "eight of diamonds": "8d", "eight of hearts": "8h", "eight of spades": "8s",
            "seven of clubs": "7c", "seven of diamonds": "7d", "seven of hearts": "7h", "seven of spades": "7s",
            "six of clubs": "6c", "six of diamonds": "6d", "six of hearts": "6h", "six of spades": "6s",
            "five of clubs": "5c", "five of diamonds": "5d", "five of hearts": "5h", "five of spades": "5s",
            "four of clubs": "4c", "four of diamonds": "4d", "four of hearts": "4h", "four of spades": "4s",
            "three of clubs": "3c", "three of diamonds": "3d", "three of hearts": "3h", "three of spades": "3s",
            "two of clubs": "2c", "two of diamonds": "2d", "two of hearts": "2h", "two of spades": "2s"
        }
        
        return name_mapping.get(raw_label.lower(), raw_label)
