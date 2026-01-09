import cv2
import paho.mqtt.client as mqtt
import time

# =========================
# MQTT CONFIG
# =========================
BROKER = "broker.emqx.io"
PORT = 1883
TOPIC = "dgt/smartcam/status"

# =========================
# MQTT CLIENT
# =========================
client = mqtt.Client(client_id="smartcam_face")
client.connect(BROKER, PORT, 60)
client.loop_start()

# =========================
# OPENCV SETUP
# =========================
cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

face_present = False
detect_confirm = 0
CONFIRM_FRAMES = 3   # debounce

print("📷 SmartCam started (Face Detection Trigger)")

# =========================
# MAIN LOOP
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,     # เพิ่ม = เข้มงวดขึ้น
        minSize=(60, 60)   # กัน noise เล็ก ๆ
    )

    face_count = len(faces)

    # ─────────────────────
    # DEBOUNCE + EDGE TRIGGER
    # ─────────────────────
    if face_count > 0:
        detect_confirm += 1
    else:
        detect_confirm = 0
        if face_present:
            print("🙂 No face → Reset state")
            face_present = False

    if detect_confirm >= CONFIRM_FRAMES and not face_present:
        client.publish(TOPIC, "detect")
        print("📤 Face detected → Send 'detect'")
        face_present = True

    # ─────────────────────
    # DRAW FACE BOX
    # ─────────────────────
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            frame,
            "Face",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"Faces: {face_count}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    cv2.imshow("SmartCam Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(0.1)

# =========================
# CLEANUP
# =========================
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
