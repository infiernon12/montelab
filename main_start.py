"""
MonteLab - Advanced Poker Analysis Tool
Main entry point with license validation and UI selection
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QButtonGroup, QRadioButton, QGroupBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('montelab.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UISelectionDialog(QDialog):
    """Dialog for selecting UI mode after license validation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mode = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI selection dialog"""
        self.setWindowTitle("MonteLab - Select Interface")
        self.setFixedSize(500, 350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🎮 Choose Your Interface")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4CAF50; padding: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Select the interface that best suits your workflow:")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #ccc; font-size: 13px; padding: 5px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # UI mode selection group
        mode_group = QGroupBox("Interface Modes")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(15)
        
        self.button_group = QButtonGroup(self)
        
        # Classic mode option
        self.classic_radio = QRadioButton("📊 Classic Mode")
        self.classic_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #fff;
                padding: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        classic_desc = QLabel("Traditional single-window interface with all controls in one view.\nBest for: Single monitor setups, focused analysis")
        classic_desc.setStyleSheet("color: #aaa; font-size: 11px; padding-left: 30px; margin-bottom: 10px;")
        classic_desc.setWordWrap(True)
        
        # Adaptive mode option
        self.adaptive_radio = QRadioButton("🎯 Adaptive Mode")
        self.adaptive_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #fff;
                padding: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        adaptive_desc = QLabel("Modern dockable interface with floating panels and persistent layout.\nBest for: Multi-monitor setups, customizable workspace")
        adaptive_desc.setStyleSheet("color: #aaa; font-size: 11px; padding-left: 30px; margin-bottom: 10px;")
        adaptive_desc.setWordWrap(True)
        
        self.button_group.addButton(self.classic_radio, 1)
        self.button_group.addButton(self.adaptive_radio, 2)
        
        # Set default selection
        self.adaptive_radio.setChecked(True)
        
        mode_layout.addWidget(self.classic_radio)
        mode_layout.addWidget(classic_desc)
        mode_layout.addWidget(self.adaptive_radio)
        mode_layout.addWidget(adaptive_desc)
        
        layout.addWidget(mode_group)
        
        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_btn = QPushButton("🚀 Start MonteLab")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.start_btn.clicked.connect(self.on_start)
        
        self.cancel_btn = QPushButton("❌ Exit")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #777;
            }
            QPushButton:pressed {
                background-color: #555;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1e1e1e;
            }
            QGroupBox::title {
                color: #4CAF50;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
    
    def on_start(self):
        """Handle start button click"""
        if self.classic_radio.isChecked():
            self.selected_mode = "classic"
        else:
            self.selected_mode = "adaptive"
        
        logger.info(f"User selected UI mode: {self.selected_mode}")
        self.accept()
    
    def get_selected_mode(self):
        """Get selected UI mode"""
        return self.selected_mode


def check_license():
    """
    Perform license validation
    Returns: True if valid license, False otherwise
    """
    try:
        from utils.hwid_generator import HWIDGenerator
        from utils.license_client import LicenseClient
        from ui.hwid_dialog import HWIDDialog
        
        # Generate HWID
        hwid = HWIDGenerator.generate_hwid()
        logger.info(f"Generated HWID: {hwid}")
        
        # Initialize license client
        api_url = "https://185.221.196.69:8000/api/v1/"
        secret_key = "28de6a1eb3b9e9edb29c886a43d71964935bd12cb981cc2e604381076d73f6660fdca0a6092ee4b055882859563e7c373472d01d28d0e91cefa810bc1106c572"
        
        license_client = LicenseClient(api_url, secret_key, hwid)
        
        # Check license
        logger.info("Checking license...")
        is_valid = license_client.check_license()
        
        if not is_valid:
            logger.warning("License validation failed - showing HWID dialog")
            
            # Show HWID dialog for user to get license
            hwid_dialog = HWIDDialog()
            result = hwid_dialog.exec()
            
            if result == QDialog.DialogCode.Rejected:
                logger.info("User closed HWID dialog")
                return False
            
            # User may have obtained license - check again
            logger.info("Rechecking license after HWID dialog...")
            is_valid = license_client.check_license()
            
            if not is_valid:
                QMessageBox.critical(
                    None,
                    "License Required",
                    "Valid license not found. Please contact administrator with your HWID.\n\n"
                    "Application will now exit."
                )
                return False
        
        logger.info("License validation successful")
        return True
        
    except Exception as e:
        logger.error(f"License check error: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "License Error",
            f"Failed to validate license:\n{str(e)}\n\nApplication will exit."
        )
        return False


def initialize_services():
    """
    Initialize ML and analysis services
    Returns: (ml_service, analysis_service) or (None, None) on failure
    """
    try:
        from services.ml_service import MLService
        from services.analysis_service import AnalysisService
        from core.poker import EquityCalculator, CppMonteCarloBackend
        
        # Model paths
        script_dir = Path(__file__).parent
        
        yolo_path = script_dir / "models" / "board_player_detector_v4.pt"
        resnet_path = script_dir / "models" / "fine_tuned_resnet_cards_240EPOCH.pt"
        
        # Initialize ML service
        logger.info("Initializing ML service...")
        if yolo_path.exists() and resnet_path.exists():
            ml_service = MLService.from_weights(
                str(yolo_path),
                str(resnet_path),
                device="cpu"
            )
            logger.info("ML service initialized successfully")
        else:
            logger.warning(f"Model files not found: YOLO={yolo_path.exists()}, ResNet={resnet_path.exists()}")
            ml_service = MLService(None, None)
        
        # Initialize Monte Carlo backend
        logger.info("Initializing Monte Carlo backend...")
        try:
            mc_backend = CppMonteCarloBackend()
            equity_calculator = EquityCalculator(backend=mc_backend)
            logger.info("Monte Carlo backend initialized successfully")
        except Exception as e:
            logger.warning(f"Monte Carlo backend unavailable: {e}")
            equity_calculator = EquityCalculator(backend=None)
        
        # Initialize analysis service
        analysis_service = AnalysisService(equity_calculator)
        logger.info("Analysis service initialized successfully")
        
        return ml_service, analysis_service
        
    except Exception as e:
        logger.error(f"Service initialization error: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Initialization Error",
            f"Failed to initialize services:\n{str(e)}\n\nApplication will exit."
        )
        return None, None


def launch_classic_ui(ml_service, analysis_service):
    """Launch classic single-window UI"""
    try:
        from ui.windows.main_window import MainWindow
        
        logger.info("Launching Classic UI...")
        window = MainWindow(ml_service, analysis_service)
        window.show()
        return window
        
    except Exception as e:
        logger.error(f"Failed to launch Classic UI: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "UI Error",
            f"Failed to launch Classic interface:\n{str(e)}"
        )
        return None


def launch_adaptive_ui(ml_service, analysis_service):
    """Launch adaptive dockable UI"""
    try:
        from ui.windows.adaptive_main_window import AdaptiveMainWindow
        
        logger.info("Launching Adaptive UI...")
        window = AdaptiveMainWindow(ml_service, analysis_service)
        window.show()
        return window
        
    except Exception as e:
        logger.error(f"Failed to launch Adaptive UI: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "UI Error",
            f"Failed to launch Adaptive interface:\n{str(e)}"
        )
        return None


def main():
    """Main application entry point"""
    logger.info("=" * 60)
    logger.info("MonteLab - Advanced Poker Analysis Tool")
    logger.info("Starting application...")
    logger.info("=" * 60)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("MonteLab")
    app.setOrganizationName("MonteLab")
    
    # Apply dark theme
    try:
        from ui.styles import apply_dark_theme
        apply_dark_theme(app)
        logger.info("Dark theme applied")
    except Exception as e:
        logger.warning(f"Failed to apply theme: {e}")
    
    # Step 1: License validation
    logger.info("Step 1: License validation")
    if not check_license():
        logger.error("License validation failed - exiting")
        return 1
    
    logger.info("✅ License validation passed")
    
    # Step 2: Initialize services
    logger.info("Step 2: Initializing services")
    ml_service, analysis_service = initialize_services()
    
    if ml_service is None or analysis_service is None:
        logger.error("Service initialization failed - exiting")
        return 1
    
    logger.info("✅ Services initialized")
    
    # Step 3: UI mode selection
    logger.info("Step 3: UI mode selection")
    selection_dialog = UISelectionDialog()
    
    if selection_dialog.exec() != QDialog.DialogCode.Accepted:
        logger.info("User cancelled UI selection - exiting")
        return 0
    
    selected_mode = selection_dialog.get_selected_mode()
    logger.info(f"✅ Selected mode: {selected_mode}")
    
    # Step 4: Launch selected UI
    logger.info(f"Step 4: Launching {selected_mode} UI")
    
    if selected_mode == "classic":
        window = launch_classic_ui(ml_service, analysis_service)
    else:  # adaptive
        window = launch_adaptive_ui(ml_service, analysis_service)
    
    if window is None:
        logger.error("Failed to launch UI - exiting")
        return 1
    
    logger.info("✅ UI launched successfully")
    logger.info("=" * 60)
    logger.info("Application ready - entering event loop")
    logger.info("=" * 60)
    
    # Run application
    exit_code = app.exec()
    
    logger.info("=" * 60)
    logger.info(f"Application exiting with code: {exit_code}")
    logger.info("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Critical Error",
            f"Unhandled exception occurred:\n{str(e)}\n\nApplication will exit."
        )
        sys.exit(1)