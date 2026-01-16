import cv2
import time
import mediapipe as mp
import paho.mqtt.client as mqtt

# ======================
# MQTT CONFIG
# ======================
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC_CMD = "dgt/light/1/cmd"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# ======================
# MEDIAPIPE
# ======================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ======================
# CAMERA
# ======================
cap = cv2.VideoCapture(0)

# ======================
# BUTTON CONFIG
# ======================
HOLD_TIME = 1.5  # seconds

btn_on  = (50, 100, 250, 250)     # x1,y1,x2,y2
btn_off = (390, 100, 590, 250)

on_timer = None
off_timer = None

last_sent = None

print("[SYSTEM] MediaPipe Virtual Button Started")

# ======================
def inside(px, py, rect):
    x1, y1, x2, y2 = rect
    return x1 <= px <= x2 and y1 <= py <= y2

# ======================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    hand_x = hand_y = None

    if result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0].landmark[0]  # wrist
        hand_x = int(lm.x * w)
        hand_y = int(lm.y * h)
        cv2.circle(frame, (hand_x, hand_y), 10, (0,255,0), -1)

    now = time.time()

    # ===== ON BUTTON =====
    if hand_x and inside(hand_x, hand_y, btn_on):
        if on_timer is None:
            on_timer = now
        elif now - on_timer >= HOLD_TIME and last_sent != "on":
            print("[EVENT] LIGHT ON")
            client.publish(TOPIC_CMD, "on")
            last_sent = "on"
    else:
        on_timer = None

    # ===== OFF BUTTON =====
    if hand_x and inside(hand_x, hand_y, btn_off):
        if off_timer is None:
            off_timer = now
        elif now - off_timer >= HOLD_TIME and last_sent != "off":
            print("[EVENT] LIGHT OFF")
            client.publish(TOPIC_CMD, "off")
            last_sent = "off"
    else:
        off_timer = None

    # ======================
    # DRAW UI
    # ======================
    def draw_button(rect, label, timer):
        x1,y1,x2,y2 = rect
        color = (0,255,0) if timer and now - timer >= HOLD_TIME else (255,255,255)
        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
        cv2.putText(frame, label, (x1+40, y1+90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

    draw_button(btn_on,  "ON",  on_timer)
    draw_button(btn_off, "OFF", off_timer)

    cv2.imshow("MediaPipe Virtual Button", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# ======================
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
