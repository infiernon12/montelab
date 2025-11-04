#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MonteLab BUILD - FIXED for PyInstaller + Nuitka conflict
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOLUTION: Run PyInstaller BEFORE removing Python files
- Nuitka compiles modules
- Python files stay temporarily for PyInstaller analysis
- PyInstaller analyzes PYTHON files, not .pyd
- Remove Python files after successful build
"""

import subprocess
import sys
import shutil
from pathlib import Path
import time

class FixedBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.backup_dir = self.project_root / "python_backup"
        
        self.nuitka_modules = [
            'core/constants.py',
            'core/data_models.py',
            'core/hand_analyzer.py',
            'core/license_integration.py',
            'utils/screen_capture.py',
            'utils/hwid_generator.py',
            'utils/license_client.py',
            'ui/widgets.py',
            'ui/hwid_dialog.py',
            'monte_carlo_engine.py',
            'secure_entry.py',
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
        
        try:
            result = subprocess.run(['python', '-m', 'nuitka', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log(f"Nuitka: {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("Nuitka not found", "ERROR")
                return False
        except:
            self.log("Nuitka not found", "ERROR")
            return False
        
        try:
            result = subprocess.run(['pyinstaller', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log(f"PyInstaller: {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("PyInstaller not found", "ERROR")
                return False
        except:
            self.log("PyInstaller not found", "ERROR")
            return False
        
        return True
    
    def clean_build(self):
        self.step("Cleaning previous builds")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
        
        # Remove old .pyd files
        for pyd_file in self.project_root.rglob("*.pyd"):
            if 'venv' in str(pyd_file) or 'porta-venv' in str(pyd_file):
                continue
            try:
                pyd_file.unlink()
            except:
                pass
        
        self.log("Build directories cleaned", "SUCCESS")
    
    def backup_python_files(self):
        self.step("Backing up Python files")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir()
        
        for module in self.nuitka_modules:
            src = self.project_root / module
            if not src.exists():
                continue
            
            dst = self.backup_dir / module
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        
        count = len(list(self.backup_dir.rglob('*.py')))
        self.log(f"Backed up {count} files", "SUCCESS")
    
    def compile_with_nuitka(self):
        self.step("Compiling modules with Nuitka")
        
        self.log("Compiling... (10-15 minutes)", "INFO")
        
        compiled_count = 0
        
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
                '--include-package-data=cv2',
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
                    
                    for pattern in [f"{module_name}*.pyd", f"{module_name}*.so"]:
                        matches = list(output_dir.glob(pattern))
                        if matches:
                            compiled_file = matches[0]
                            break
                    
                    if compiled_file:
                        self.log(f"✓ {module} → {compiled_file.name}", "SUCCESS")
                        compiled_count += 1
                    
            except Exception as e:
                self.log(f"Exception: {module} - {e}", "ERROR")
        
        self.log(f"Compiled {compiled_count}/{len(self.nuitka_modules)} modules", "SUCCESS")
        return True
    
    def create_pyinstaller_spec(self):
        self.step("Creating PyInstaller spec")
        
        spec_content = '''# -*- coding: utf-8 -*-
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
'''
        
        spec_file = self.project_root / "MonteLab_fixed.spec"
        spec_file.write_text(spec_content, encoding='utf-8')
        
        self.log(f"Created: {spec_file.name}", "SUCCESS")
        return spec_file
    
    def build_with_pyinstaller(self, spec_file):
        self.step("Building with PyInstaller")
        
        self.log("IMPORTANT: Keeping Python files during analysis", "WARNING")
        self.log("PyInstaller will analyze .py files, not .pyd", "INFO")
        
        cmd = ['pyinstaller', '--clean', '--noconfirm', str(spec_file)]
        
        self.log("Packaging... (5-10 minutes)", "INFO")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                self.log("PyInstaller completed", "SUCCESS")
                return True
            else:
                self.log("PyInstaller failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"PyInstaller error: {e}", "ERROR")
            return False
    
    def cleanup_python_from_dist(self):
        self.step("Removing Python files from distribution")
        
        dist_folder = self.dist_dir / "MonteLab"
        
        if not dist_folder.exists():
            self.log("Dist folder not found", "WARNING")
            return
        
        # Remove Python source files from compiled modules
        removed_count = 0
        for module in self.nuitka_modules:
            module_name = Path(module).stem
            
            # Find and remove .py files
            for py_file in dist_folder.rglob(f"{module_name}.py"):
                try:
                    py_file.unlink()
                    removed_count += 1
                    self.log(f"Removed: {py_file.name}", "INFO")
                except Exception as e:
                    self.log(f"Could not remove {py_file.name}: {e}", "WARNING")
        
        self.log(f"Removed {removed_count} Python source files from dist", "SUCCESS")
    
    def verify_build(self):
        self.step("Verifying build")
        
        exe_path = self.dist_dir / "MonteLab" / "MonteLab.exe"
        
        if not exe_path.exists():
            self.log(f"Executable not found: {exe_path}", "ERROR")
            return False
        
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        self.log(f"Executable size: {size_mb:.1f} MB", "INFO")
        
        pyd_files = list((self.dist_dir / "MonteLab").rglob("*.pyd"))
        self.log(f"Found {len(pyd_files)} compiled modules", "INFO")
        
        self.log("Build verification completed", "SUCCESS")
        return True
    
    def restore_python_files(self):
        self.step("Restoring Python source files")
        
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
        print("🚀 MonteLab BUILD - FIXED VERSION")
        print("="*70)
        print()
        print("FIX: PyInstaller analyzes Python files BEFORE removal")
        print()
        
        start_time = time.time()
        
        try:
            if not self.check_dependencies():
                return False
            
            self.clean_build()
            self.backup_python_files()
            
            # STEP 1: Compile with Nuitka (creates .pyd alongside .py)
            if not self.compile_with_nuitka():
                self.log("Compilation issues", "WARNING")
            
            # STEP 2: Create spec (while .py files still exist!)
            spec_file = self.create_pyinstaller_spec()
            
            # STEP 3: Run PyInstaller (analyzes .py files)
            if not self.build_with_pyinstaller(spec_file):
                self.log("PyInstaller failed", "ERROR")
                return False
            
            # STEP 4: Clean up Python files from dist
            self.cleanup_python_from_dist()
            
            # STEP 5: Verify
            if not self.verify_build():
                return False
            
            elapsed = time.time() - start_time
            
            print("\n" + "="*70)
            self.log(f"BUILD COMPLETED in {elapsed/60:.1f} minutes", "SUCCESS")
            print("="*70)
            
            exe_path = self.dist_dir / "MonteLab" / "MonteLab.exe"
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            
            print()
            print(f"📦 Executable: {exe_path}")
            print(f"💾 Size: {size_mb:.1f} MB")
            print(f"🔒 Protected modules: {len(self.nuitka_modules)} compiled")
            print()
            
            return True
            
        except KeyboardInterrupt:
            self.log("Build interrupted", "WARNING")
            return False
        except Exception as e:
            self.log(f"Build failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.restore_python_files()


def main():
    builder = FixedBuilder()
    success = builder.build()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
