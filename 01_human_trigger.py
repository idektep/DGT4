import cv2
import paho.mqtt.client as mqtt
import time

# ======================
# MQTT CONFIG
# ======================
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC_STATUS = "dgt1/smartcam/status"

# ======================
# MQTT SETUP
# ======================
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# ======================
# LOAD FACE CASCADE
# (comes with OpenCV)
# ======================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ======================
# CAMERA
# ======================
cap = cv2.VideoCapture(0)

prev_detected = False

print("[CV] SmartCam started")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(60, 60)
    )

    detected = len(faces) > 0

    # ======================
    # EVENT LOGIC
    # ======================
    if detected and not prev_detected:
        print("[EVENT] detect")
        client.publish(TOPIC_STATUS, "detect")

    if not detected and prev_detected:
        print("[EVENT] clear")
        client.publish(TOPIC_STATUS, "clear")

    prev_detected = detected

    # ======================
    # DRAW DEBUG
    # ======================
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.putText(
        frame,
        f"Faces: {len(faces)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0) if detected else (0, 0, 255),
        2
    )

    cv2.imshow("SmartCam (Face Detection)", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

# ======================
# CLEANUP
# ======================
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
