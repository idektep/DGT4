import cv2
import time
import paho.mqtt.client as mqtt

# =====================
# MQTT CONFIG
# =====================
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC_COUNT = "dgt/vision/face_count"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# =====================
# OPENCV FACE DETECTOR
# =====================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)

last_sent = None
last_pub_time = 0
PUB_INTERVAL = 0.25  # ส่งได้สูงสุดทุก 0.25 วิ

print("[SYSTEM] Face Count → MQTT Started (press q to quit)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    count = len(faces)
    now = time.time()

    # ส่งเมื่อค่าเปลี่ยน หรือครบเวลา interval
    if count != last_sent or (now - last_pub_time) >= PUB_INTERVAL:
        client.publish(TOPIC_COUNT, str(count))
        print(f"[MQTT] {TOPIC_COUNT} = {count}")
        last_sent = count
        last_pub_time = now

    # วาดกรอบ
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.putText(frame, f"Count: {count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Face Count MQTT", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
