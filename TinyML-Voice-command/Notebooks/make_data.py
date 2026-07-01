import gc
gc.collect()
import machine
from machine import I2S, Pin
import time

# ==========================================
# 1. SETTINGS & PRE-ALLOCATION
# ==========================================
CLASSES = ["on", "off", "stop", "unknown"]
SAMPLES_PER_CLASS = 10  # تعداد دفعاتی که باید هر کلمه را تکرار کنید

SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  
RECORD_SECONDS = 1.0  
BUFFER_LENGTH = int(SAMPLE_RATE * 2 * RECORD_SECONDS)

word_buffer = bytearray(BUFFER_LENGTH)
audio_buffer = bytearray(CHUNK_SIZE)
gc.collect()

# ==========================================
# 2. HARDWARE CONFIGURATION
# ==========================================
audio_in = I2S(2, sck=Pin('Y6'), ws=Pin('Y5'), sd=Pin('Y8'), 
               mode=I2S.RX, bits=16, format=I2S.MONO, 
               rate=SAMPLE_RATE, ibuf=4096)

# ==========================================
# 3. VAD & CALIBRATION
# ==========================================
def calculate_energy(buffer):
    sum_squares = 0.0
    buffer_len = len(buffer)
    for i in range(0, buffer_len, 2):
        val = buffer[i] | (buffer[i+1] << 8)
        if val >= 32768: val -= 65536
        sum_squares += val * val
    num_samples = buffer_len // 2
    if num_samples == 0: return 0
    return (sum_squares / num_samples) ** 0.5

def calibrate_noise_level(duration_sec=2.0):
    print("Calibrating... Keep quiet for 2 seconds!")
    total_energy = 0
    num_chunks = int((SAMPLE_RATE * 2) / CHUNK_SIZE) * int(duration_sec)
    for _ in range(num_chunks):
        if audio_in.readinto(audio_buffer) > 0:
            total_energy += calculate_energy(audio_buffer)
    noise_threshold = (total_energy / num_chunks) * 2.0 
    return noise_threshold

# ==========================================
# 4. ZERO-RAM FEATURE EXTRACTION
# ==========================================
def compute_pseudo_mfcc(raw_buffer, start_byte, end_byte, num_coeffs=13):
    features = [0.0] * num_coeffs
    total_samples = (end_byte - start_byte) // 2
    samples_per_chunk = total_samples // num_coeffs
    bytes_per_chunk = samples_per_chunk * 2
    
    for i in range(num_coeffs):
        chunk_start = start_byte + i * bytes_per_chunk
        chunk_end = chunk_start + bytes_per_chunk
        chunk_energy = 0.0
        zero_crossings = 0
        last_sign = 0
        
        for j in range(chunk_start, chunk_end, 2):
            val = raw_buffer[j] | (raw_buffer[j+1] << 8)
            if val >= 32768: val -= 65536
            chunk_energy += abs(val)
            sign = 1 if val > 0 else -1 if val < 0 else 0
            if sign != 0 and sign != last_sign:
                zero_crossings += 1
                last_sign = sign
                
        mean_energy = chunk_energy / samples_per_chunk if samples_per_chunk > 0 else 0
        features[i] = (mean_energy * 0.1) + (zero_crossings * 0.5)
    return features

def extract_39_features(raw_buffer):
    buffer_len = len(raw_buffer)
    bytes_per_part = ((buffer_len // 2) // 3) * 2
    p1_s, p1_e = 0, bytes_per_part
    p2_s, p2_e = p1_e, p1_e + bytes_per_part
    p3_s, p3_e = p2_e, p2_e + bytes_per_part
    
    m1 = compute_pseudo_mfcc(raw_buffer, p1_s, p1_e, 13)
    m2 = compute_pseudo_mfcc(raw_buffer, p2_s, p2_e, 13)
    m3 = compute_pseudo_mfcc(raw_buffer, p3_s, p3_e, 13)
    return m1 + m2 + m3

# ==========================================
# 5. DATASET BUILDER LOOP
# ==========================================
def main():
    time.sleep(1) 
    threshold = calibrate_noise_level(duration_sec=2.0)
    
    # باز کردن فایل روی SD کارت با قابلیت اضافه کردن (Append)
    # اگر برد ریست شود، دیتای قبلی پاک نمی‌شود
    filename = 'dataset.csv'
    print(f"\n[ SYSTEM READY ] Threshold set to {threshold:.2f}")
    print(f"Data will be saved directly to SD Card: {filename}\n")
    
    for label in CLASSES:
        print("=========================================")
        print(f"   PREPARE TO RECORD CLASS: >> {label.upper()} <<")
        
        if label == "unknown":
            print("   (Make random noises, cough, say other words)")
            
        print("=========================================")
        time.sleep(3) # فرصت برای آماده شدن شما
        
        sample_count = 0
        while sample_count < SAMPLES_PER_CLASS:
            if audio_in.readinto(audio_buffer) > 0:
                # منتظر شنیدن صدا...
                if calculate_energy(audio_buffer) > threshold:
                    print(f"Recording '{label}' ({sample_count + 1}/{SAMPLES_PER_CLASS})...", end="")
                    
                    # ضبط 1 ثانیه کامل
                    word_buffer[0:CHUNK_SIZE] = audio_buffer
                    audio_in.readinto(memoryview(word_buffer)[CHUNK_SIZE:BUFFER_LENGTH])
                    
                    # استخراج ۳۹ ویژگی
                    features = extract_39_features(word_buffer)
                    
                    # ذخیره در فایل به فرمت CSV
                    with open(filename, 'a') as f:
                        # فرمت: برچسب,ویژگی1,ویژگی2,...,ویژگی39
                        str_features = ",".join([f"{x:.4f}" for x in features])
                        f.write(f"{label},{str_features}\n")
                        
                    print(" Saved!")
                    sample_count += 1
                    
                    gc.collect()
                    time.sleep(1) # یک ثانیه توقف تا صدای نفس کشیدن شما را به عنوان کلمه جدید ثبت نکند
                    
    print("\n=========================================")
    print("   DATA COLLECTION COMPLETE! AWESOME!   ")
    print("   You can now take out the SD Card.    ")
    print("=========================================")

if __name__ == '__main__':
    main()