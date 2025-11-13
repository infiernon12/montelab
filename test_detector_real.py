"""
Тестовый скрипт для проверки YOLOX детектора на реальных изображениях
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

def test_detector_real():
    """Тестирование детектора на реальных изображениях"""
    print("=" * 80)
    print("ТЕСТ YOLOX ДЕТЕКТОРА КАРТ (РЕАЛЬНЫЕ ИЗОБРАЖЕНИЯ)")
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
        device="cpu"
    )
    print("✅ Детектор загружен")
    print()

    # Проверяем наличие тестовых изображений
    test_images = list(Path(".").glob("*.png")) + list(Path(".").glob("*.jpg"))

    if not test_images:
        print("⚠️ Нет изображений для тестирования (.png или .jpg)")
        print()
        print("Создание синтетического изображения с текстурой карт...")
        test_image = create_synthetic_poker_table()
        test_images = [("synthetic", test_image)]
    else:
        print(f"✅ Найдено {len(test_images)} изображений для тестирования")
        test_images = [(str(path), cv2.imread(str(path))) for path in test_images[:3]]

    # Тестируем на каждом изображении
    for img_name, img in test_images:
        if img is None:
            continue

        print(f"\n{'='*80}")
        print(f"ТЕСТ НА: {img_name}")
        print(f"Размер: {img.shape[1]}x{img.shape[0]}")
        print(f"{'='*80}")

        # Тестируем с низким порогом
        threshold = 0.01
        print(f"\nПорог confidence: {threshold}")

        detections = detector.predict(img, confidence_threshold=threshold)

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

            # Сохраняем результат с аннотациями
            output_img = img.copy()
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                color = (0, 255, 0) if det.kind == "player" else (255, 0, 0)
                cv2.rectangle(output_img, (x1, y1), (x2, y2), color, 2)
                label = f"{det.kind} {det.score:.2f}"
                cv2.putText(output_img, label, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            output_name = f"detection_result_{Path(img_name).stem}.jpg"
            cv2.imwrite(output_name, output_img)
            print(f"\n✅ Результат сохранен: {output_name}")
        else:
            print("  ⚠️ Детекций не найдено")
            print("  Причины:")
            print("    - Модель обучена на реальных картах покера")
            print("    - Изображение может не содержать карт")
            print("    - Карты могут быть слишком маленькие/размытые")

    print("\n" + "="*80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*80)

def create_synthetic_poker_table():
    """Создает синтетическое изображение покерного стола"""
    # Создаем зеленый фон (как покерный стол)
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    img[:, :] = (35, 86, 35)  # Темно-зеленый

    # Рисуем прямоугольники с градиентом (имитация карт)
    def draw_card(img, x, y, w, h):
        # Белый прямоугольник с черной рамкой
        card = np.ones((h, w, 3), dtype=np.uint8) * 240
        # Добавляем текстуру
        noise = np.random.randint(-20, 20, (h, w, 3), dtype=np.int16)
        card = np.clip(card.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        # Рамка
        cv2.rectangle(card, (0, 0), (w-1, h-1), (0, 0, 0), 2)
        # Символы (простые линии для имитации)
        cv2.line(card, (10, 10), (20, 30), (200, 0, 0), 2)
        cv2.circle(card, (w//2, h//2), 15, (0, 0, 200), -1)

        img[y:y+h, x:x+w] = card

    # Player cards (внизу)
    draw_card(img, 500, 550, 70, 100)
    draw_card(img, 710, 550, 70, 100)

    # Board cards (центр)
    for i in range(3):
        draw_card(img, 400 + i * 90, 280, 70, 100)

    return img

if __name__ == "__main__":
    test_detector_real()
