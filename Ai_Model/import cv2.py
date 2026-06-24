import cv2
import torch
import numpy as np
from ultralytics import YOLO
import timm
from torchvision import transforms
from PIL import Image
from collections import deque
import os
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- Firebase ---
if not firebase_admin._apps:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, "serviceAccountKey.json")
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://falldetection-4f6fe-default-rtdb.europe-west1.firebasedatabase.app/'
        })
        print("✅ Firebase initialized successfully!")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        exit()

fall_ref = db.reference('fall')
try:
    fall_ref.update({'isDetected': False, 'last_fall_time': '0'})
    print("🔄 Firebase status reset.")
except:
    pass

# --- Device ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)
if device.type == 'cuda':
    print("GPU:", torch.cuda.get_device_name(0))

model_path = r'D:\ai_fall_detection_2\fall_detection_vit_hybrid_RGB_Skeleton.pth'

# --- Models ---
yolo_pose = YOLO('yolov8n-pose.pt').to(device)

vit_model = timm.create_model('vit_tiny_patch16_224', num_classes=2)
vit_model.load_state_dict(torch.load(model_path, map_location=device))
vit_model.to(device)
vit_model.eval()

if device.type == 'cuda':
    vit_model.half()

# --- Transforms ---
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# --- History ---
prediction_history = deque(maxlen=10)

# --- Camera ---
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

print("🚀 System Running...")


def is_suspicious_pose(keypoints_data):
    """
    بيحلل الـ keypoints من YOLO ويشوف لو في اشتباه بسقوط.
    بيعتمد على:
    1. نسبة الارتفاع للعرض (الشخص بيبقى أفقي)
    2. موقع الكتف والورك بالنسبة للإطار
    """
    try:
        kps = keypoints_data.xy[0].cpu().numpy()  # shape: (17, 2)

        # Keypoint indices (COCO format):
        # 5,6 = shoulders | 11,12 = hips | 15,16 = ankles

        def valid(pt):
            return pt[0] > 0 and pt[1] > 0

        left_shoulder  = kps[5]
        right_shoulder = kps[6]
        left_hip       = kps[11]
        right_hip      = kps[12]
        left_ankle     = kps[15]
        right_ankle    = kps[16]

        pts = [p for p in [left_shoulder, right_shoulder,
                            left_hip, right_hip,
                            left_ankle, right_ankle] if valid(p)]

        if len(pts) < 3:
            return False  # مفيش بيانات كافية

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        width  = max(xs) - min(xs)
        height = max(ys) - min(ys)

        if height == 0:
            return False

        aspect_ratio = width / height

        # لو الشخص أفقي (عرض > ارتفاع) → اشتباه سقوط
        suspicious = aspect_ratio > 1.2

        return suspicious

    except Exception:
        return False


while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))

    # --- YOLO على كل فريم ---
    results = yolo_pose(frame, verbose=False, device=0)

    final_status = "Normal"
    confidence_score = 0.0

    for r in results:
        if r.keypoints is None:
            continue

        frame = r.plot(boxes=False)

        # --- مرحلة 1: هل في اشتباه؟ ---
        suspicious = is_suspicious_pose(r.keypoints)

        if suspicious:
            # --- مرحلة 2: ViT بس لو في اشتباه ---
            skeleton_only = r.plot(boxes=False, labels=False)
            img_rgb = cv2.cvtColor(skeleton_only, cv2.COLOR_BGR2RGB)
            img_tensor = transform(Image.fromarray(img_rgb)).unsqueeze(0).to(device)

            if device.type == 'cuda':
                img_tensor = img_tensor.half()

            with torch.no_grad():
                output = vit_model(img_tensor)
                probabilities = torch.nn.functional.softmax(output, dim=1)
                fall_prob = probabilities[0][0].item()
                confidence_score = fall_prob

                if fall_prob > 0.90:
                    prediction_history.append("Fall")
                else:
                    prediction_history.append("Normal")
        else:
            # مفيش اشتباه → Normal مباشرة بدون ViT
            prediction_history.append("Normal")

    # --- Decision ---
    if len(prediction_history) > 0:
        fall_count = list(prediction_history).count("Fall")
        final_status = "Fall" if fall_count >= 7 else "Normal"

    # --- Alert ---
    if final_status == "Fall":
        color = (0, 0, 255)
        cv2.rectangle(frame, (15, 15),
                      (frame.shape[1]-15, frame.shape[0]-15),
                      color, 12)
        try:
            fall_ref.update({
                'isDetected': True,
                'last_fall_time': datetime.now().strftime("%H:%M:%S")
            })
            print("🚨 Fall detected!")
        except Exception as e:
            print("Firebase Error:", e)
    else:
        color = (0, 255, 0)

    # --- Display ---
    label = f'STATUS: {final_status} ({confidence_score:.2f})'
    cv2.putText(frame, label, (40, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)

    # بيوضح لو ViT اشتغل أو لا
    cv2.putText(frame,
                "ViT: ON (suspicious)" if confidence_score > 0 else "ViT: OFF",
                (40, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 165, 255) if confidence_score > 0 else (200, 200, 200),
                2)

    cv2.imshow('AI Fall Detection (GPU Optimized)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
try:
    fall_ref.update({'isDetected': False})
except:
    pass

cap.release()
cv2.destroyAllWindows()