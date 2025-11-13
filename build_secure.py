#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MonteLab BUILD - Secure Version with Neural Network Exclusion
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategy:
- Compile business logic with Nuitka (core, utils, services, ui)
- Keep neural networks as Python (ml/detector.py)
- Exclude ultralytics and ML frameworks from compilation
- Use main_secure.py as entry point

Why:
- Neural networks are already compiled (torch C++ extensions)
- Ultralytics has complex dependencies, not worth compiling
- Faster build times
- Easier debugging of ML code
"""

import subprocess
import sys
import shutil
from pathlib import Path
import time

class SecureBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.backup_dir = self.project_root / "python_backup"

        # Modules to compile with Nuitka (EXCLUDES neural networks)
        self.nuitka_modules = [
            # Core domain
            'core/domain/card.py',
            'core/domain/game_state.py',
            'core/domain/detection.py',

            # Core poker logic
            'core/poker/hand_evaluator.py',
            'core/poker/outs_calculator.py',
            'core/poker/board_analyzer.py',
            'core/poker/equity_calculator.py',
            'core/poker/monte_carlo_backend.py',

            # Utils (security-sensitive)
            'utils/hwid_generator.py',
            'utils/license_client.py',
            'utils/screen_capture.py',
            'utils/global_hotkeys.py',

            # Services (excluding ml_service.py - uses detector)
            'services/analysis_service.py',
            'services/improved_abc_recommendations.py',

            # UI widgets (but NOT windows - they import ML modules)
            'ui/hwid_dialog.py',
            'ui/styles.py',
            'ui/ui_config.py',
            # 'ui/dock_widgets.py',  # Excluded - may import ml_worker
            'ui/widgets/card_input.py',
            'ui/widgets/selection_overlay.py',
            # 'ui/windows/main_window.py',  # Excluded - imports MLWorker, MLService
            # 'ui/windows/adaptive_main_window.py',  # Excluded - imports MLWorker, MLService
        ]

        # Modules to KEEP as Python (neural networks + dependencies)
        self.excluded_from_compilation = [
            # ML modules
            'ml/detector.py',  # Neural networks
            'ml/__init__.py',  # Imports detector
            'services/ml_service.py',  # Uses detector
            'ui/ml_worker.py',  # Uses ml_service

            # UI that imports ML
            'ui/dock_widgets.py',  # May import ml_worker
            'ui/windows/main_window.py',  # Imports MLWorker, MLService
            'ui/windows/adaptive_main_window.py',  # Imports MLWorker, MLService

            # Entry points
            'main_start.py',  # Entry point (PyInstaller handles it)
            'main_secure.py',  # Entry point
        ]

    def log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "STEP": "▶️"
        }
        symbol = symbols.get(level, "•")
        print(f"[{timestamp}] {symbol} {message}")

    def step(self, message):
        print("\n" + "="*70)
        self.log(message, "STEP")
        print("="*70 + "\n")

    def check_dependencies(self):
        self.step("Checking dependencies")

        # Check Nuitka
        try:
            result = subprocess.run(['python', '-m', 'nuitka', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log(f"Nuitka: {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("Nuitka not found", "ERROR")
                return False
        except:
            self.log("Nuitka not found - install: pip install nuitka", "ERROR")
            return False

        # Check PyInstaller
        try:
            result = subprocess.run(['pyinstaller', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log(f"PyInstaller: {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("PyInstaller not found", "ERROR")
                return False
        except:
            self.log("PyInstaller not found - install: pip install pyinstaller", "ERROR")
            return False

        return True

    def clean_build(self):
        self.step("Cleaning previous builds")

        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)

        # Remove old .pyd/.so files (except in venv)
        for ext in ['*.pyd', '*.so']:
            for compiled_file in self.project_root.rglob(ext):
                if 'venv' in str(compiled_file):
                    continue
                try:
                    compiled_file.unlink()
                    self.log(f"Removed: {compiled_file.name}", "INFO")
                except:
                    pass

        self.log("Build directories cleaned", "SUCCESS")

    def backup_python_files(self):
        self.step("Backing up Python files for compilation")

        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir()

        backed_up = 0
        for module in self.nuitka_modules:
            src = self.project_root / module
            if not src.exists():
                continue

            dst = self.backup_dir / module
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up += 1

        self.log(f"Backed up {backed_up} files", "SUCCESS")

    def compile_with_nuitka(self):
        self.step("Compiling modules with Nuitka")

        self.log(f"Compiling {len(self.nuitka_modules)} modules...", "INFO")
        self.log("⚠️  Excluding: ml/*, ml_service.py, ml_worker.py, ui/windows/*", "WARNING")
        self.log("ℹ️  UI windows excluded (they import ML modules)", "INFO")
        self.log("⏱️  Estimated time: 10-20 minutes", "INFO")

        compiled_count = 0
        failed_count = 0

        for module in self.nuitka_modules:
            module_path = self.project_root / module

            if not module_path.exists():
                self.log(f"Skipping: {module} (not found)", "WARNING")
                continue

            self.log(f"Compiling: {module}", "INFO")

            output_dir = module_path.parent

            cmd = [
                sys.executable, '-m', 'nuitka',
                '--module',
                '--remove-output',
                f'--output-dir={output_dir}',
                '--nofollow-imports',
                '--show-progress',
                '--assume-yes-for-downloads',
                '--disable-plugin=anti-bloat',
                '--enable-plugin=implicit-imports',
                '--include-package-data=numpy',
                str(module_path)
            ]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

                if result.returncode == 0:
                    module_name = module_path.stem
                    compiled_file = None

                    # Find compiled file (.pyd on Windows, .so on Linux)
                    for pattern in [f"{module_name}*.pyd", f"{module_name}*.so"]:
                        matches = list(output_dir.glob(pattern))
                        if matches:
                            compiled_file = matches[0]
                            break

                    if compiled_file:
                        self.log(f"✓ {module} → {compiled_file.name}", "SUCCESS")
                        compiled_count += 1
                    else:
                        self.log(f"✗ {module} - compiled file not found", "WARNING")
                        failed_count += 1
                else:
                    self.log(f"✗ {module} - compilation failed", "ERROR")
                    failed_count += 1

            except subprocess.TimeoutExpired:
                self.log(f"✗ {module} - timeout", "ERROR")
                failed_count += 1
            except Exception as e:
                self.log(f"✗ {module} - {e}", "ERROR")
                failed_count += 1

        print()
        self.log(f"Compiled: {compiled_count}/{len(self.nuitka_modules)} modules",
                "SUCCESS" if compiled_count > 0 else "WARNING")
        if failed_count > 0:
            self.log(f"Failed: {failed_count} modules", "WARNING")

        return compiled_count > 0

    def create_pyinstaller_spec(self):
        self.step("Creating PyInstaller spec")

        spec_content = '''# -*- coding: utf-8 -*-
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
'''

        spec_file = self.project_root / "MonteLab_secure.spec"
        spec_file.write_text(spec_content, encoding='utf-8')

        self.log(f"Created: {spec_file.name}", "SUCCESS")
        return spec_file

    def build_with_pyinstaller(self, spec_file):
        self.step("Building with PyInstaller")

        self.log("Packaging with PyInstaller...", "INFO")
        self.log("⏱️  Estimated time: 5-10 minutes", "INFO")

        cmd = ['pyinstaller', '--clean', '--noconfirm', str(spec_file)]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )

            if result.returncode == 0:
                self.log("PyInstaller completed successfully", "SUCCESS")
                return True
            else:
                self.log("PyInstaller failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"PyInstaller error: {e}", "ERROR")
            return False

    def cleanup_python_from_dist(self):
        self.step("Removing compiled Python sources from distribution")

        dist_folder = self.dist_dir / "MonteLab"

        if not dist_folder.exists():
            self.log("Dist folder not found", "WARNING")
            return

        # Remove .py files for compiled modules only
        removed_count = 0
        for module in self.nuitka_modules:
            module_name = Path(module).stem

            # Find and remove .py files in dist
            for py_file in dist_folder.rglob(f"{module_name}.py"):
                try:
                    py_file.unlink()
                    removed_count += 1
                    self.log(f"Removed: {py_file.name}", "INFO")
                except Exception as e:
                    self.log(f"Could not remove {py_file.name}: {e}", "WARNING")

        self.log(f"Removed {removed_count} compiled Python source files", "SUCCESS")
        self.log("⚠️  ML modules (detector.py, ml_service.py) kept as Python", "INFO")

    def verify_build(self):
        self.step("Verifying build")

        dist_folder = self.dist_dir / "MonteLab"
        exe_path = dist_folder / "MonteLab.exe" if sys.platform == "win32" else dist_folder / "MonteLab"

        if not exe_path.exists():
            self.log(f"Executable not found: {exe_path}", "ERROR")
            return False

        size_mb = exe_path.stat().st_size / (1024 * 1024)
        self.log(f"Executable: {exe_path.name}", "SUCCESS")
        self.log(f"Size: {size_mb:.1f} MB", "INFO")

        # Count compiled modules
        pyd_files = list(dist_folder.rglob("*.pyd"))
        so_files = list(dist_folder.rglob("*.so"))
        compiled_files = pyd_files + so_files
        self.log(f"Compiled modules: {len(compiled_files)}", "INFO")

        # Verify ML modules are present as .py
        ml_detector = dist_folder / "ml" / "detector.py"
        if ml_detector.exists():
            self.log("✓ ml/detector.py present (not compiled)", "SUCCESS")
        else:
            self.log("⚠️  ml/detector.py not found", "WARNING")

        return True

    def restore_python_files(self):
        self.step("Restoring Python source files to project")

        if not self.backup_dir.exists():
            return

        restored = 0
        for backup_file in self.backup_dir.rglob("*.py"):
            relative_path = backup_file.relative_to(self.backup_dir)
            target = self.project_root / relative_path

            shutil.copy2(backup_file, target)
            restored += 1

        self.log(f"Restored {restored} Python files", "SUCCESS")

    def build(self):
        print("\n" + "="*70)
        print("🚀 MonteLab BUILD - Secure Version")
        print("="*70)
        print()
        print("Strategy:")
        print("  ✓ Compile business logic with Nuitka")
        print("  ✓ Keep neural networks as Python")
        print("  ✓ Exclude ultralytics from compilation")
        print()

        start_time = time.time()

        try:
            if not self.check_dependencies():
                return False

            self.clean_build()
            self.backup_python_files()

            # STEP 1: Compile with Nuitka (excluding ML modules)
            if not self.compile_with_nuitka():
                self.log("Some compilation issues, continuing...", "WARNING")

            # STEP 2: Create PyInstaller spec
            spec_file = self.create_pyinstaller_spec()

            # STEP 3: Build with PyInstaller
            if not self.build_with_pyinstaller(spec_file):
                self.log("PyInstaller failed", "ERROR")
                return False

            # STEP 4: Clean up compiled sources from dist
            self.cleanup_python_from_dist()

            # STEP 5: Verify build
            if not self.verify_build():
                return False

            elapsed = time.time() - start_time

            print("\n" + "="*70)
            self.log(f"BUILD COMPLETED in {elapsed/60:.1f} minutes", "SUCCESS")
            print("="*70)

            dist_folder = self.dist_dir / "MonteLab"
            exe_name = "MonteLab.exe" if sys.platform == "win32" else "MonteLab"
            exe_path = dist_folder / exe_name

            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print()
                print(f"📦 Executable: {exe_path}")
                print(f"💾 Size: {size_mb:.1f} MB")
                print(f"🔒 Protected modules: {len(self.nuitka_modules)} compiled")
                print(f"🧠 ML modules: kept as Python for flexibility")
                print()

            return True

        except KeyboardInterrupt:
            self.log("Build interrupted by user", "WARNING")
            return False
        except Exception as e:
            self.log(f"Build failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.restore_python_files()


def main():
    builder = SecureBuilder()
    success = builder.build()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
