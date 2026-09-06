import cv2
import serial
import time
import numpy as np

# ۱. تنظیم پورت سریال (شماره COM را بر اساس سیستم خودت تغییر بده)
# سرعت 115200 برای انتقال سریع فریم‌ها مناسب است
try:
    ser = serial.Serial('COM10', 115200, timeout=1)
    print("ارتباط سریال با برد برقرار شد.")
except Exception as e:
    print("خطا در اتصال به پورت سریال. لطفاً شماره COM را بررسی کنید.")
    exit()

# ۲. روشن کردن وب‌کم
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # ۳. پیش‌پردازش (دقیقاً مشابه مراحل قبلی)
    h, w, _ = frame.shape
    min_dim = min(h, w)
    start_x = (w - min_dim) // 2
    start_y = (h - min_dim) // 2
    cropped = frame[start_y:start_y+min_dim, start_x:start_x+min_dim]
    
    resized = cv2.resize(cropped, (96, 96))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    # ۴. ارسال داده‌ها به برد
    # ما پیکسل‌ها را به صورت اعداد صحیح (0 تا 255) می‌فرستیم تا حجم داده کم باشد (حدود ۹ کیلوبایت)
    # برد خودش تقسیم بر 255 را انجام می‌دهد
    flat_data = gray.flatten().tobytes()
    ser.write(flat_data)
    
    # ۵. خواندن جواب از برد
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8').strip()
        
        # نمایش نتیجه روی تصویر
        color = (0, 255, 0) if "Person" in response else (0, 0, 255)
        cv2.putText(frame, f"Board Says: {response}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    
    cv2.imshow('PC to MicroBluePy', frame)
    
    # برای جلوگیری از پر شدن بافر سریال، کمی تاخیر می‌دهیم
    time.sleep(0.1)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()