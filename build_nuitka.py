#!/usr/bin/env python3
"""
Nuitka Build Script for MonteLab
Компилирует проект с шифрованием, исключая тестовые файлы и detector.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Файлы, которые НЕ должны быть включены в сборку
EXCLUDE_FILES = [
    "yolomaker.py",
    "test_yolox_output.py",
    "test_detector_real.py",
    "test_detector.py",
    "test_adaptive_ui.py",
    "montelab.log",
    "main_adaptive.py",
    "main.py",
    "build_nuitka.py",
    "build_pyinstaller.py",
    "build_fixed_v2.py",
    "monte_carlo_engine_v3.py",
    "1111.py",
    "22222.py",
    "123123.py",
]

# Модули, которые НЕ компилировать (оставить как .py)
NO_COMPILE_MODULES = [
    "ml.detector",  # detector.py и модели нейросетей не компилировать
]

# Файлы/папки с данными для включения
DATA_FILES = [
    "models",  # Модели нейросетей
]


def clean_build_dirs():
    """Очистка директорий сборки"""
    print("🧹 Очистка предыдущих сборок...")
    dirs_to_clean = ["build", "dist", "main_secure.dist", "main_secure.build"]

    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  ✓ Удалено: {dir_name}")


def build_with_nuitka():
    """Сборка с Nuitka"""
    print("\n🔨 Начинаем сборку с Nuitka...\n")

    # Базовая команда Nuitka
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",

        # Основной файл
        "main_secure.py",

        # Включить все модули проекта
        "--include-package=core",
        "--include-package=services",
        "--include-package=ui",
        "--include-package=utils",
        "--include-package=ml",

        # Включить main_start (с логикой лицензии) - будет скомпилирован
        "--include-module=main_start",

        # Следовать все импорты
        "--follow-imports",

        # Не компилировать detector.py
        "--nofollow-import-to=ml.detector",

        # Шифрование Python кода (кроме исключенных)
        "--python-flag=-O",

        # Включить data files
        "--include-data-dir=models=models",

        # Оптимизации
        "--assume-yes-for-downloads",
        "--remove-output",

        # Вывод
        "--output-dir=dist",
        "--output-filename=MonteLab",

        # Отключить console для Windows (опционально)
        # "--windows-disable-console",

        # Показывать прогресс
        "--show-progress",
        "--show-memory",
    ]

    # Добавляем исключения для тестовых файлов
    for exclude_file in EXCLUDE_FILES:
        module_name = exclude_file.replace(".py", "").replace("/", ".").replace("\\", ".")
        if module_name:
            cmd.append(f"--nofollow-import-to={module_name}")

    print("📋 Команда сборки:")
    print(" ".join(cmd))
    print()

    # Запуск сборки
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Сборка завершена успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка сборки: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Nuitka не найден. Установите: pip install nuitka")
        return False


def copy_non_compiled_files():
    """Копирование не компилируемых файлов в dist"""
    print("\n📦 Копирование не компилируемых файлов...")

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ Директория dist не найдена")
        return False

    # Копируем detector.py
    detector_src = Path("ml/detector.py")
    if detector_src.exists():
        detector_dst = dist_dir / "ml"
        detector_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(detector_src, detector_dst / "detector.py")
        print(f"  ✓ Скопирован: {detector_src}")

    # Копируем модели
    models_src = Path("models")
    if models_src.exists():
        models_dst = dist_dir / "models"
        if models_dst.exists():
            shutil.rmtree(models_dst)
        shutil.copytree(models_src, models_dst)
        print(f"  ✓ Скопирована папка: models")

    return True


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

    return True


def main():
    """Главная функция"""
    print("=" * 60)
    print("🚀 MonteLab - Nuitka Build Script")
    print("=" * 60)

    # Проверка рабочей директории
    if not Path("main_secure.py").exists():
        print("❌ main_secure.py не найден. Запустите скрипт из корня проекта.")
        return 1

    # Шаги сборки
    steps = [
        ("Очистка", clean_build_dirs),
        ("Сборка с Nuitka", build_with_nuitka),
        ("Копирование файлов", copy_non_compiled_files),
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
