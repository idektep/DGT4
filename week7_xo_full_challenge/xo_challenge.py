
import os
import glob
import cv2
import numpy as np

CANNY_LOW = 50
CANNY_HIGH = 150

HOUGH_THRESHOLD = 30
MIN_LINE_LENGTH = 40
MAX_LINE_GAP = 10

ANGLE_MIN = 20
ANGLE_MAX = 70

RESIZE_W, RESIZE_H = 600, 600
GRID_ROWS, GRID_COLS = 4, 4
CELL_PAD = 18

def expected_from_filename(filename: str) -> str:
    f = filename.lower()
    if "double" in f:
        return "INVALID_DOUBLE"
    if "none" in f:
        return "INVALID_NONE"
    if "valid" in f:
        return "VALID"
    return "UNKNOWN"

def detect_x_in_roi(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)
    lines = cv2.HoughLinesP(edges,1,np.pi/180,HOUGH_THRESHOLD,
                            minLineLength=MIN_LINE_LENGTH,
                            maxLineGap=MAX_LINE_GAP)

    angles = []
    if lines is None:
        return False

    for x1,y1,x2,y2 in lines[:,0]:
        angle = np.degrees(np.arctan2(y2-y1, x2-x1))
        if ANGLE_MIN < abs(angle) < ANGLE_MAX:
            angles.append(angle)

    has_pos = any(a>0 for a in angles)
    has_neg = any(a<0 for a in angles)

    return has_pos and has_neg

def analyze_image(path):
    img = cv2.imread(path)
    img = cv2.resize(img,(RESIZE_W,RESIZE_H))
    h,w,_ = img.shape
    cell_w = w//GRID_COLS
    cell_h = h//GRID_ROWS

    total_x = 0

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x1 = c*cell_w
            y1 = r*cell_h
            x2 = (c+1)*cell_w
            y2 = (r+1)*cell_h

            roi = img[y1+CELL_PAD:y2-CELL_PAD,
                      x1+CELL_PAD:x2-CELL_PAD]

            if detect_x_in_roi(roi):
                total_x += 1

    if total_x == 1:
        return "VALID"
    elif total_x == 0:
        return "INVALID_NONE"
    else:
        return "INVALID_DOUBLE"

if __name__ == "__main__":
    files = sorted(glob.glob("week7/week7_xo_full_challenge/images/*.png"))
    print("\n=== XO TABLE ===")
    for f in files:
        expected = expected_from_filename(f)
        result = analyze_image(f)
        mark = "O" if expected == result else "X"
        print(os.path.basename(f), "=>", result, "|", mark)
