import bluelib
import time
from pyb import Pin, ADC
import gc

import tinyml_model
from tinyml_inference import TinyMLPredictor

# ==========================================
# 1. HARDWARE CONFIGURATION
# ==========================================
adc = ADC(Pin("X19"))          
brgb = bluelib.BRGB(Pin("X1"), 2) 

# ==========================================
# 2. SETTINGS
# ==========================================
SAMPLES = 20
SETTLE_TIME = 0.05
LED_BRIGHTNESS = 255

# ==========================================
# 3. SENSOR OPERATIONS
# ==========================================
def read_avg():
    total = 0
    for _ in range(SAMPLES):
        total += adc.read()
        time.sleep_ms(2)
    return total / SAMPLES

def turn_off_all():
    brgb.fill((0, 0, 0))
    brgb.write()

def measure_light(r, g, b):
    turn_off_all()
    color = (g, r, b) # GRB format
    brgb.fill(color)
    brgb.write()
    time.sleep(SETTLE_TIME)
    value = read_avg()
    turn_off_all()
    return value

def get_full_profile():
    ambient = measure_light(0, 0, 0)
    
    r_val = measure_light(LED_BRIGHTNESS, 0, 0) - ambient
    g_val = measure_light(0, LED_BRIGHTNESS, 0) - ambient
    b_val = measure_light(0, 0, LED_BRIGHTNESS) - ambient
    w_val = measure_light(LED_BRIGHTNESS, LED_BRIGHTNESS, LED_BRIGHTNESS) - ambient
    
    return max(r_val, 0), max(g_val, 0), max(b_val, 0), max(w_val, 0)

def calibrate_reference():
    print("=========================================")
    print("   [ SYSTEM CALIBRATION ]                ")
    print("=========================================")
    print("Place a WHITE surface under the sensor...")
    time.sleep(3)

    ref_r, ref_g, ref_b, ref_w = get_full_profile()
    
    ref_r = max(ref_r, 1.0)
    ref_g = max(ref_g, 1.0)
    ref_b = max(ref_b, 1.0)
    ref_w = max(ref_w, 1.0)

    print("-> Ready. Base White Intesnity: {:.1f}".format(ref_w))
    return ref_r, ref_g, ref_b, ref_w

# ==========================================
# 4. MAIN INFERENCE LOOP
# ==========================================
def main():
    gc.collect()
    
    print("=========================================")
    print("   [ INITIALIZING AI ENGINE ]            ")
    print("=========================================")
    try:
        predictor = TinyMLPredictor(tinyml_model)
        print("[*] Engine Ready. Type: {}".format(predictor.type))
    except Exception as e:
        print("[-] Error loading model:", e)
        return

    time.sleep(1)
    
    # Run hardware calibration
    ref_r, ref_g, ref_b, ref_w = calibrate_reference()
    
    print("\n=========================================")
    print("   [ EDGE COLOR PREDICTOR RUNNING ]      ")
    print("=========================================")
    
    while True:
        # 1. Capture the 4-feature profile
        raw_r, raw_g, raw_b, raw_w = get_full_profile()
        
        # 2. Normalize inputs
        norm_r = raw_r / ref_r
        norm_g = raw_g / ref_g
        norm_b = raw_b / ref_b
        norm_w = raw_w / ref_w
        
        # 3. Create input dictionary mapping to CSV headers
        data_for_ai = {
            "Red_Value": norm_r,
            "Green_Value": norm_g,
            "Blue_Value": norm_b,
            "White_Value": norm_w
        }
        
        # 4. Predict
        try:
            predicted_color = predictor.predict(data_for_ai)
        except Exception as e:
            predicted_color = "ERROR"
            print("[!] Inference Error:", e)
        
        # 5. Output results
        print("-----------------------------------------")
        print("   -> Features: R={:.2f} G={:.2f} B={:.2f} W={:.2f}".format(norm_r, norm_g, norm_b, norm_w))
        print("   => 🎯 PREDICTION: {}".format(str(predicted_color).upper()))
        print("-----------------------------------------")
        
        gc.collect()
        time.sleep(1.5)

if __name__ == '__main__':
    main()