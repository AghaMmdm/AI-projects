import gc
gc.collect()
import machine
from machine import I2S, Pin
import time
import struct

# ==========================================
# 1. SETTINGS & GLOBALS (NO ALLOCATIONS YET!)
# ==========================================
SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  
RECORD_SECONDS = 1.2  # Record 1.2 seconds to prevent word clipping
BUFFER_LENGTH = int(SAMPLE_RATE * 2 * RECORD_SECONDS)
GAIN_MULTIPLIER = 8 

# These variables are allocated after the model is loaded to keep RAM free
word_buffer = None
current_buf = None
audio_in = None
NN_MODEL = {}

gc.collect()

# ==========================================
# 2. ULTIMATE ZERO-RAM BINARY LOADER
# ==========================================
def load_nn_model():
    global NN_MODEL
    print("\nLoading Neural Network Binary File... ", end="")
    try:
        # RAM is completely empty at this stage
        with open('model_weights.bin', 'rb') as f:
            header = f.read(6)
            num_feat, num_hidden, num_classes = struct.unpack('<HHH', header)
            
            NN_MODEL['num_feat'] = num_feat
            NN_MODEL['num_hidden'] = num_hidden
            NN_MODEL['num_classes'] = num_classes
            
            def read_small_list(count):
                return [struct.unpack('<f', f.read(4))[0] for _ in range(count)]
            
            NN_MODEL['mean'] = read_small_list(num_feat)
            NN_MODEL['scale'] = read_small_list(num_feat)
            
            # Save heavy matrices as raw bytes (Zero-percent RAM overhead)
            NN_MODEL['W1'] = f.read(num_feat * num_hidden * 4)
            NN_MODEL['B1'] = read_small_list(num_hidden)
            
            NN_MODEL['W2'] = f.read(num_hidden * num_classes * 4)
            NN_MODEL['B2'] = read_small_list(num_classes)
            
            # Only 3 classes ('off' command has been removed)
            NN_MODEL['classes'] = ['on', 'stop', 'unknown']
            
        print(f"Done! (Hidden Neurons: {num_hidden}, Classes: {num_classes})")
        gc.collect()
    except Exception as e:
        print("\n[!] ERROR: Could not load 'model_weights.bin'. Make sure it is on the SD Card!")
        print(e)
        while True: time.sleep(1)

# ==========================================
# 3. DIGITAL GAIN & VAD
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
    return (total_energy / num_chunks) * 0.45 

# ==========================================
# 4. SMART FEATURE EXTRACTION
# ==========================================
def get_trim_indices(raw_buffer, noise_floor):
    window_size = 512 
    buffer_len = len(raw_buffer)
    start_idx, end_idx = 0, buffer_len
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
    if start_idx >= end_idx - 1000: return 0, buffer_len
    return start_idx, end_idx

def compute_smart_features(raw_buffer, start_byte, end_byte, num_coeffs=13):
    num_samples = (end_byte - start_byte) // 2
    if num_samples <= 0: return [0.0] * num_coeffs
    
    max_amp, sum_amp, sum_high, sum_low, zcr, peaks = 1, 0, 0, 0, 0, 0
    last_val, last_low, last_sign, last_diff_sign = 0, 0, 0, 0
    envelope = [0.0] * 8
    spb = max(1, num_samples // 8)
    sample_idx = 0
    
    for i in range(start_byte, end_byte, 2):
        val = raw_buffer[i] | (raw_buffer[i+1] << 8)
        if val >= 32768: val -= 65536
        abs_val = abs(val)
        
        if abs_val > max_amp: max_amp = abs_val
        sum_amp += abs_val
        diff = val - last_val
        sum_high += abs(diff)
        
        low_val = (last_low * 8 + val * 2) // 10
        sum_low += abs(low_val)
        envelope[min(7, sample_idx // spb)] += abs_val
        
        if abs_val > 300: 
            sign = 1 if val > 0 else -1
            if sign != last_sign and last_sign != 0: zcr += 1
            last_sign = sign
            
            dsign = 1 if diff > 0 else -1 if diff < 0 else 0
            if dsign != last_diff_sign and last_diff_sign == 1: peaks += 1
            last_diff_sign = dsign
            
        last_val = val
        last_low = low_val
        sample_idx += 1
        
    f1 = (sum_amp / num_samples) / max_amp              
    f2 = sum_high / (sum_amp + 1) 
    f3 = sum_low / (sum_amp + 1)  
    f4 = zcr / num_samples             
    f5 = peaks / num_samples           
    
    max_env = max(max(envelope), 1)
    return [f1, f2, f3, f4, f5] + [e / max_env for e in envelope]

def extract_39_features(raw_buffer, noise_floor):
    start_idx, end_idx = get_trim_indices(raw_buffer, noise_floor)
    bpp = (((end_idx - start_idx) // 2) // 3) * 2
    
    p1_s, p1_e = start_idx, start_idx + bpp
    p2_s, p2_e = p1_e, p1_e + bpp
    p3_s, p3_e = p2_e, end_idx 
    
    m1 = compute_smart_features(raw_buffer, p1_s, p1_e, 13)
    m2 = compute_smart_features(raw_buffer, p2_s, p2_e, 13)
    m3 = compute_smart_features(raw_buffer, p3_s, p3_e, 13)
    return m1 + m2 + m3

# ==========================================
# 5. NEURAL NETWORK PIPELINE 
# ==========================================
def relu(x):
    return x if x > 0 else 0.0

def predict_audio_class(features):
    num_feat = NN_MODEL['num_feat']
    num_hidden = NN_MODEL['num_hidden']
    num_classes = NN_MODEL['num_classes']
    
    scaled_features = [0.0] * num_feat
    for j in range(num_feat):
        scaled_features[j] = (features[j] - NN_MODEL['mean'][j]) / NN_MODEL['scale'][j]
        
    hidden_layer = [0.0] * num_hidden
    for i in range(num_hidden):
        sum_val = NN_MODEL['B1'][i]
        for j in range(num_feat):
            byte_offset = (j * num_hidden + i) * 4
            w = struct.unpack_from('<f', NN_MODEL['W1'], byte_offset)[0]
            sum_val += scaled_features[j] * w
        hidden_layer[i] = relu(sum_val)
        
    best_score = -999999.0
    best_class = "unknown"
    
    for c in range(num_classes):
        score = NN_MODEL['B2'][c]
        for i in range(num_hidden):
            byte_offset = (i * num_classes + c) * 4
            w = struct.unpack_from('<f', NN_MODEL['W2'], byte_offset)[0]
            score += hidden_layer[i] * w
            
        if score > best_score:
            best_score = score
            best_class = NN_MODEL['classes'][c]
            
    return best_class

# ==========================================
# 6. MAIN EXPLICIT PROMPTED LOOP
# ==========================================
def main():
    global word_buffer, current_buf, audio_in
    
    # Step 1: Load the model without taking up extra RAM!
    load_nn_model()
    
    # Step 2: Allocate heavy audio buffers after the network is fully loaded
    print("Allocating audio buffers...")
    word_buffer = bytearray(BUFFER_LENGTH)
    current_buf = bytearray(CHUNK_SIZE)
    gc.collect()
    
    # Step 3: Initialize I2S microphone hardware
    print("Initializing Microphone...")
    audio_in = I2S(2, sck=Pin('Y6'), ws=Pin('Y5'), sd=Pin('Y8'), 
                   mode=I2S.RX, bits=16, format=I2S.MONO, 
                   rate=SAMPLE_RATE, ibuf=4096)
    
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
        
        # Completely flush the I2S hardware buffer before recording starts
        audio_in.readinto(current_buf)
            
        print(">>> 🔴 START SPEAKING NOW! <<<")
        
        # Record exactly 1.2 seconds of audio in a continuous loop
        bytes_recorded = 0
        view = memoryview(word_buffer)
        current_view = memoryview(current_buf) # Allocated memory window view
        
        while bytes_recorded < BUFFER_LENGTH:
            num_read = audio_in.readinto(current_buf)
            if num_read > 0:
                copy_len = min(num_read, BUFFER_LENGTH - bytes_recorded)
                # Direct memory-to-memory copy without creating any new variables!
                view[bytes_recorded : bytes_recorded + copy_len] = current_view[0:copy_len] 
                bytes_recorded += copy_len                
        print(">>> ⏹️ STOP! <<<")
        print("   (Analyzing...) ", end="")
        
        apply_digital_gain(word_buffer, BUFFER_LENGTH, GAIN_MULTIPLIER)
        features = extract_39_features(word_buffer, threshold)
        predicted_class = predict_audio_class(features)
        
        print("Done!")
        if predicted_class == "unknown":
            print("   --> [ Noise / Unknown ] ignored.")
        else:
            print(f"   --> >>> PREDICTED COMMAND: {predicted_class.upper()} <<<")
        
        gc.collect()
        time.sleep(1)
    print("\n=========================================")
    print("   TESTING COMPLETED. 10/10 DONE!        ")
    print("=========================================")

if __name__ == '__main__':
    main()