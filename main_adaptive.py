"""Main application entry point - With Adaptive UI"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from utils.hwid_generator import HWIDGenerator
from utils.license_client import LicenseClient
from ui.hwid_dialog import HWIDDialog

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_license(app):
    """Check license before starting application"""
    try:
        # Generate HWID
        hwid = HWIDGenerator.generate_hwid()
        logger.info(f"Generated HWID: {hwid}")
        
        # Initialize license client
        hmac_secret = "super-secure-hmac-key-for-production-change-this-immediately"
        license_client = LicenseClient(
            api_base_url="https://85.239.147.227/api/v1/",
            hmac_secret_key=hmac_secret,
            hwid=hwid
        )
        
        # Check license
        logger.info("Checking license...")
        is_licensed = license_client.check_license()
        
        if not is_licensed:
            logger.warning("⚠️ License not active")
            # Show HWID dialog
            dialog = HWIDDialog()
            dialog.exec()
            return False
        
        logger.info("✅ License verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"License check failed: {e}")
        # Show error message
        QMessageBox.critical(
            None,
            "Ошибка лицензии",
            f"Не удалось проверить лицензию:\n{str(e)}\n\nПриложение будет закрыто."
        )
        return False


def main():
    """Application entry point"""
    logger.info("=" * 60)
    logger.info("MonteLab - Adaptive UI Version")
    logger.info("=" * 60)
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MonteLab")
        app.setApplicationVersion("2.0-Adaptive")
        
        # Check license before proceeding
        if not check_license(app):
            logger.info("Application terminated: License not verified")
            return 1
        
        # Apply dark theme
        app.setStyle("Fusion")
        from ui.styles import apply_dark_theme
        apply_dark_theme(app)
        
        # Initialize services
        from services.ml_service import MLService
        from core.poker import EquityCalculator, CppMonteCarloBackend
        from services.analysis_service import AnalysisService
        
        # Load ML models
        script_dir = Path(__file__).parent
        yolo_path = script_dir / "models" / "board_player_detector_v4.pt"
        resnet_path = script_dir / "models" / "fine_tuned_resnet_cards_240EPOCH.pt"
        
        ml_service = MLService.from_weights(str(yolo_path), str(resnet_path), "cpu")
        
        # Initialize Monte Carlo backend
        try:
            monte_carlo_backend = CppMonteCarloBackend()
            equity_calculator = EquityCalculator(backend=monte_carlo_backend)
            logger.info("✅ Monte Carlo backend initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️  Monte Carlo backend unavailable: {e}")
            equity_calculator = EquityCalculator(backend=None)
        
        analysis_service = AnalysisService(equity_calculator)
        
        # Create adaptive main window
        from ui.windows.adaptive_main_window import AdaptiveMainWindow
        window = AdaptiveMainWindow(ml_service, analysis_service)
        window.show()
        
        logger.info("✅ Adaptive UI initialized successfully")
        logger.info("Features enabled:")
        logger.info(f"  • ML Card Detection: {'✅' if ml_service.is_available else '❌'}")
        logger.info(f"  • Monte Carlo Equity: {'✅' if equity_calculator.backend else '❌'}")
        logger.info(f"  • Adaptive Dockable UI: ✅")
        logger.info(f"  • Persistent Layout: ✅")
        logger.info("")
        
        return app.exec()
        
    except Exception as e:
        logger.critical(f"Application startup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
