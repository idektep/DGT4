import cv2, time, math
import mediapipe as mp

CAM_INDEX = 0
MIN_VIS = 0.6

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

def get_lm(lms, idx):
    lm = lms.landmark[idx]
    return lm.x, lm.y, lm.visibility

def angle_from_vertical(dx, dy):
    return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))

cap = cv2.VideoCapture(CAM_INDEX)

with mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as pose:

    prev = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)

        fps = 1.0 / max(1e-6, time.time() - prev)
        prev = time.time()

        ok_pose = False
        torso_angle = 0.0
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
                torso_angle = angle_from_vertical(sh_x - hip_x, sh_y - hip_y)

            mp_draw.draw_landmarks(frame, lms, mp_pose.POSE_CONNECTIONS)

        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame, f"ok_pose={int(ok_pose)}  torso_angle={torso_angle:.1f}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
        cv2.putText(frame, f"hip_y={hip_y:.3f} (y down in image)", (10, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        cv2.imshow("01_pose_features_viewer", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()