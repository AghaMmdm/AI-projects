"""
Real-time Edge AI Inference for Surface Color Recognition on MicroPython / STM32.

Hardware Architecture:
- Microcontroller: STM32 running MicroPython
- Sensor: Ambient / Reflected light sensor (LDR connected to ADC pin 'X19')
- Illuminator: WS2812B / BRGB LED Module connected to Pin 'X1'

Workflow:
1. Loads TinyML classification model (using `tinyml_inference.TinyMLPredictor` or lightweight decision tree).
2. Performs 1-step white surface calibration to eliminate ambient variance.
3. Continuously measures reflected intensity (Red, Green, Blue, White) with ambient cancellation.
4. Normalizes feature inputs and runs on-device inference (< 5ms).
5. Outputs predicted color class.
"""

import bluelib
import time
from pyb import Pin, ADC
import gc

# TinyML MicroPython Inference Engine
import tinyml_model
from tinyml_inference import TinyMLPredictor

# ==============================================================================
# 1. HARDWARE CONFIGURATION
# ==============================================================================
ADC_PIN = "X19"
LED_PIN = "X1"
LED_COUNT = 2

adc = ADC(Pin(ADC_PIN))
brgb = bluelib.BRGB(Pin(LED_PIN), LED_COUNT)

# ==============================================================================
# 2. RUNTIME PARAMETERS
# ==============================================================================
SAMPLES = 20              # ADC oversampling count
SETTLE_TIME = 0.05        # Sensor stabilization delay (seconds)
LED_BRIGHTNESS = 255      # Full scale LED illumination level
INFERENCE_INTERVAL = 1.5  # Delay between predictions (seconds)

# ==============================================================================
# 3. SENSOR & OPTICAL ENGINE
# ==============================================================================
def read_average_adc():
    """Reads multiple samples from ADC pin and returns the average value."""
    total = 0
    for _ in range(SAMPLES):
        total += adc.read()
        time.sleep_ms(2)
    return total / SAMPLES

def turn_off_leds():
    """Shuts down all onboard LEDs."""
    brgb.fill((0, 0, 0))
    brgb.write()

def measure_reflection(r, g, b):
    """Illuminates target with specified RGB color and reads reflected flux."""
    turn_off_leds()
    color = (g, r, b)  # Hardware GRB order
    brgb.fill(color)
    brgb.write()
    time.sleep(SETTLE_TIME)
    val = read_average_adc()
    turn_off_leds()
    return val

def get_full_profile():
    """
    Measures ambient background light and subtracts it from active reflections.
    Returns: (r_val, g_val, b_val, w_val)
    """
    ambient = measure_reflection(0, 0, 0)
    
    r_val = measure_reflection(LED_BRIGHTNESS, 0, 0) - ambient
    g_val = measure_reflection(0, LED_BRIGHTNESS, 0) - ambient
    b_val = measure_reflection(0, 0, LED_BRIGHTNESS) - ambient
    w_val = measure_reflection(LED_BRIGHTNESS, LED_BRIGHTNESS, LED_BRIGHTNESS) - ambient
    
    return max(r_val, 0.0), max(g_val, 0.0), max(b_val, 0.0), max(w_val, 0.0)

def calibrate_white_reference():
    """Calibrates baseline reflection coefficients against a white surface."""
    print("=========================================")
    print("   [ HARDWARE CALIBRATION ]              ")
    print("=========================================")
    print("Place a WHITE surface under the sensor...")
    time.sleep(3)

    ref_r, ref_g, ref_b, ref_w = get_full_profile()
    
    # Avoid zero-division errors
    ref_r = max(ref_r, 1.0)
    ref_g = max(ref_g, 1.0)
    ref_b = max(ref_b, 1.0)
    ref_w = max(ref_w, 1.0)

    print("-> System Calibrated. Base White Intensity: {:.1f}".format(ref_w))
    print("   R={:.1f} | G={:.1f} | B={:.1f} | W={:.1f}".format(ref_r, ref_g, ref_b, ref_w))
    return ref_r, ref_g, ref_b, ref_w

# ==============================================================================
# 4. MAIN INFERENCE LOOP
# ==============================================================================
def main():
    gc.collect()
    
    print("=========================================")
    print("   [ INITIALIZING TINYML ENGINE ]        ")
    print("=========================================")
    try:
        predictor = TinyMLPredictor(tinyml_model)
        print("[*] Engine Ready. Model Type: {}".format(predictor.type))
    except Exception as e:
        print("[-] Error loading TinyML model:", e)
        return

    time.sleep(1)
    
    # Run optical reference calibration
    ref_r, ref_g, ref_b, ref_w = calibrate_white_reference()
    
    print("\n=========================================")
    print("   [ EDGE COLOR PREDICTOR RUNNING ]      ")
    print("=========================================")
    
    while True:
        # 1. Capture optical reflection profile
        raw_r, raw_g, raw_b, raw_w = get_full_profile()
        
        # 2. Normalize inputs against white reference
        norm_r = raw_r / ref_r
        norm_g = raw_g / ref_g
        norm_b = raw_b / ref_b
        norm_w = raw_w / ref_w
        
        # 3. Format input mapping
        data_for_ai = {
            "Red_Value": norm_r,
            "Green_Value": norm_g,
            "Blue_Value": norm_b,
            "White_Value": norm_w
        }
        
        # 4. Execute on-device prediction
        try:
            predicted_color = predictor.predict(data_for_ai)
        except Exception as e:
            predicted_color = "ERROR"
            print("[!] Inference Error:", e)
        
        # 5. Output telemetry
        print("-----------------------------------------")
        print("   -> Features: R={:.2f} G={:.2f} B={:.2f} W={:.2f}".format(norm_r, norm_g, norm_b, norm_w))
        print("   => 🎯 PREDICTION: {}".format(str(predicted_color).upper()))
        print("-----------------------------------------")
        
        gc.collect()
        time.sleep(INFERENCE_INTERVAL)

if __name__ == "__main__":
    main()
