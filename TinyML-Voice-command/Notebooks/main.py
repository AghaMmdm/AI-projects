import gc
gc.collect()

import machine
from machine import I2S, Pin
import time
import math
import struct

# ==========================================
# 1. MEMORY PRE-ALLOCATION
# ==========================================
SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  
RECORD_SECONDS = 0.6 # 0.6 ثانیه برای کلمات کوتاه کافیست
BUFFER_LENGTH = int(SAMPLE_RATE * 2 * RECORD_SECONDS)

word_buffer = bytearray(BUFFER_LENGTH)
audio_buffer = bytearray(CHUNK_SIZE)

gc.collect()

import model_data_lr
gc.collect()

# ==========================================
# 2. HARDWARE CONFIGURATION
# ==========================================
SCK_PIN = 'Y6'
WS_PIN = 'Y5'
SD_PIN = 'Y8'

try:
    audio_in = I2S(
        2, 
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
        mode=I2S.RX,
        bits=16,
        format=I2S.MONO,
        rate=SAMPLE_RATE,
        ibuf=4096 
    )
except MemoryError:
    print("FATAL ERROR: RAM fragmented. Reset board!")
    machine.reset()

# ==========================================
# 3. ZERO-RAM VAD (Voice Activity Detection)
# ==========================================
def calculate_energy(buffer):
    sum_squares = 0.0
    buffer_len = len(buffer)
    for i in range(0, buffer_len, 2):
        val = buffer[i] | (buffer[i+1] << 8)
        if val >= 32768:
            val -= 65536
        sum_squares += val * val
        
    num_samples = buffer_len // 2
    if num_samples == 0: return 0
    return (sum_squares / num_samples) ** 0.5

def calibrate_noise_level(duration_sec=2.0):
    print("Calibrating environment noise... Keep quiet!")
    total_energy = 0
    num_chunks = int((SAMPLE_RATE * 2) / CHUNK_SIZE) * int(duration_sec)
    
    for _ in range(num_chunks):
        num_bytes_read = audio_in.readinto(audio_buffer)
        if num_bytes_read > 0:
            total_energy += calculate_energy(audio_buffer)
            
    mean_noise_energy = total_energy / num_chunks
    # ضریب 3.0 برای جلوگیری از تریگر شدن با نویزهای ریز
    noise_threshold = mean_noise_energy * 3.0 
    print(f"Calibration Done! Threshold: {noise_threshold:.2f}")
    return noise_threshold

# ==========================================
# 4. ZERO-RAM FEATURE EXTRACTION (MFCC Approx)
# ==========================================
def compute_pseudo_mfcc(raw_buffer, start_byte, end_byte, num_coeffs=13):
    """
    محاسبه ویژگی‌ها مستقیماً روی بافر خام بدون اشغال رَم جدید
    """
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
            # خواندن مستقیم اعداد 16 بیتی از بافر اصلی
            val = raw_buffer[j] | (raw_buffer[j+1] << 8)
            if val >= 32768: 
                val -= 65536
            
            chunk_energy += abs(val)
            sign = 1 if val > 0 else -1 if val < 0 else 0
            if sign != 0 and sign != last_sign:
                zero_crossings += 1
                last_sign = sign
                
        # میانگین‌گیری برای جلوگیری از سرریز اعداد
        mean_energy = chunk_energy / samples_per_chunk if samples_per_chunk > 0 else 0
        features[i] = (mean_energy * 0.1) + (zero_crossings * 0.5)
        
    return features

def extract_39_features(raw_buffer):
    """
    تقسیم مجازی بافر به 3 قسمت (بدون کپی کردن)
    """
    buffer_len = len(raw_buffer)
    
    # محاسبه طول هر بخش به بایت (باید زوج باشد)
    bytes_per_part = ((buffer_len // 2) // 3) * 2
    
    part1_start = 0
    part1_end = bytes_per_part
    
    part2_start = part1_end
    part2_end = part1_end + bytes_per_part
    
    part3_start = part2_end
    part3_end = part2_end + bytes_per_part
    
    # ارسال آدرس بایت‌ها به جای کپی کردن کل آرایه
    mfcc1 = compute_pseudo_mfcc(raw_buffer, part1_start, part1_end, 13)
    mfcc2 = compute_pseudo_mfcc(raw_buffer, part2_start, part2_end, 13)
    mfcc3 = compute_pseudo_mfcc(raw_buffer, part3_start, part3_end, 13)
    
    return mfcc1 + mfcc2 + mfcc3

# ==========================================
# 5. INFERENCE ENGINE (LDA + Logistic Regression)
# ==========================================
def predict_audio_class(mfcc_features):
    num_original_features = 39 
    num_super_features = 3     
    num_classes = len(model_data_lr.CLASSES)
    
    # اعمال ماتریس LDA
    lda_features = [0.0] * num_super_features
    for i in range(num_super_features):
        sum_val = 0.0
        for j in range(num_original_features):
            sum_val += mfcc_features[j] * model_data_lr.LDA_SCALINGS[j][i]
        lda_features[i] = sum_val
        
    # رگرسیون لجستیک
    class_scores = [0.0] * num_classes
    for c in range(num_classes):
        score = model_data_lr.LR_INTERCEPT[0][c]
        for i in range(num_super_features):
            score += lda_features[i] * model_data_lr.LR_COEF[c][i]
        class_scores[c] = score
        
    # پیدا کردن بیشترین امتیاز
    best_class = 0
    max_score = class_scores[0]
    for i in range(1, num_classes):
        if class_scores[i] > max_score:
            max_score = class_scores[i]
            best_class = i
            
    return best_class

# ==========================================
# 6. MAIN LOOP
# ==========================================
def main():
    time.sleep(1) 
    threshold = calibrate_noise_level(duration_sec=2.0)
    print("\nMicrophone is READY. Say 'On', 'Off', or 'Stop'...")
    
    while True:
        num_bytes_read = audio_in.readinto(audio_buffer)
        
        if num_bytes_read > 0:
            current_energy = calculate_energy(audio_buffer)
            
            # تشخیص شروع کلمه
            if current_energy > threshold:
                print(f"Recording {RECORD_SECONDS}s...")
                
                # کپی کردن بافر فعلی به ابتدای بافر اصلی
                word_buffer[0:CHUNK_SIZE] = audio_buffer
                # خواندن ادامه صدا تا پر شدن بافر 0.6 ثانیه‌ای
                bytes_to_read = BUFFER_LENGTH - CHUNK_SIZE
                audio_in.readinto(memoryview(word_buffer)[CHUNK_SIZE:BUFFER_LENGTH])
                
                # 1. استخراج ۳۹ ویژگی از صدای خام (همانند پایتون سرور)
                features = extract_39_features(word_buffer)
                
                # 2. استنتاج و پیش‌بینی کلمه
                result_idx = predict_audio_class(features)
                predicted_word = model_data_lr.CLASSES[result_idx]
                
                if predicted_word != 'unknown':
                    print(f">>> PREDICTED: {predicted_word.upper()} <<<\n")
                else:
                    print("--- Unknown/Noise ---")
                
                # آزادسازی رم و مکث کوتاه برای جلوگیری از تشخیص تکراری
                gc.collect()
                time.sleep(0.5)
                print("Listening...")

if __name__ == '__main__':
    main()