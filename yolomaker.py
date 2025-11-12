import os
import json
from pathlib import Path
from PIL import Image

os.makedirs(r"C:\Users\User\Desktop\annotations", exist_ok=True)

def yolo_txt_to_coco(
    images_dir,
    labels_dir,
    output_json,
    categories
):
    coco = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    # Формируем список категорий как требуется COCO
    for idx, name in enumerate(categories):
        coco["categories"].append({
            "id": idx,
            "name": name
        })

    annotation_id = 0
    image_id = 0
    img_extensions = (".jpg", ".jpeg", ".png")

    for img_file in sorted(os.listdir(images_dir)):
        if not img_file.lower().endswith(img_extensions):
            continue
        img_path = os.path.join(images_dir, img_file)
        img = Image.open(img_path)
        width, height = img.size

        coco["images"].append({
            "id": image_id,
            "file_name": img_file,
            "width": width,
            "height": height
        })

        label_file = os.path.join(labels_dir, Path(img_file).stem + ".txt")
        if os.path.isfile(label_file):
            with open(label_file) as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue
                    cls, x, y, w, h = map(float, parts)
                    # YOLO формат: x/y/w/h — центр и размеры, нормированные [0,1]
                    # COCO формат: bbox=[x_min, y_min, width, height], абсолютные px!
                    x_coco = (x - w / 2) * width
                    y_coco = (y - h / 2) * height
                    w_coco = w * width
                    h_coco = h * height

                    coco["annotations"].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": int(cls),
                        "bbox": [x_coco, y_coco, w_coco, h_coco],
                        "area": w_coco * h_coco,
                        "iscrowd": 0,
                        "segmentation": [] # не заполняем, если нет разметки сегментации
                    })
                    annotation_id += 1

        image_id += 1

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(coco, f, indent=4)
    print(f"COCO json saved: {output_json}")

# ========== НАСТРОЙКИ ==========

categories = [
    "class1", "class2", "class3"
    # ... замените на свои имена классов и разрешите их количество
]

# Пути до данных
train_images_dir = r"C:\Users\User\Desktop\images\train"
train_labels_dir = r"C:\Users\User\Desktop\labels\train"
val_images_dir   = r"C:\Users\User\Desktop\images\val"
val_labels_dir   = r"C:\Users\User\Desktop\labels\val"

# ==== Конвертим train =====
yolo_txt_to_coco(
    train_images_dir,
    train_labels_dir,
    r"C:\Users\User\Desktop\annotations\instances_train.json",
    categories
)

# ==== Конвертим val =====
yolo_txt_to_coco(
    val_images_dir,
    val_labels_dir,
    r"C:\Users\User\Desktop\annotations\instances_val.json",
    categories
)

print("Конвертация завершена!")
