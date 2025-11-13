# -*- coding: utf-8 -*-
"""
MonteLab PyInstaller Spec - Secure Version
Neural networks and ML frameworks kept as Python for flexibility
"""

import sys
from pathlib import Path

project_root = Path.cwd()

# Data files
datas = [
    ('models/*.pt', 'models'),
    ('MonteCarlo-Poker-master/MonteCarloPoker.exe', 'MonteCarlo-Poker-master'),
    ('MonteCarlo-Poker-master/lookup_tablev3.bin', 'MonteCarlo-Poker-master'),
]

# Hidden imports
hiddenimports = [
    # Core modules (compiled with Nuitka)
    'core',
    'core.domain',
    'core.domain.card',
    'core.domain.game_state',
    'core.domain.detection',
    'core.poker',
    'core.poker.hand_evaluator',
    'core.poker.outs_calculator',
    'core.poker.board_analyzer',
    'core.poker.equity_calculator',
    'core.poker.monte_carlo_backend',

    # Utils (compiled with Nuitka)
    'utils',
    'utils.hwid_generator',
    'utils.license_client',
    'utils.screen_capture',
    'utils.global_hotkeys',

    # Services
    'services',
    'services.analysis_service',
    'services.improved_abc_recommendations',
    'services.ml_service',  # Keep as Python

    # ML modules (NOT compiled - keep as Python)
    'ml',
    'ml.detector',  # Neural networks

    # UI
    'ui',
    'ui.hwid_dialog',
    'ui.styles',
    'ui.ui_config',
    'ui.dock_widgets',
    'ui.ml_worker',  # Keep as Python
    'ui.widgets',
    'ui.widgets.card_input',
    'ui.widgets.selection_overlay',
    'ui.windows',
    'ui.windows.main_window',
    'ui.windows.adaptive_main_window',

    # Main modules
    'main_start',

    # ML dependencies (NOT compiled)
    'torch',
    'torch._C',
    'torch.nn',
    'torch.nn.functional',
    'torchvision',
    'torchvision.models',
    'torchvision.transforms',
    'ultralytics',
    'ultralytics.engine',
    'ultralytics.models',

    # Standard libraries
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'requests',
    'psutil',
    'mss',
    'pyautogui',
    'matplotlib',
    'matplotlib.pyplot',
    'pandas',
    'logging',
    'pathlib',
    'collections',
]

if sys.platform == 'win32':
    try:
        import wmi
        hiddenimports.append('wmi')
    except:
        pass

# Exclude unnecessary packages
excludes = [
    'scipy',
    'tkinter',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'setuptools',
]

# Set recursion limit
sys.setrecursionlimit(5000)

a = Analysis(
    ['main_secure.py'],  # Use secure entry point
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    # Keep ML frameworks as regular Python modules
    module_collection_mode={
        'torch': 'pyz',
        'torchvision': 'pyz',
        'ultralytics': 'pyz',
    }
)

pyz = PYZ(a.pure, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MonteLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MonteLab'
)
