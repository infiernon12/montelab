#!/usr/bin/env python3
"""
PyInstaller Build Script for MonteLab
Альтернативная сборка с использованием PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Файлы, которые НЕ должны быть включены в сборку
EXCLUDE_FILES = [
    "yolomaker",
    "test_yolox_output",
    "test_detector_real",
    "test_detector",
    "test_adaptive_ui",
    "main_adaptive",
    "main",
    "build_nuitka",
    "build_pyinstaller",
    "build_fixed_v2",
    "monte_carlo_engine_v3",
    "1111",
    "22222",
    "123123",
]


def clean_build_dirs():
    """Очистка директорий сборки"""
    print("🧹 Очистка предыдущих сборок...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["MonteLab.spec"]

    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  ✓ Удалено: {dir_name}")

    for file_name in files_to_clean:
        if Path(file_name).exists():
            Path(file_name).unlink()
            print(f"  ✓ Удалено: {file_name}")


def create_spec_file():
    """Создание .spec файла для PyInstaller"""
    print("\n📝 Создание .spec файла...")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Excluded modules
excludes = [
    'yolomaker',
    'test_yolox_output',
    'test_detector_real',
    'test_detector',
    'test_adaptive_ui',
    'main_adaptive',
    'main',
    'build_nuitka',
    'build_pyinstaller',
    'build_fixed_v2',
    'monte_carlo_engine_v3',
]

a = Analysis(
    ['main_secure.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'models'),  # Включить модели
    ],
    hiddenimports=[
        'main_start',
        'core',
        'core.domain',
        'core.poker',
        'services',
        'ui',
        'ui.widgets',
        'ui.windows',
        'utils',
        'ml',
        'ml.detector',
        'PySide6',
        'torch',
        'torchvision',
        'cv2',
        'numpy',
        'yolox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MonteLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Установите False для GUI без консоли
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    spec_file = Path("MonteLab.spec")
    spec_file.write_text(spec_content)
    print(f"  ✓ Создан файл: {spec_file}")
    return True


def build_with_pyinstaller():
    """Сборка с PyInstaller"""
    print("\n🔨 Начинаем сборку с PyInstaller...\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "MonteLab.spec"
    ]

    print("📋 Команда сборки:")
    print(" ".join(cmd))
    print()

    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Сборка завершена успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка сборки: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ PyInstaller не найден. Установите: pip install pyinstaller")
        return False


def verify_build():
    """Проверка сборки"""
    print("\n🔍 Проверка сборки...")

    dist_dir = Path("dist")
    executable = dist_dir / "MonteLab" if os.name != "nt" else dist_dir / "MonteLab.exe"

    if not executable.exists():
        print(f"❌ Исполняемый файл не найден: {executable}")
        return False

    file_size = executable.stat().st_size / (1024 * 1024)  # MB
    print(f"  ✓ Найден исполняемый файл: {executable}")
    print(f"  ✓ Размер: {file_size:.2f} MB")

    # Проверка наличия models
    models_dir = dist_dir / "models"
    if models_dir.exists():
        print(f"  ✓ Найдена папка models")
    else:
        print(f"  ⚠️ Папка models не найдена (может быть упакована в exe)")

    return True


def main():
    """Главная функция"""
    print("=" * 60)
    print("🚀 MonteLab - PyInstaller Build Script")
    print("=" * 60)

    # Проверка рабочей директории
    if not Path("main_secure.py").exists():
        print("❌ main_secure.py не найден. Запустите скрипт из корня проекта.")
        return 1

    # Шаги сборки
    steps = [
        ("Очистка", clean_build_dirs),
        ("Создание .spec", create_spec_file),
        ("Сборка с PyInstaller", build_with_pyinstaller),
        ("Проверка", verify_build),
    ]

    for step_name, step_func in steps:
        print(f"\n{'=' * 60}")
        print(f"Шаг: {step_name}")
        print(f"{'=' * 60}")

        if not step_func():
            print(f"\n❌ Ошибка на шаге: {step_name}")
            return 1

    print("\n" + "=" * 60)
    print("✅ Сборка полностью завершена!")
    print("=" * 60)
    print(f"\n📦 Результат в папке: dist/")
    print(f"🎯 Запуск: ./dist/MonteLab")

    return 0


if __name__ == "__main__":
    sys.exit(main())
