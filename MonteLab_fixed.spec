# -*- coding: utf-8 -*-
"""
MonteLab PyInstaller Spec - FIXED VERSION
Key: Uses Python files for analysis, includes .pyd in binaries
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
    # Core modules
    'core.constants',
    'core.data_models',
    'core.hand_analyzer',
    'core.license_integration',
    'utils.screen_capture',
    'utils.hwid_generator',
    'utils.license_client',
    'ui.widgets',
    'ui.hwid_dialog',
    'monte_carlo_engine_v2',
    'secure_entry',
    
    # ML modules
    'ml.detector',
    'app_window',
    
    # ML dependencies
    'torch',
    'torch._C',
    'torchvision',
    'ultralytics',
    
    # Standard
    'cv2',
    'numpy',
    'PIL',
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
]

if sys.platform == 'win32':
    try:
        import wmi
        hiddenimports.append('wmi')
    except:
        pass

excludes = [
    'scipy',
    'tkinter',
    'IPython',
    'jupyter',
]

# CRITICAL: Set recursion limit to avoid infinite loops
import sys
sys.setrecursionlimit(5000)

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    # CRITICAL: Limit module graph depth
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
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='MonteLab'
)
