"""
Test script for Adaptive UI - Validates all adaptive features
Run: python test_adaptive_ui.py
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all new modules can be imported"""
    logger.info("=" * 60)
    logger.info("TEST 1: Module Imports")
    logger.info("=" * 60)
    
    try:
        from ui.ui_config import UIConfig, UIConfigManager, WindowGeometry, DockState
        logger.info("✅ ui.ui_config imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import ui.ui_config: {e}")
        return False
    
    try:
        from ui.dock_widgets import (BaseDockWidget, TableConfigDock, 
                                    CardsDock, AnalysisDock, ImagePreviewDock)
        logger.info("✅ ui.dock_widgets imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import ui.dock_widgets: {e}")
        return False
    
    try:
        from ui.windows.adaptive_main_window import AdaptiveMainWindow
        logger.info("✅ ui.windows.adaptive_main_window imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import adaptive_main_window: {e}")
        return False
    
    logger.info("")
    return True


def test_ui_config():
    """Test UIConfig functionality"""
    logger.info("=" * 60)
    logger.info("TEST 2: UIConfig Functionality")
    logger.info("=" * 60)
    
    try:
        from ui.ui_config import UIConfig, WindowGeometry, DockState
        
        # Test WindowGeometry
        geom = WindowGeometry(x=100, y=100, width=1400, height=900)
        logger.info(f"✅ WindowGeometry created: {geom.width}x{geom.height}")
        
        # Test QRect conversion
        qrect = geom.to_qrect()
        logger.info(f"✅ QRect conversion works: {qrect.width()}x{qrect.height()}")
        
        # Test DockState
        dock_state = DockState(
            name="test_dock",
            floating=True,
            visible=True,
            area="left"
        )
        logger.info(f"✅ DockState created: {dock_state.name}")
        
        # Test dict conversion
        state_dict = dock_state.to_dict()
        logger.info(f"✅ DockState to_dict works: {state_dict}")
        
        # Test UIConfig
        config = UIConfig(
            window_geometry=geom,
            dock_states={"test": dock_state}
        )
        logger.info(f"✅ UIConfig created with {len(config.dock_states)} docks")
        
        # Test serialization
        config_dict = config.to_dict()
        logger.info(f"✅ UIConfig serialization works")
        
        # Test deserialization
        config_restored = UIConfig.from_dict(config_dict)
        logger.info(f"✅ UIConfig deserialization works")
        
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ UIConfig test failed: {e}", exc_info=True)
        return False


def test_ui_config_manager():
    """Test UIConfigManager save/load"""
    logger.info("=" * 60)
    logger.info("TEST 3: UIConfigManager Save/Load")
    logger.info("=" * 60)
    
    try:
        from ui.ui_config import UIConfigManager, WindowGeometry
        import tempfile
        import os
        
        # Create temp config file
        temp_dir = tempfile.gettempdir()
        temp_config = Path(temp_dir) / "test_ui_config.json"
        
        # Clean up if exists
        if temp_config.exists():
            temp_config.unlink()
        
        # Create manager
        manager = UIConfigManager(temp_config)
        logger.info(f"✅ UIConfigManager created: {temp_config}")
        
        # Load (should create default)
        config = manager.load()
        logger.info(f"✅ Default config loaded")
        
        # Modify
        config.window_geometry = WindowGeometry(x=200, y=200, width=1600, height=1000)
        config.roi = [100, 100, 500, 400]
        
        # Save
        success = manager.save(config)
        if success:
            logger.info(f"✅ Config saved successfully")
        else:
            logger.error(f"❌ Failed to save config")
            return False
        
        # Verify file exists
        if temp_config.exists():
            logger.info(f"✅ Config file created: {temp_config}")
        else:
            logger.error(f"❌ Config file not found")
            return False
        
        # Load again
        config_loaded = manager.load()
        logger.info(f"✅ Config loaded from file")
        
        # Verify data
        if config_loaded.window_geometry.width == 1600:
            logger.info(f"✅ Window geometry restored correctly")
        else:
            logger.error(f"❌ Window geometry mismatch")
            return False
        
        if config_loaded.roi == [100, 100, 500, 400]:
            logger.info(f"✅ ROI restored correctly")
        else:
            logger.error(f"❌ ROI mismatch")
            return False
        
        # Clean up
        temp_config.unlink()
        logger.info(f"✅ Cleanup successful")
        
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ UIConfigManager test failed: {e}", exc_info=True)
        return False


def test_dock_widgets():
    """Test dock widget creation (no GUI)"""
    logger.info("=" * 60)
    logger.info("TEST 4: Dock Widgets Creation")
    logger.info("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.dock_widgets import (TableConfigDock, CardsDock, 
                                    AnalysisDock, ImagePreviewDock)
        
        # Need QApplication for Qt widgets
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test TableConfigDock
        table_dock = TableConfigDock()
        logger.info(f"✅ TableConfigDock created: {table_dock.objectName()}")
        
        # Test CardsDock
        cards_dock = CardsDock()
        logger.info(f"✅ CardsDock created: {cards_dock.objectName()}")
        logger.info(f"   - Has {len(cards_dock.get_all_card_widgets())} card widgets")
        
        # Test AnalysisDock
        analysis_dock = AnalysisDock()
        logger.info(f"✅ AnalysisDock created: {analysis_dock.objectName()}")
        
        # Test ImagePreviewDock
        image_dock = ImagePreviewDock()
        logger.info(f"✅ ImagePreviewDock created: {image_dock.objectName()}")
        
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dock widgets test failed: {e}", exc_info=True)
        return False


def test_adaptive_window_creation():
    """Test adaptive main window creation (no show)"""
    logger.info("=" * 60)
    logger.info("TEST 5: Adaptive Main Window Creation")
    logger.info("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.windows.adaptive_main_window import AdaptiveMainWindow
        from services.ml_service import MLService
        from services.analysis_service import AnalysisService
        from core.poker import EquityCalculator
        
        # Need QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create mock services (without actual models)
        ml_service = MLService(detector=None, classifier=None)
        equity_calculator = EquityCalculator(backend=None)
        analysis_service = AnalysisService(equity_calculator)
        
        logger.info(f"✅ Services created (mock)")
        
        # Create window (don't show)
        window = AdaptiveMainWindow(ml_service, analysis_service)
        logger.info(f"✅ AdaptiveMainWindow created")
        
        # Test docks exist
        if window.table_config_dock:
            logger.info(f"✅ TableConfigDock exists")
        else:
            logger.error(f"❌ TableConfigDock missing")
            return False
        
        if window.cards_dock:
            logger.info(f"✅ CardsDock exists")
        else:
            logger.error(f"❌ CardsDock missing")
            return False
        
        if window.analysis_dock:
            logger.info(f"✅ AnalysisDock exists")
        else:
            logger.error(f"❌ AnalysisDock missing")
            return False
        
        if window.image_preview_dock:
            logger.info(f"✅ ImagePreviewDock exists")
        else:
            logger.error(f"❌ ImagePreviewDock missing")
            return False
        
        # Test UI components
        if window.menuBar():
            logger.info(f"✅ MenuBar exists")
        else:
            logger.error(f"❌ MenuBar missing")
        
        if window.statusBar():
            logger.info(f"✅ StatusBar exists")
        else:
            logger.error(f"❌ StatusBar missing")
        
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ Adaptive window test failed: {e}", exc_info=True)
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 10 + "ADAPTIVE UI TEST SUITE" + " " * 26 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")
    
    results = {
        "Module Imports": test_imports(),
        "UIConfig Functionality": test_ui_config(),
        "UIConfigManager Save/Load": test_ui_config_manager(),
        "Dock Widgets Creation": test_dock_widgets(),
        "Adaptive Window Creation": test_adaptive_window_creation()
    }
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    # Change to project directory
    project_dir = Path(__file__).parent
    sys.path.insert(0, str(project_dir))
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
