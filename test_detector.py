"""
Тестовый скрипт для проверки работы YOLOX детектора карт
"""
import sys
import io
import logging
import cv2
import numpy as np
from pathlib import Path
from ml.detector import TableCardDetector

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_detector():
    """Тестирование детектора"""
    print("=" * 80)
    print("ТЕСТ YOLOX ДЕТЕКТОРА КАРТ")
    print("=" * 80)

    # Путь к модели
    weights_path = "epoch_50_ckpt.pth"

    if not Path(weights_path).exists():
        print(f"❌ Модель не найдена: {weights_path}")
        return

    print(f"✅ Модель найдена: {weights_path}")
    print()

    # Создаем детектор
    print("Загрузка детектора...")
    detector = TableCardDetector(
        weights_path=weights_path,
        device="cpu"  # Используем CPU для теста
    )
    print("✅ Детектор загружен")
    print()

    # Создаем тестовое изображение (черный фон)
    print("Создание тестового изображения...")
    test_image = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Рисуем белые прямоугольники, имитирующие карты
    # Player cards (внизу по центру)
    cv2.rectangle(test_image, (500, 550), (570, 680), (255, 255, 255), -1)  # Левая карта
    cv2.rectangle(test_image, (710, 550), (780, 680), (255, 255, 255), -1)  # Правая карта

    # Board cards (по центру)
    for i in range(3):
        x_start = 400 + i * 100
        cv2.rectangle(test_image, (x_start, 250), (x_start + 70, 380), (200, 200, 200), -1)

    print("✅ Тестовое изображение создано (5 белых прямоугольников)")
    print()

    # Тестируем с разными порогами
    thresholds = [0.1, 0.25, 0.4, 0.5]

    for threshold in thresholds:
        print(f"\n{'='*80}")
        print(f"ТЕСТ С ПОРОГОМ CONFIDENCE = {threshold}")
        print(f"{'='*80}")

        detections = detector.predict(test_image, confidence_threshold=threshold)

        print(f"\n✅ Результат: найдено {len(detections)} карт(ы)")

        if detections:
            print("\nДетали детекций:")
            for i, det in enumerate(detections, 1):
                x1, y1, x2, y2 = det.bbox
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                print(f"  {i}. {det.kind.upper()} card:")
                print(f"     Confidence: {det.score:.4f}")
                print(f"     BBox: ({x1}, {y1}) -> ({x2}, {y2})")
                print(f"     Center: ({center_x}, {center_y})")
                print(f"     Size: {x2-x1}x{y2-y1}")
        else:
            print("  ⚠️ Детекций не найдено")

    print("\n" + "="*80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*80)

if __name__ == "__main__":
    test_detector()
