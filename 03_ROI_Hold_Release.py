import cv2
import time

# ===== TUNE HERE =====
SCALE_FACTOR = 1.15
MIN_NEIGHBORS = 6
MIN_SIZE = (80, 80)

HOLD_TIME = 1.0
RELEASE_TIME = 1.2
# =====================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)

state = "IDLE"
detect_start = None
lost_start = None

print("ESC to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape

    # ROI: middle 60%
    rx1, rx2 = int(w * 0.2), int(w * 0.8)
    ry1, ry2 = int(h * 0.2), int(h * 0.8)

    roi = frame[ry1:ry2, rx1:rx2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=SCALE_FACTOR,
        minNeighbors=MIN_NEIGHBORS,
        minSize=MIN_SIZE
    )

    count = len(faces)
    now = time.time()

    # Draw ROI border on full frame
    cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)

    # Draw detected faces (mapped back to full frame)
    for (x, y, fw, fh) in faces:
        cv2.rectangle(frame, (rx1 + x, ry1 + y), (rx1 + x + fw, ry1 + y + fh), (0, 255, 0), 2)

    # HOLD / RELEASE logic
    if count > 0:
        lost_start = None
        if detect_start is None:
            detect_start = now
        elif now - detect_start >= HOLD_TIME:
            state = "ACTIVE"
    else:
        detect_start = None
        if lost_start is None:
            lost_start = now
        elif now - lost_start >= RELEASE_TIME:
            state = "IDLE"

    cv2.putText(frame, f"count={count} state={state}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Stable Face (ROI + Hold/Release)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
