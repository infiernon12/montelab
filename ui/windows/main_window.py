"""Main application window - Refactored with service layer - COMPLETE"""
import json
import logging
from pathlib import Path
from typing import Optional, List
import numpy as np
import cv2

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QScrollArea, QMessageBox,
                               QRadioButton, QButtonGroup, QSizePolicy)
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QImage, QPixmap

from core.domain import Card, GameState, GameStage, TableSize, GameType
from services.ml_service import MLService
from services.analysis_service import AnalysisService
from ui.widgets import CardInputWidget, SelectionOverlay
from utils.screen_capture import ScreenCapture

logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    """Main application window with clean separation of concerns"""
    
    def __init__(self, ml_service: MLService, analysis_service: AnalysisService):
        super().__init__()
        self.ml_service = ml_service
        self.analysis_service = analysis_service
        self.screen_capture = ScreenCapture()
        
        self.roi: Optional[QRect] = None
        self.captured_frame: Optional[np.ndarray] = None
        self.game_state = GameState(
            table_size=TableSize.SIX_MAX,
            game_type=GameType.CASH,
            stage=GameStage.PREFLOP,
            player_cards=[],
            board_cards=[]
        )
        
        self.setup_ui()
        self.load_roi()
        
        self.analysis_timer = QTimer(self)
        self.analysis_timer.setSingleShot(True)
        self.analysis_timer.timeout.connect(self.analyze_situation)
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("💜 MonteLab - Refactored 💜")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout = QVBoxLayout(self)
        
        title = QLabel("MonteLab - Advanced Poker Analysis (Refactored)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4CAF50; padding: 15px;")
        main_layout.addWidget(title)
        
        controls = self._create_controls()
        main_layout.addLayout(controls)
        
        self.game_state_label = QLabel("Current Mode: 6-Max Cash | Stage: Preflop")
        self.game_state_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #81C784; padding: 8px;")
        main_layout.addWidget(self.game_state_label)
        
        content = self._create_content_area()
        main_layout.addLayout(content, 1)
        
        self.status_label = QLabel("Ready - Configure and analyze")
        self.status_label.setStyleSheet("color: #888; padding: 8px; background-color: #222; border-radius: 4px;")
        main_layout.addWidget(self.status_label)
    
    def _create_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        
        self.select_roi_btn = QPushButton("🎯 Select Area")
        self.capture_btn = QPushButton("📸 Capture")
        self.analyze_btn = QPushButton("🧠 Analyze")
        
        self.capture_btn.setEnabled(False)
        
        # Apply individual styling with colors
        self.select_roi_btn.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #FF9800;")
        self.capture_btn.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #2196F3;")
        self.analyze_btn.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #4CAF50;")
        
        self.select_roi_btn.clicked.connect(self.select_roi)
        self.capture_btn.clicked.connect(self.capture_and_detect)
        self.analyze_btn.clicked.connect(self.analyze_situation)
        
        layout.addWidget(self.select_roi_btn)
        layout.addWidget(self.capture_btn)
        layout.addWidget(self.analyze_btn)
        layout.addStretch()
        
        return layout
    
    def _create_content_area(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        table_config = self._create_table_config()
        layout.addWidget(table_config)
        
        cards_column = self._create_cards_column()
        layout.addLayout(cards_column)
        
        analysis_frame = self._create_analysis_frame()
        layout.addWidget(analysis_frame, 1)
        
        image_frame = self._create_image_frame()
        layout.addWidget(image_frame)
        
        return layout
    
    def _create_table_config(self) -> QGroupBox:
        frame = QGroupBox("Table Configuration")
        frame.setFixedWidth(180)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        
        self.table_size_group = QButtonGroup()
        table_sizes = [
            ("2_players", "2 игрока", TableSize.HEADS_UP),
            ("3_players", "3 игрока", TableSize.THREE_MAX),
            ("4_players", "4 игрока", TableSize.FOUR_MAX),
            ("5_players", "5 игроков", TableSize.FIVE_MAX),
            ("6_players", "6 игроков", TableSize.SIX_MAX),
            ("7_players", "7 игроков", TableSize.SEVEN_MAX),
            ("8_players", "8 игроков", TableSize.EIGHT_MAX),
            ("9_players", "9 игроков", TableSize.NINE_MAX)
        ]
        
        for btn_id, label, size in table_sizes:
            btn = QRadioButton(label)
            btn.setProperty("table_size", size)
            btn.setStyleSheet("font-size: 11px; padding: 2px;")
            
            if btn_id == "6_players":
                btn.setChecked(True)
            
            self.table_size_group.addButton(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        self.table_size_group.buttonClicked.connect(self.on_table_config_changed)
        
        return frame
    
    def _create_cards_column(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        player_cards_frame = QGroupBox("Player Cards")
        player_cards_frame.setFixedWidth(280)
        player_cards_layout = QVBoxLayout(player_cards_frame)
        player_cards_layout.setSpacing(8)
        
        self.card1_widget = CardInputWidget("Card 1:")
        self.card2_widget = CardInputWidget("Card 2:")
        
        for widget in [self.card1_widget, self.card2_widget]:
            widget.label.setFixedWidth(70)
            widget.line_edit.setFixedWidth(45)
            for btn in widget.suit_buttons:
                btn.setFixedSize(30, 30)
        
        player_cards_layout.addWidget(self.card1_widget)
        player_cards_layout.addWidget(self.card2_widget)
        
        board_cards_frame = QGroupBox("Board Cards")
        board_cards_frame.setFixedWidth(280)
        board_cards_layout = QVBoxLayout(board_cards_frame)
        board_cards_layout.setSpacing(6)
        
        self.flop1_widget = CardInputWidget("Flop 1:")
        self.flop2_widget = CardInputWidget("Flop 2:")
        self.flop3_widget = CardInputWidget("Flop 3:")
        self.turn_widget = CardInputWidget("Turn:")
        self.river_widget = CardInputWidget("River:")
        
        for widget in [self.flop1_widget, self.flop2_widget, self.flop3_widget,
                      self.turn_widget, self.river_widget]:
            widget.label.setFixedWidth(70)
            widget.line_edit.setFixedWidth(45)
            for btn in widget.suit_buttons:
                btn.setFixedSize(30, 30)
        
        board_cards_layout.addWidget(self.flop1_widget)
        board_cards_layout.addWidget(self.flop2_widget)
        board_cards_layout.addWidget(self.flop3_widget)
        board_cards_layout.addWidget(self.turn_widget)
        board_cards_layout.addWidget(self.river_widget)
        
        layout.addWidget(player_cards_frame)
        layout.addWidget(board_cards_frame)
        layout.addStretch()
        
        for widget in [self.card1_widget, self.card2_widget, 
                      self.flop1_widget, self.flop2_widget, self.flop3_widget,
                      self.turn_widget, self.river_widget]:
            widget.line_edit.textChanged.connect(self.on_cards_changed)
        
        return layout
    
    def _create_analysis_frame(self) -> QGroupBox:
        frame = QGroupBox("Poker Analysis")
        frame.setMinimumWidth(350)
        
        layout = QVBoxLayout(frame)
        
        self.analysis_scroll = QScrollArea()
        self.analysis_content = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_content)
        
        self.analysis_scroll.setWidget(self.analysis_content)
        self.analysis_scroll.setWidgetResizable(True)
        
        layout.addWidget(self.analysis_scroll, 1)
        
        self.create_default_analysis()
        
        return frame
    
    def _create_image_frame(self) -> QGroupBox:
        frame = QGroupBox("Captured Image")
        frame.setMinimumWidth(300)
        
        layout = QVBoxLayout(frame)
        
        self.image_label = QLabel("Select area and capture\ntable to detect cards\nautomatically")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(280, 300)
        self.image_label.setStyleSheet("""
            background: #111; color: #ccc; border: 2px solid #444; 
            border-radius: 4px; font-size: 14px; padding: 15px;
        """)
        
        layout.addWidget(self.image_label, 1)
        
        return frame
    
    def create_default_analysis(self):
        while self.analysis_layout.count():
            child = self.analysis_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        welcome_label = QLabel("🃏 Welcome to MonteLab")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; padding: 15px;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        instructions = QLabel("""
        <b>Instructions:</b><br>
        1. Select table configuration<br>
        2. Enter player cards and board cards<br>
        3. OR use ML detection by capturing area<br>
        4. Click 'Analyze' for comprehensive analysis<br><br>
        
        <b>Features:</b><br>
        • Postflop hand strength evaluation<br>
        • Board texture analysis<br>
        • Outs calculations<br>
        • Stage-specific strategy advice
        """)
        instructions.setStyleSheet("color: #ccc; padding: 20px; line-height: 1.6;")
        instructions.setWordWrap(True)
        
        self.analysis_layout.addWidget(welcome_label)
        self.analysis_layout.addWidget(instructions)
        self.analysis_layout.addStretch()
    
    def on_table_config_changed(self):
        checked_btn = self.table_size_group.checkedButton()
        if checked_btn:
            table_size = checked_btn.property("table_size")
            self.game_state.table_size = table_size
            self.update_game_state_display()
            
            if self.has_player_cards():
                self.analyze_situation()
    
    def on_cards_changed(self):
        board_cards = self.get_board_cards()
        self.game_state.board_cards = board_cards
        self.game_state.stage = self._determine_stage(board_cards)
        
        self.update_game_state_display()
        
        if self.has_player_cards():
            self.analysis_timer.stop()
            self.analysis_timer.start(300)
    
    def update_game_state_display(self):
        players_count = self.game_state.get_players_count()
        stage_name = self.game_state.stage.value
        board_count = len(self.game_state.board_cards)
        
        display_text = f"Стол: {players_count} игроков | Стадия: {stage_name} ({board_count} карт)"
        self.game_state_label.setText(display_text)
    
    def has_player_cards(self) -> bool:
        card1 = self.card1_widget.get_text().strip()
        card2 = self.card2_widget.get_text().strip()
        return bool(card1 and card2)
    
    def get_player_cards(self) -> List[Card]:
        cards = []
        for widget in [self.card1_widget, self.card2_widget]:
            text = widget.get_text().strip()
            if text:
                card = Card.parse(text)
                if card:
                    cards.append(card)
        return cards
    
    def get_board_cards(self) -> List[Card]:
        cards = []
        for widget in [self.flop1_widget, self.flop2_widget, self.flop3_widget, 
                      self.turn_widget, self.river_widget]:
            text = widget.get_text().strip()
            if text:
                card = Card.parse(text)
                if card:
                    cards.append(card)
        return cards
    
    def _determine_stage(self, board_cards: List[Card]) -> GameStage:
        num_board = len(board_cards)
        stage_map = {
            0: GameStage.PREFLOP,
            3: GameStage.FLOP,
            4: GameStage.TURN,
            5: GameStage.RIVER
        }
        return stage_map.get(num_board, GameStage.PREFLOP)
    
    def select_roi(self):
        logger.info("ROI selection started")
        try:
            overlay = SelectionOverlay(self)
            overlay.show()
            
            result = overlay.exec()
            
            if result == overlay.DialogCode.Accepted:
                rect = overlay.selected_rect()
                
                if rect and rect.width() > 50 and rect.height() > 50:
                    self.roi = rect
                    self.save_roi()
                    self.capture_btn.setEnabled(True)
                    self.status_label.setText(
                        f"✅ Selected area: {rect.width()}×{rect.height()} at ({rect.x()}, {rect.y()})"
                    )
                    logger.info(f"ROI saved: {rect.width()}x{rect.height()}")
                else:
                    QMessageBox.warning(self, "Selection Too Small", 
                                      "Please select larger area (min 50×50)")
            
        except Exception as e:
            logger.error(f"ROI selection error: {e}", exc_info=True)
            QMessageBox.critical(self, "Selection Error", f"Failed to select region: {e}")
    
    def capture_and_detect(self):
        if not self.roi:
            QMessageBox.warning(self, "No Area", "Please select capture area first")
            return
        
        self.status_label.setText("📸 Capturing and analyzing...")
        
        try:
            frame = self.screen_capture.grab_roi(self.roi)
            if frame is None:
                QMessageBox.warning(self, "Capture Failed", "Failed to capture screenshot")
                self.status_label.setText("❌ Capture failed")
                return
            
            self.captured_frame = frame.copy()
            self.display_frame(frame)
            
            if self.ml_service.is_available:
                self.status_label.setText("🔍 Analyzing cards with ML...")
                self._detect_and_fill_cards(frame)
            else:
                self.status_label.setText("📷 Picture captured - ML not available, enter cards manually")
        
        except Exception as e:
            logger.error(f"Capture error: {e}", exc_info=True)
            QMessageBox.critical(self, "Capture Error", f"Failed to capture: {e}")
            self.status_label.setText("❌ Capture error")
    
    def _detect_and_fill_cards(self, frame: np.ndarray):
        try:
            player_cards, board_cards = self.ml_service.detect_and_classify(frame, confidence_threshold=0.4)
            
            overlay_frame = frame.copy()
            
            for detection in player_cards:
                x1, y1, x2, y2 = detection.bbox
                cv2.rectangle(overlay_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(overlay_frame, f"P: {detection.classification}", (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            for detection in board_cards:
                x1, y1, x2, y2 = detection.bbox
                cv2.rectangle(overlay_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(overlay_frame, f"B: {detection.classification}", (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            self.display_frame(overlay_frame)
            
            if len(player_cards) >= 1:
                self.card1_widget.set_text(player_cards[0].classification or "")
            if len(player_cards) >= 2:
                self.card2_widget.set_text(player_cards[1].classification or "")
            
            board_widgets = [self.flop1_widget, self.flop2_widget, self.flop3_widget,
                           self.turn_widget, self.river_widget]
            
            for i, widget in enumerate(board_widgets):
                if i < len(board_cards):
                    widget.set_text(board_cards[i].classification or "")
                else:
                    widget.clear()
            
            if len(player_cards) >= 2:
                self.analyze_situation()
                self.status_label.setText(
                    f"✅ Detected: {len(player_cards)} player, {len(board_cards)} board cards"
                )
            else:
                self.status_label.setText(
                    f"⚠️ Found {len(player_cards)} player cards - Complete manually"
                )
        
        except Exception as e:
            logger.error(f"Detection error: {e}", exc_info=True)
            self.status_label.setText(f"❌ Detection error")
    
    def display_frame(self, frame: np.ndarray):
        try:
            if len(frame.shape) == 3:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, 
                               QImage.Format.Format_RGB888).rgbSwapped()
            else:
                height, width = frame.shape
                bytes_per_line = width
                q_image = QImage(frame.data, width, height, bytes_per_line, 
                               QImage.Format.Format_Grayscale8)
            
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        
        except Exception as e:
            logger.error(f"Display error: {e}")
    
    def analyze_situation(self):
        if not self.has_player_cards():
            QMessageBox.warning(self, "Input Error", "Please enter both player cards")
            return
        
        try:
            player_cards = self.get_player_cards()
            board_cards = self.get_board_cards()
            
            if len(player_cards) != 2:
                QMessageBox.warning(self, "Invalid Cards", "Please enter valid player cards")
                return
            
            self.game_state.player_cards = player_cards
            self.game_state.board_cards = board_cards
            self.game_state.stage = self._determine_stage(board_cards)
            
            self.update_game_state_display()
            
            analysis_result = self.analysis_service.analyze_hand(self.game_state)
            
            if "error" in analysis_result:
                QMessageBox.warning(self, "Analysis Error", analysis_result["error"])
            else:
                self._display_analysis_result(analysis_result)
            
            self.status_label.setText("✅ Analysis complete")
        
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            QMessageBox.critical(self, "Analysis Error", f"Failed to analyze: {e}")
    
    def _display_analysis_result(self, result: dict):
        while self.analysis_layout.count():
            child = self.analysis_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        stage = result.get("stage", "")
        
        cards_display = " ".join(str(c) for c in self.game_state.player_cards)
        board_display = " ".join(str(c) for c in self.game_state.board_cards) if self.game_state.board_cards else "No board"
        
        title = QLabel(f"Анализ - {stage}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4CAF50; padding: 10px;")
        
        cards_label = QLabel(f"Player: {cards_display} | Board: {board_display}")
        cards_label.setStyleSheet("font-size: 16px; color: #81C784; padding: 8px; font-weight: bold;")
        
        self.analysis_layout.addWidget(title)
        self.analysis_layout.addWidget(cards_label)
        
        if "current_hand" in result:
            strength_group = QGroupBox("Анализ руки")
            strength_layout = QVBoxLayout(strength_group)
            
            current_hand_label = QLabel(f"Текущая комбинация: {result['current_hand']}")
            current_hand_label.setStyleSheet("font-size: 16px; color: #fff; padding: 8px; font-weight: bold;")
            strength_layout.addWidget(current_hand_label)
            
            outs_data = result.get("outs_analysis", {})
            total_outs = result.get("total_outs", 0)
            
            if total_outs >= 0:
                outs_text = f"🎯 АНАЛИЗ АУТОВ:\n"
                outs_text += f"• Флеш: {outs_data.get('flush', 0)} аутов\n"
                outs_text += f"• Стрит: {outs_data.get('straight', 0)} аутов\n"
                outs_text += f"• Сет/Трипс: {outs_data.get('set_trips', 0)} аутов\n"
                outs_text += f"• Оверкарты: {outs_data.get('overcard', 0)} аутов\n"
                outs_text += f"━━━━━━━━━━━━━━━━━━━\n"
                outs_text += f"📊 ВСЕГО АУТОВ: {total_outs}\n\n"
                
                cards_to_come = 5 - len(self.game_state.board_cards)
                if cards_to_come == 2:
                    improvement_equity = min(total_outs * 4, 100)
                    stage_text = "до ривера"
                elif cards_to_come == 1:
                    improvement_equity = min(total_outs * 2, 100)
                    stage_text = "на ривере"
                else:
                    improvement_equity = 0
                    stage_text = "завершен"
                
                outs_text += f"📈 Шанс улучшения {stage_text}: {improvement_equity:.2f}%\n"
                
                equity = result.get("equity", {})
                if "win_rate" in equity and not equity.get("error"):
                    outs_text += f"\n🏆 ВЕРОЯТНОСТЬ ПОБЕДЫ:\n"
                    outs_text += f"• Победа: {equity.get('win_rate', 0):.2f}%\n"
                    outs_text += f"• Ничья: {equity.get('tie_rate', 0):.2f}%\n"
                    outs_text += f"• Поражение: {equity.get('lose_rate', 0):.2f}%"
            else:
                outs_text = "❌ Значимых дро не обнаружено"
            
            outs_label = QLabel(outs_text)
            outs_label.setStyleSheet("font-size: 14px; color: #ccc; padding: 8px; font-family: 'Consolas';")
            outs_label.setWordWrap(True)
            strength_layout.addWidget(outs_label)
            
            self.analysis_layout.addWidget(strength_group)
        
        texture = result.get("board_texture", {})
        if texture and "error" not in texture:
            texture_group = QGroupBox("Текстура доски")
            texture_layout = QVBoxLayout(texture_group)
            
            features = []
            if texture.get('monotone'):
                features.append("🔴 Монотон")
            elif texture.get('two_tone'):
                features.append("🟡 Двухцветная")
            elif texture.get('rainbow'):
                features.append("🌈 Радужная")
            
            if texture.get('paired'):
                features.append("👥 Спаренная")
            
            if texture.get('coordinated'):
                features.append("🔗 Скоординированная")
            elif texture.get('dry'):
                features.append("🏜️ Сухая")
            
            if texture.get('flush_draw'):
                features.append("💧 Флеш-дро")
            
            texture_text = "Характеристики:\n" + "\n".join(f"• {f}" for f in features) if features else "Стандартная"
            
            texture_label = QLabel(texture_text)
            texture_label.setStyleSheet("font-size: 14px; color: #ccc; padding: 8px;")
            texture_label.setWordWrap(True)
            texture_layout.addWidget(texture_label)
            
            self.analysis_layout.addWidget(texture_group)
        
        strategy = result.get("strategy_recommendation", "")
        if strategy:
            recommendations_group = QGroupBox("ABC Рекомендации")
            recommendations_layout = QVBoxLayout(recommendations_group)
            
            strategy_label = QLabel(f"🎯 {strategy}")
            strategy_label.setStyleSheet("""
                font-size: 16px; color: #FFD700; padding: 15px; font-weight: bold; 
                border: 2px solid #FFD700; border-radius: 8px; background-color: rgba(255, 215, 0, 0.1);
            """)
            strategy_label.setWordWrap(True)
            recommendations_layout.addWidget(strategy_label)
            
            self.analysis_layout.addWidget(recommendations_group)
        
        self.analysis_layout.addStretch()
    
    def save_roi(self):
        if self.roi:
            roi_data = [self.roi.x(), self.roi.y(), self.roi.width(), self.roi.height()]
            config_data = {"roi": roi_data}
            try:
                config_file = Path(__file__).parent.parent.parent / "gui_config.json"
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                logger.info(f"ROI saved: {roi_data}")
            except Exception as e:
                logger.error(f"Failed to save ROI: {e}")
    
    def load_roi(self):
        config_file = Path(__file__).parent.parent.parent / "gui_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                roi_data = data.get('roi')
                if roi_data and len(roi_data) == 4:
                    self.roi = QRect(*roi_data)
                    self.capture_btn.setEnabled(True)
                    self.status_label.setText(f"📁 Loaded saved area: {roi_data[2]}×{roi_data[3]}")
            except Exception as e:
                logger.warning(f"Failed to load ROI: {e}")
    
    def clear_all_inputs(self):
        """Clear all card input widgets"""
        self.card1_widget.clear()
        self.card2_widget.clear()
        self.flop1_widget.clear()
        self.flop2_widget.clear()
        self.flop3_widget.clear()
        self.turn_widget.clear()
        self.river_widget.clear()
        
        self.game_state.player_cards = []
        self.game_state.board_cards = []
        self.game_state.stage = GameStage.PREFLOP
        
        self.update_game_state_display()
        self.create_default_analysis()
        self.status_label.setText("🔄 All inputs cleared")
        logger.info("All inputs cleared")
    
    def closeEvent(self, event):
        logger.info("Application closing")
        event.accept()
