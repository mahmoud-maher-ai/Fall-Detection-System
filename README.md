#  AI-Based Fall Detection System

An advanced, real-time fall detection system combining state-of-the-art Computer Vision and Deep Learning techniques to ensure immediate safety responses. 

##  Key Features
* **Pose Estimation:** Powered by **YOLOv8-Pose** for high-accuracy human keypoint tracking.
* **Sequence Classification:** Uses a **Vision Transformer (ViT)** architecture to analyze temporal motion frames and detect falls.
* **Real-time Alerts:** Integrated with **Firebase Realtime Database** for instant notification routing.
* **Edge-Ready Architecture:** Built with Python for modular deployment.

---

##  System Architecture & Workflow
1. **Video/Camera Input:** Captures real-time frames from the source video.
2. **YOLOv8 Inference:** Extracts skeleton keypoints and bounding boxes from the human subject.
3. **ViT Classification:** The Vision Transformer processes temporal sequences to determine if a transition signifies a 'Fall' or normal movement.
4. **Firebase Trigger:** If a fall event is confirmed, an alert payload is instantly pushed to the Firebase Realtime Database.

---

##  Tech Stack
* **Languages:** Python
* **AI & Deep Learning:** PyTorch, Ultralytics YOLOv8, Vision Transformers (ViT)
* **Computer Vision:** OpenCV (cv2)
* **Cloud Infrastructure:** Firebase Realtime Database

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
```bash
git clone [https://github.com/mahmoud-maher-ai/Fall-Detection-System.git](https://github.com/mahmoud-maher-ai/Fall-Detection-System.git)
