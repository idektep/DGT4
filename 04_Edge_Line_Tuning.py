import cv2
import numpy as np

# ===== TUNE HERE =====
CANNY_LOW = 50
CANNY_HIGH = 150

HOUGH_THRESHOLD = 20
MIN_LINE_LENGTH = 40
MAX_LINE_GAP = 5
# =====================

cap = cv2.VideoCapture(0)
print("ESC to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=HOUGH_THRESHOLD,
        minLineLength=MIN_LINE_LENGTH,
        maxLineGap=MAX_LINE_GAP
    )

    overlay = frame.copy()
    if lines is not None:
        for (x1, y1, x2, y2) in lines[:, 0]:
            cv2.line(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.putText(overlay,
                f"Canny({CANNY_LOW},{CANNY_HIGH}) Hough(th={HOUGH_THRESHOLD},len={MIN_LINE_LENGTH},gap={MAX_LINE_GAP})",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Edges", edges)
    cv2.imshow("Lines Overlay", overlay)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
