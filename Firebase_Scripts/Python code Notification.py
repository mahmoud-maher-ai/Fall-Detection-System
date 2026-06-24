# Fall Detection Notification - Python + Firebase
# تأكد إن serviceAccountKey.json موجود في نفس مجلد هذا الملف

import os
import firebase_admin
from firebase_admin import credentials, db, messaging

# ------------------------------
# 1️⃣ تهيئة Firebase
# ------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(current_dir, "serviceAccountKey.json")

# تحميل بيانات المفتاح
cred = credentials.Certificate(key_path)

# تهيئة التطبيق (غير الـ databaseURL باللي عندك في Firebase)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://falldetection-4f6fe-default-rtdb.europe-west1.firebasedatabase.app/'
})

# ------------------------------
# 2️⃣ دالة لإرسال حالة السقوط للـ Realtime Database
# ------------------------------
def send_to_firebase():
    try:
        ref = db.reference('fall')  # اسم العقدة اللي هتتخزن فيها الحالات
        new_fall = ref.push({"fall": True})
        print("Firebase DB response:", new_fall)
        return True
    except Exception as e:
        print("Error sending data to Firebase:", e)
        return False

# ------------------------------
# 3️⃣ دالة لإرسال Notification عبر FCM
# ------------------------------
def send_notification():
    try:
        # هنا بنرسل لكل الأجهزة المشتركه في topic 'caregiver'
        message = messaging.Message(
            notification=messaging.Notification(
                title="Fall Detected!",
                body="A fall event has been detected. Please check immediately."
            ),
            topic='caregiver'
        )
        response = messaging.send(message)
        print("Notification sent:", response)
    except Exception as e:
        print("Error sending notification:", e)

# ------------------------------
# 4️⃣ تشغيل الوظائف
# ------------------------------
if send_to_firebase():
    send_notification()