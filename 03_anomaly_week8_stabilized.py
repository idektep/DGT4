import cv2, time, math
from collections import deque
import mediapipe as mp

CAM_INDEX = 0
MIN_VIS = 0.6

ANGLE_STAND_DEG = 25
ANGLE_LIE_DEG = 60

DROP_WINDOW_SEC = 0.5
DROP_THRESH = 0.18

HOLD_FRAMES = 8
COOLDOWN_SEC = 3.0

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

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

        # cooldown
        if now < self.cooldown_until:
            return "COOLDOWN", "", 0.0

        # update drop window
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

        # confirm fall by HOLD_FRAMES
        if fall_candidate:
            self.hold += 1
            if self.hold >= HOLD_FRAMES:
                self.hold = 0
                self.cooldown_until = now + COOLDOWN_SEC
                self.hip_hist.clear()
                self.state = "LYING"
                return self.state, "FALL", drop
            return "FALLING", "", drop

        # posture update
        self.hold = max(0, self.hold - 1)
        if lying_like:
            self.state = "LYING"
        elif stand_like:
            self.state = "STANDING"
        # else keep previous

        return self.state, "", drop

cap = cv2.VideoCapture(CAM_INDEX)
fsm = FSM()

with mp_pose.Pose(static_image_mode=False, model_complexity=1,
                  enable_segmentation=False,
                  min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:

    while True:
        ok, frame = cap.read()
        if not ok: break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)

        ok_pose = False
        angle = 0.0
        hip_y = 0.0

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

            mp_draw.draw_landmarks(frame, lms, mp_pose.POSE_CONNECTIONS)

        state, eventName, drop = fsm.update(ok_pose, angle, hip_y)

        # severity help for tuning (0..1-ish)
        sev_drop = max(0.0, min(1.0, drop / max(1e-6, DROP_THRESH)))
        sev_ang = max(0.0, min(1.0, (angle - ANGLE_STAND_DEG) / max(1e-6, (ANGLE_LIE_DEG - ANGLE_STAND_DEG))))
        score = 0.5 * sev_drop + 0.5 * sev_ang  # just for visualization

        cv2.putText(frame, f"STATE={state} EVENT={eventName}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(frame, f"angle={angle:.1f} drop={drop:.3f} score={score:.2f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
        cv2.putText(frame, f"hold={fsm.hold}/{HOLD_FRAMES}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        cv2.imshow("03_anomaly_week8_stabilized", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()