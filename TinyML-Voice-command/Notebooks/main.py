import gc
gc.collect()
import machine
from machine import I2S, Pin
import time
import struct

# ==========================================
# 1. SETTINGS & PRE-ALLOCATION
# ==========================================
SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  
RECORD_SECONDS = 1.0  
BUFFER_LENGTH = int(SAMPLE_RATE * 2 * RECORD_SECONDS)
GAIN_MULTIPLIER = 8 

word_buffer = bytearray(BUFFER_LENGTH)
history_buf = bytearray(CHUNK_SIZE)
current_buf = bytearray(CHUNK_SIZE)

# متغیر سراسری برای نگه‌داری وزن‌های شبکه عصبی
NN_MODEL = {}

gc.collect()

# ==========================================
# 2. HARDWARE CONFIGURATION
# ==========================================
audio_in = I2S(2, sck=Pin('Y6'), ws=Pin('Y5'), sd=Pin('Y8'), 
               mode=I2S.RX, bits=16, format=I2S.MONO, 
               rate=SAMPLE_RATE, ibuf=4096)

# ==========================================
# 3. BINARY NEURAL NETWORK LOADER
# ==========================================
def load_nn_model():
    print("\nLoading Neural Network Binary File... ", end="")
    try:
        with open('model_weights.bin', 'rb') as f:
            # خواندن ابعاد شبکه
            header = f.read(6)
            num_feat, num_hidden, num_classes = struct.unpack('<HHH', header)
            
            def read_floats(count):
                return [struct.unpack('<f', f.read(4))[0] for _ in range(count)]
            
            NN_MODEL['mean'] = read_floats(num_feat)
            NN_MODEL['scale'] = read_floats(num_feat)
            
            W1 = []
            for _ in range(num_feat): W1.append(read_floats(num_hidden))
            NN_MODEL['W1'] = W1
            NN_MODEL['B1'] = read_floats(num_hidden)
            
            W2 = []
            for _ in range(num_hidden): W2.append(read_floats(num_classes))
            NN_MODEL['W2'] = W2
            NN_MODEL['B2'] = read_floats(num_classes)
            NN_MODEL['classes'] = ['on', 'off', 'stop', 'unknown']
            
        print(f"Done! (Hidden Neurons: {num_hidden})")
        gc.collect()
    except Exception as e:
        print("\n[!] ERROR: Could not load 'model_weights.bin'. Make sure it is on the SD Card!")
        print(e)
        while True: time.sleep(1)

# ==========================================
# 4. DIGITAL GAIN & VAD
# ==========================================
def apply_digital_gain(buffer, num_bytes, gain_multiplier):
    for i in range(0, num_bytes, 2):
        val = buffer[i] | (buffer[i+1] << 8)
        if val >= 32768: val -= 65536
        
        val = val * gain_multiplier
        
        if val > 32767: val = 32767
        elif val < -32768: val = -32768
        
        if val < 0: val += 65536
        buffer[i] = val & 0xFF
        buffer[i+1] = (val >> 8) & 0xFF

def calculate_energy(buffer, start=0, end=None):
    if end is None: end = len(buffer)
    sum_squares = 0.0
    for i in range(start, end, 2):
        val = buffer[i] | (buffer[i+1] << 8)
        if val >= 32768: val -= 65536
        sum_squares += val * val
    num_samples = (end - start) // 2
    if num_samples == 0: return 0
    return (sum_squares / num_samples) ** 0.5

def calibrate_noise_level(duration_sec=2.0):
    print("Calibrating ambient noise... Keep quiet for 2 seconds!")
    total_energy = 0
    num_chunks = int((SAMPLE_RATE * 2) / CHUNK_SIZE) * int(duration_sec)
    for _ in range(num_chunks):
        num_read = audio_in.readinto(current_buf)
        if num_read > 0:
            apply_digital_gain(current_buf, num_read, GAIN_MULTIPLIER)
            total_energy += calculate_energy(current_buf)
            
    noise_threshold = (total_energy / num_chunks) * 0.45 
    return noise_threshold

# ==========================================
# 5. SMART FEATURE EXTRACTION
# ==========================================
def get_trim_indices(raw_buffer, noise_floor):
    window_size = 512 
    buffer_len = len(raw_buffer)
    start_idx = 0
    end_idx = buffer_len
    
    for i in range(0, buffer_len, window_size):
        chunk_end = min(i + window_size, buffer_len)
        if calculate_energy(raw_buffer, i, chunk_end) > noise_floor * 1.5:
            start_idx = max(0, i - (window_size * 2))
            break
            
    for i in range(buffer_len - window_size, -1, -window_size):
        chunk_end = min(i + window_size, buffer_len)
        if calculate_energy(raw_buffer, i, chunk_end) > noise_floor * 1.5:
            end_idx = min(buffer_len, chunk_end + (window_size * 2))
            break
            
    if start_idx >= end_idx - 1000:
        return 0, buffer_len
    return start_idx, end_idx

def compute_smart_features(raw_buffer, start_byte, end_byte, num_coeffs=13):
    num_samples = (end_byte - start_byte) // 2
    if num_samples <= 0: return [0.0] * num_coeffs
    
    max_amp = 1
    sum_amp = 0
    sum_high_freq = 0
    sum_low_freq = 0
    zcr = 0
    peaks = 0
    last_val = 0
    last_low = 0
    last_sign = 0
    last_diff_sign = 0
    
    envelope = [0.0] * 8
    samples_per_bin = max(1, num_samples // 8)
    sample_idx = 0
    
    for i in range(start_byte, end_byte, 2):
        val = raw_buffer[i] | (raw_buffer[i+1] << 8)
        if val >= 32768: val -= 65536
        abs_val = abs(val)
        
        if abs_val > max_amp: max_amp = abs_val
        sum_amp += abs_val
        
        diff = val - last_val
        sum_high_freq += abs(diff)
        
        low_val = (last_low * 8 + val * 2) // 10
        sum_low_freq += abs(low_val)
        
        bin_idx = min(7, sample_idx // samples_per_bin)
        envelope[bin_idx] += abs_val
        
        if abs_val > 300: 
            sign = 1 if val > 0 else -1
            if sign != last_sign and last_sign != 0: zcr += 1
            last_sign = sign
            
            diff_sign = 1 if diff > 0 else -1 if diff < 0 else 0
            if diff_sign != last_diff_sign and last_diff_sign == 1: peaks += 1
            last_diff_sign = diff_sign
            
        last_val = val
        last_low = low_val
        sample_idx += 1
        
    f1 = (sum_amp / num_samples) / max_amp              
    f2 = sum_high_freq / (sum_amp + 1) 
    f3 = sum_low_freq / (sum_amp + 1)  
    f4 = zcr / num_samples             
    f5 = peaks / num_samples           
    
    max_env = max(envelope)
    if max_env == 0: max_env = 1
    env_norm = [e / max_env for e in envelope] 
    
    return [f1, f2, f3, f4, f5] + env_norm

def extract_39_features(raw_buffer, noise_floor):
    start_idx, end_idx = get_trim_indices(raw_buffer, noise_floor)
    trimmed_len = end_idx - start_idx
    
    bytes_per_part = ((trimmed_len // 2) // 3) * 2
    
    p1_s = start_idx
    p1_e = p1_s + bytes_per_part
    p2_s = p1_e
    p2_e = p2_s + bytes_per_part
    p3_s = p2_e
    p3_e = end_idx 
    
    m1 = compute_smart_features(raw_buffer, p1_s, p1_e, 13)
    m2 = compute_smart_features(raw_buffer, p2_s, p2_e, 13)
    m3 = compute_smart_features(raw_buffer, p3_s, p3_e, 13)
    
    return m1 + m2 + m3

# ==========================================
# 6. NEURAL NETWORK PIPELINE (SCALER + MLP)
# ==========================================
def relu(x):
    return x if x > 0 else 0.0

def predict_audio_class(features):
    num_features = 39
    num_hidden = len(NN_MODEL['B1'])
    num_classes = len(NN_MODEL['classes'])
    
    # STAGE 1: Apply StandardScaler
    scaled_features = [0.0] * num_features
    for j in range(num_features):
        scaled_features[j] = (features[j] - NN_MODEL['mean'][j]) / NN_MODEL['scale'][j]
        
    # STAGE 2: Hidden Layer (Matrix Multiplication + ReLU)
    hidden_layer = [0.0] * num_hidden
    for i in range(num_hidden):
        sum_val = NN_MODEL['B1'][i]
        for j in range(num_features):
            sum_val += scaled_features[j] * NN_MODEL['W1'][j][i]
        hidden_layer[i] = relu(sum_val)
        
    # STAGE 3: Output Layer (Matrix Multiplication)
    best_score = -999999.0
    best_class = "unknown"
    
    for c in range(num_classes):
        score = NN_MODEL['B2'][c]
        for i in range(num_hidden):
            score += hidden_layer[i] * NN_MODEL['W2'][i][c]
            
        if score > best_score:
            best_score = score
            best_class = NN_MODEL['classes'][c]
            
    return best_class

# ==========================================
# 7. MAIN 10-ITERATION LOOP
# ==========================================
def main():
    global history_buf, current_buf
    
    # ابتدا مدل سنگین لود می‌شود
    load_nn_model()
    
    time.sleep(1)
    threshold = calibrate_noise_level(duration_sec=2.0)
    
    print(f"\n[ SYSTEM READY ] Threshold set to {threshold:.2f}")
    valid_commands = [c.upper() for c in NN_MODEL['classes'] if c != 'unknown']
    print(f"Target commands: {valid_commands}")
    
    TOTAL_ATTEMPTS = 10
    
    for attempt in range(1, TOTAL_ATTEMPTS + 1):
        print("\n" + "="*40)
        print(f"   --- TEST ATTEMPT {attempt}/{TOTAL_ATTEMPTS} ---")
        print("   Get ready...")
        time.sleep(1.5)  
        
        audio_in.readinto(current_buf)
        for i in range(CHUNK_SIZE): history_buf[i] = 0
            
        print(">>> SPEAK NOW! <<<")
        
        spoken = False
        while not spoken:
            num_read = audio_in.readinto(current_buf)
            if num_read > 0:
                apply_digital_gain(current_buf, num_read, GAIN_MULTIPLIER)
                
                if calculate_energy(current_buf) > threshold:
                    print("   (Voice detected, Neural Net analyzing...) ", end="")
                    
                    word_buffer[0:CHUNK_SIZE] = history_buf
                    word_buffer[CHUNK_SIZE:2*CHUNK_SIZE] = current_buf
                    
                    remainder_view = memoryview(word_buffer)[2*CHUNK_SIZE:]
                    num_rem = audio_in.readinto(remainder_view)
                    
                    if num_rem > 0:
                        apply_digital_gain(remainder_view, num_rem, GAIN_MULTIPLIER)
                    
                    features = extract_39_features(word_buffer, threshold)
                    predicted_class = predict_audio_class(features)
                    
                    print("Done!")
                    if predicted_class == "unknown":
                        print("   --> [ Noise / Unknown ] ignored.")
                    else:
                        print(f"   --> >>> PREDICTED COMMAND: {predicted_class.upper()} <<<")
                    
                    spoken = True 
                    gc.collect()
                    time.sleep(1) 
                    
                else:
                    history_buf, current_buf = current_buf, history_buf

    print("\n=========================================")
    print("   TESTING COMPLETED. 10/10 DONE!        ")
    print("=========================================")

if __name__ == '__main__':
    main()