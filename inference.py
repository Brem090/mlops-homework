import sys
import json
import torch
from torchvision import transforms
from PIL import Image

# Завантаження класів ImageNet (потрібно завантажити файл imagenet_class_index.json)
try:
    with open("imagenet_class_index.json", "r") as f:
        class_idx = json.load(f)
        idx2label = [class_idx[str(k)][1] for k in range(len(class_idx))]
except FileNotFoundError:
    print("Помилка: Файл 'imagenet_class_index.json' не знайдено.")
    print("Будь ласка, завантажте його: wget https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json")
    sys.exit(1)


def predict(image_path: str, model_path: str = "model.pt", top_k: int = 3):
    """
    Завантажує модель TorchScript, обробляє зображення та повертає топ-K передбачень.
    """
    # Завантаження моделі
    try:
        model = torch.jit.load(model_path)
        model.eval()
    except Exception as e:
        print(f"Не вдалося завантажити модель з {model_path}: {e}")
        sys.exit(1)
        
    # Відкривання зображення
    try:
        input_image = Image.open(image_path).convert('RGB')
    except FileNotFoundError:
        print(f"Помилка: Файл зображення '{image_path}' не знайдено.")
        sys.exit(1)

    # Трансформації для зображення 
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0) # Створення міні-батчів

    # Виконання inference
    with torch.no_grad():
        output = model(input_batch)

    # Отримуання ймовірностей за допомогою Softmax
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    
    # Отримання топ-K результатів
    top_prob, top_indices = torch.topk(probabilities, top_k)
    
    print(f"Результати для зображення: {image_path}\n")
    for i in range(top_k):
        label = idx2label[top_indices[i]]
        prob = top_prob[i].item() * 100
        print(f"{i+1}. Клас: {label}, Ймовірність: {prob:.2f}%")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python inference.py <шлях_до_зображення>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    predict(image_path)