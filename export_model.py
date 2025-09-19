import torch
import torchvision.models as models

def export_mobilenetv2():
    """
    Завантажує попередньо навчену модель MobileNetV2,
    переводить її в режим оцінки та зберігає у форматі TorchScript.
    """
    # Завантаження попередньо навченої моделі
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    
    # Переведення моделі у режим оцінки
    model.eval()
    
    # Створення прикладу вхідного тензора
    example_input = torch.rand(1, 3, 224, 224)
    
    # Трасування моделі за допомогою TorchScript
    scripted_model = torch.jit.trace(model, example_input)
    
    # Збереження
    model_path = "model.pt"
    scripted_model.save(model_path)
    
    print(f"Модель MobileNetV2 успішно експортовано у '{model_path}'")

if __name__ == "__main__":
    export_mobilenetv2()
