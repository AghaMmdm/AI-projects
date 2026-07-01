import gc
gc.collect()
import machine
from machine import I2S, Pin
import time

# Import the compiled machine learning model
import model_data_lr_realtime

# ==========================================
# 1. SETTINGS & PRE-ALLOCATION
# ==========================================
SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  # 0.1 seconds of audio chunk
RECORD_SECONDS = 1.0  
BUFFER_LENGTH = int(SAMPLE_RATE * 2 * RECORD_SECONDS)

# Memory allocation for recording
word_buffer = bytearray(BUFFER_LENGTH)

# Dual buffers for the Pre-roll History Buffer technique (Real-time clipping prevention)
history_buf = bytearray(CHUNK_SIZE)
current_buf = bytearray(CHUNK_SIZE)

gc.collect()

# ==========================================
# 2. HARDWARE CONFIGURATION
# ==========================================
audio_in = I2S(2, sck=Pin('Y6'), ws=Pin('Y5'), sd=Pin('Y8'), 
               mode=I2S.RX, bits=16, format=I2S.MONO, 
               rate=SAMPLE_RATE, ibuf=4096)

# ==========================================
# 3. VAD (Voice Activity Detection)
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
    print("Calibrating ambient noise... Keep quiet for 2 seconds!")
    total_energy = 0
    num_chunks = int((SAMPLE_RATE * 2) / CHUNK_SIZE) * int(duration_sec)
    for _ in range(num_chunks):
        if audio_in.readinto(current_buf) > 0:
            total_energy += calculate_energy(current_buf)
            
    # Set threshold to 2.0x the average ambient noise
    noise_threshold = (total_energy / num_chunks) * 2.0 
    return noise_threshold

# ==========================================
# 4. FEATURE EXTRACTION
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
# 5. CLASSIFICATION PIPELINE (LDA + LR)
# ==========================================
def predict_audio_class(features):
    num_original_features = 39
    
    # Dynamically extract dimensions from the imported model
    num_super_features = len(model_data_lr.LDA_SCALINGS[0]) 
    num_classes = len(model_data_lr.CLASSES)
    
    # STAGE 1: LDA Transformation (Dimensionality Reduction)
    lda_features = [0.0] * num_super_features
    for i in range(num_super_features):
        sum_val = 0.0
        for j in range(num_original_features):
            # Apply XBAR subtraction (Mean Centering) for maximum accuracy
            adjusted_feature = features[j] - model_data_lr.LDA_XBAR[j]
            sum_val += adjusted_feature * model_data_lr.LDA_SCALINGS[j][i]
        lda_features[i] = sum_val
        
    # STAGE 2: Logistic Regression Inference
    best_score = -999999.0
    best_class = "unknown"
    
    for c in range(num_classes):
        score = model_data_lr.LR_INTERCEPT[c]
        for i in range(num_super_features):
            score += lda_features[i] * model_data_lr.LR_COEF[c][i]
            
        if score > best_score:
            best_score = score
            best_class = model_data_lr.CLASSES[c]
            
    return best_class

# ==========================================
# 6. MAIN REAL-TIME LOOP
# ==========================================
def main():
    global history_buf, current_buf
    
    time.sleep(1)
    threshold = calibrate_noise_level(duration_sec=2.0)
    
    print(f"\n[ SYSTEM READY ] Threshold set to {threshold:.2f}")
    valid_commands = [c.upper() for c in model_data_lr.CLASSES if c != 'unknown']
    print(f"Listening for commands: {valid_commands}")
    print("-" * 40)
    
    while True:
        if audio_in.readinto(current_buf) > 0:
            
            # Check if current audio energy triggers the VAD threshold
            if calculate_energy(current_buf) > threshold:
                
                # VAD Triggered! Assemble the word buffer using the history pre-roll
                word_buffer[0:CHUNK_SIZE] = history_buf
                word_buffer[CHUNK_SIZE:2*CHUNK_SIZE] = current_buf
                
                # Stream the remainder of the 1-second audio window
                audio_in.readinto(memoryview(word_buffer)[2*CHUNK_SIZE:])
                
                # Extract features and run model inference
                features = extract_39_features(word_buffer)
                predicted_class = predict_audio_class(features)
                
                # Display Result
                if predicted_class == "unknown":
                    print("--> [ Noise / Unknown ] ignored.")
                else:
                    print(f"--> >>> PREDICTED COMMAND: {predicted_class.upper()} <<<")
                
                # Free memory and apply a short delay to prevent multi-triggering
                gc.collect()
                time.sleep(0.5)
                
                # Flush the audio buffer so old sounds don't trigger the next loop immediately
                audio_in.readinto(current_buf)
                
            else:
                # If quiet, swap buffers to maintain the rolling 0.1s history
                history_buf, current_buf = current_buf, history_buf

if __name__ == '__main__':
    main()