import cv2, time, json, math
from collections import deque
import mediapipe as mp
import paho.mqtt.client as mqtt

# ===== MQTT =====
BROKER = "localhost"
PORT = 1883
PERSON = "person1"
TOPIC_JOINTS = f"dt/vision/{PERSON}/joints"
TOPIC_STATE  = f"dt/vision/{PERSON}/state"
TOPIC_EVENT  = f"dt/vision/{PERSON}/event"

PUB_HZ = 15

# ===== Pose / thresholds =====
CAM_INDEX = 0
MIN_VIS = 0.6
ANGLE_STAND_DEG = 25
ANGLE_LIE_DEG   = 60
DROP_WINDOW_SEC = 0.5
DROP_THRESH     = 0.18
HOLD_FRAMES     = 8
COOLDOWN_SEC    = 3.0

mp_pose = mp.solutions.pose

JOINTS = {
    "head": 0,
    "shoulder_l": 11, "shoulder_r": 12,
    "elbow_l": 13, "elbow_r": 14,
    "wrist_l": 15, "wrist_r": 16,
    "hip_l": 23, "hip_r": 24,
    "knee_l": 25, "knee_r": 26,
    "ankle_l": 27, "ankle_r": 28,
}

def get_lm(lms, idx):
    lm = lms.landmark[idx]
    return lm.x, lm.y, lm.visibility

def angle_from_vertical(dx, dy):
    return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))

class FSM:
    def __init__(self):
        self.state = "UNKNOWN"
        self.hold = 0
        self.cooldown_until = 0.0
        self.hip_hist = deque()

    def update(self, ok_pose, angle, hip_y):
        now = time.time()

        if now < self.cooldown_until:
            return "COOLDOWN", "", 0.0

        drop = 0.0
        if ok_pose:
            self.hip_hist.append((now, hip_y))
            while self.hip_hist and (now - self.hip_hist[0][0]) > DROP_WINDOW_SEC:
                self.hip_hist.popleft()
            if len(self.hip_hist) >= 2:
                drop = self.hip_hist[-1][1] - self.hip_hist[0][1]

        lying_like = ok_pose and (angle >= ANGLE_LIE_DEG)
        stand_like = ok_pose and (angle <= ANGLE_STAND_DEG)
        fall_candidate = lying_like and (drop >= DROP_THRESH)

        if fall_candidate:
            self.hold += 1
            if self.hold >= HOLD_FRAMES:
                self.hold = 0
                self.cooldown_until = now + COOLDOWN_SEC
                self.hip_hist.clear()
                self.state = "LYING"
                return self.state, "FALL", drop
            return "FALLING", "", drop

        self.hold = max(0, self.hold - 1)
        if lying_like:
            self.state = "LYING"
        elif stand_like:
            self.state = "STANDING"

        return self.state, "", drop

def main():
    mc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mc.connect(BROKER, PORT, 60)
    mc.loop_start()

    cap = cv2.VideoCapture(CAM_INDEX)
    fsm = FSM()

    interval = 1.0 / max(1, PUB_HZ)
    last_pub = 0.0

    with mp_pose.Pose(static_image_mode=False, model_complexity=1,
                      enable_segmentation=False,
                      min_detection_confidence=0.6,
                      min_tracking_confidence=0.6) as pose:

        while True:
            ok, frame = cap.read()
            if not ok: break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            ok_pose = False
            angle = 0.0
            hip_y = 0.0
            joints_list = []

            if res.pose_landmarks:
                lms = res.pose_landmarks
                sx1, sy1, sv1 = get_lm(lms, 11)
                sx2, sy2, sv2 = get_lm(lms, 12)
                hx1, hy1, hv1 = get_lm(lms, 23)
                hx2, hy2, hv2 = get_lm(lms, 24)

                if min(sv1, sv2, hv1, hv2) >= MIN_VIS:
                    ok_pose = True
                    sh_x = (sx1 + sx2) / 2
                    sh_y = (sy1 + sy2) / 2
                    hip_x = (hx1 + hx2) / 2
                    hip_y = (hy1 + hy2) / 2
                    angle = angle_from_vertical(sh_x - hip_x, sh_y - hip_y)

                for name, idx in JOINTS.items():
                    x, y, v = get_lm(lms, idx)
                    joints_list.append({"name": name, "x": float(x), "y": float(y), "v": float(v)})

            state, eventName, drop = fsm.update(ok_pose, angle, hip_y)
            now = time.time()

            if (now - last_pub) >= interval:
                last_pub = now

                mc.publish(TOPIC_JOINTS, json.dumps({"ts": now, "id": PERSON, "joints": joints_list}),
                           qos=0, retain=False)

                mc.publish(TOPIC_STATE, json.dumps({
                    "ts": now, "id": PERSON, "state": state,
                    "ok_pose": int(ok_pose),
                    "torso_angle": round(angle, 2),
                    "hip_y": round(hip_y, 4),
                    "drop": round(drop, 4)
                }), qos=0, retain=True)

                if eventName:
                    mc.publish(TOPIC_EVENT, json.dumps({
                        "ts": now, "id": PERSON, "eventName": eventName,
                        "torso_angle": round(angle, 2),
                        "drop": round(drop, 4)
                    }), qos=0, retain=False)

            cv2.putText(frame, f"{state} {eventName}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            cv2.imshow("04_pose_fall_mqtt_runtime", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()