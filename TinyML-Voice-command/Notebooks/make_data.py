import gc
gc.collect()
import machine
from machine import I2S, Pin
import time

# ==========================================
# 1. SETTINGS & PRE-ALLOCATION
# ==========================================
CLASSES = ["up", "down", "unknown"]
SAMPLES_PER_CLASS = 40  # 40 repetitions per class for high accuracy

SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  # 0.1 seconds of audio chunk
RECORD_SECONDS = 1.0  
BUFFER_LENGTH = int(SAMPLE_RATE * 2 * RECORD_SECONDS)

word_buffer = bytearray(BUFFER_LENGTH)

# Dual buffers for the Pre-roll History Buffer technique
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
        if audio_in.readinto(current_buf) > 0:
            total_energy += calculate_energy(current_buf)
    # A multiplier of 2.0 works perfectly for normal ambient environments
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
# 5. DATASET BUILDER LOOP (WITH PRE-ROLL)
# ==========================================
def main():
    # Global buffers are required for zero-RAM pointer swapping
    global history_buf, current_buf
    
    time.sleep(1) 
    threshold = calibrate_noise_level(duration_sec=2.0)
    
    filename = 'dataset.csv'
    print(f"\n[ SYSTEM READY ] Threshold set to {threshold:.2f}")
    
    for label in CLASSES:
        print("\n=========================================")
        print(f"   PREPARE TO RECORD CLASS: >> {label.upper()} <<")
        if label == "unknown":
            print("   (Make noises, type on keyboard, say random words)")
        print("=========================================")
        time.sleep(3) 
        
        sample_count = 0
        while sample_count < SAMPLES_PER_CLASS:
            if audio_in.readinto(current_buf) > 0:
                
                # Check if audio energy triggers the VAD threshold
                if calculate_energy(current_buf) > threshold:
                    print(f"Recording '{label}' ({sample_count + 1}/{SAMPLES_PER_CLASS})...", end="")
                    
                    # Step 1: Prepend the 0.1s history buffer (catches the start of the word)
                    word_buffer[0:CHUNK_SIZE] = history_buf
                    
                    # Step 2: Append the current chunk that triggered the VAD
                    word_buffer[CHUNK_SIZE:2*CHUNK_SIZE] = current_buf
                    
                    # Step 3: Stream the remaining audio into the buffer to hit 1.0 full second
                    bytes_to_read = BUFFER_LENGTH - (2 * CHUNK_SIZE)
                    audio_in.readinto(memoryview(word_buffer)[2*CHUNK_SIZE:])
                    
                    # Extract 39 structural features and save directly to SD card
                    features = extract_39_features(word_buffer)
                    with open(filename, 'a') as f:
                        str_features = ",".join([f"{x:.4f}" for x in features])
                        f.write(f"{label},{str_features}\n")
                        
                    print(" Saved!")
                    sample_count += 1
                    gc.collect()
                    
                    # 1.5-second breathing room delay to prevent recording inhaling sounds
                    time.sleep(1.5)
                    
                else:
                    # If quiet, swap pointers to keep this chunk as the history frame for the next loop
                    # Fast reference switching - consumes zero extra RAM allocation
                    temp = history_buf
                    history_buf = current_buf
                    current_buf = temp
                    
    print("\n=========================================")
    print("   DATA COLLECTION COMPLETE! AWESOME!   ")
    print("   Take out the SD Card and train.      ")
    print("=========================================")

if __name__ == '__main__':
    main()