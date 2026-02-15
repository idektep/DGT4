import cv2
import numpy as np

def check_ballot(image_path):
    # 1. โหลดและคุมขนาดภาพให้เท่ากันทุกใบ (สำคัญมากสำหรับโจทย์ฝึก)
    img = cv2.imread(image_path)
    img = cv2.resize(img, (400, 800)) 
    
    # 2. ทำภาพเป็นขาวดำเพื่อหาเส้น
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150) # หาขอบรอยปากกา

    # 3. กำหนดสัดส่วนตาราง (9 แถว 2 คอลัมน์)
    row_h = 800 // 9
    col_w = 400 // 2
    
    results = []

    # 4. Loop ตรวจตั้งแต่แถวที่ 2 เป็นต้นไป (ข้ามหัวตาราง)
    for i in range(1, 9):
        # ตัดเอาเฉพาะช่องกากบาท (คอลัมน์ขวา)
        # หดขอบเข้ามาข้างละ 10px เพื่อไม่ให้ติดเส้นตาราง
        roi = edges[i*row_h+10 : (i+1)*row_h-10, col_w+10 : 400-10]
        
        # 5. ตรวจหาเส้นตรง (Hough Line Transform)
        lines = cv2.HoughLinesP(roi, 1, np.pi/180, threshold=15, minLineLength=10, maxLineGap=5)
        
        if lines is not None:
            has_left_slash = False
            has_right_slash = False
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                
                # เช็คเส้นเอียงซ้าย (\) และ เอียงขวา (/)
                if 10 < angle < 80: has_left_slash = True
                if -80 < angle < -10: has_right_slash = True
            
            # บัตรดี = ต้องมีเส้นตัดกัน 2 ทิศทาง
            if has_left_slash and has_right_slash:
                results.append(i) # เก็บหมายเลขบรรทัด (เบอร์ผู้สมัคร)

    # 6. แสดงผลลัพธ์
    if len(results) == 1:
        print(f"ผลการตรวจ {image_path}: บัตรดี (เลือกเบอร์ {results[0]})")
    else:
        print(f"ผลการตรวจ {image_path}: บัตรเสีย")

# รันโจทย์ฝึกหัด 1-7
for i in range(1, 8):
    check_ballot(f"{i}.png")