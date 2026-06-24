import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import timm
import os


dataset_path = r'D:\ai_fall_detection_2\Le2i_dataset_Final' 
train_dir = os.path.join(dataset_path, 'train')
test_dir = os.path.join(dataset_path, 'test')

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 التدريب الشامل بدأ على: {device}")

# 2. التحويلات (transforms) 
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    # تحويل الصور لرمادي عشوائياً (بنسبة 50%) عشان يركز على الشكل
    transforms.RandomGrayscale(p=0.5), 
    # إضافة تشويه بسيط في الألوان للصور الـ RGB
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
    transforms.ToTensor(),
    # الـ Normalization القياسي للـ ImageNet
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# 3. تحميل الداتا
train_dataset = datasets.ImageFolder(train_dir, transform=transform)
test_dataset = datasets.ImageFolder(test_dir, transform=transform)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

print(f"📊 عدد صور التدريب: {len(train_dataset)}")
print(f"📊 عدد صور الاختبار: {len(test_dataset)}")

# 4. بناء الموديل (ViT Tiny)
model = timm.create_model('vit_tiny_patch16_224', pretrained=True, num_classes=2)
model = model.to(device)

# 5. الـ Loss والـ Optimizer
criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(model.parameters(), lr=0.0001)

# 6. حلقة التدريب (5 Epochs)
num_epochs = 5
print(" بدأنا التدريب على الداتا الشاملة (RGB + Skeleton)...")

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    accuracy = 100 * correct / total
    print(f"Epoch [{epoch+1}/{num_epochs}] - Loss: {running_loss/len(train_loader):.4f} - Accuracy: {accuracy:.2f}%")

final_model_path = os.path.join(r'D:\ai_fall_detection_2', 'fall_detection_vit_hybrid_RGB_Skeleton.pth')
torch.save(model.state_dict(), final_model_path)
print(f"\n🏆 تم حفظ الموديل الشامل بنجاح في: {final_model_path}")