"""
RGB & 4-Feature Surface Color Data Collection on MicroPython / STM32.

Hardware Setup:
- ADC Pin: Analog Ambient/Reflected Light Sensor (e.g. LDR on 'X19')
- BRGB Module: Addressable RGB LEDs (e.g. WS2812B on Pin 'X1')

Workflow:
1. Performs white surface reference calibration to normalize subsequent readings.
2. Interactively prompts user for each target color.
3. Records reflected light under Ambient, Red, Green, Blue, and White illumination.
4. Normalizes feature values against white reference.
5. Logs data directly into a CSV dataset on the microcontroller's flash/storage.
"""

import bluelib
import time
from pyb import Pin, ADC
import gc

# ==============================================================================
# 1. HARDWARE CONFIGURATION
# ==============================================================================
ADC_PIN = "X19"
LED_PIN = "X1"
LED_COUNT = 2

adc = ADC(Pin(ADC_PIN))
brgb = bluelib.BRGB(Pin(LED_PIN), LED_COUNT)

# ==============================================================================
# 2. SAMPLING SETTINGS & TARGET CLASSES
# ==============================================================================
SAMPLES = 20              # Number of ADC readings averaged per measurement
SETTLE_TIME = 0.05        # Settle time in seconds after LED state change
LED_BRIGHTNESS = 255      # PWM brightness (0-255)
SAMPLES_PER_COLOR = 10    # Samples logged per class in one session
CSV_FILENAME = "color_dataset_4f.csv"

# Target classes to collect
COLORS = ["blue", "red", "yellow", "black", "white", "green"]

# ==============================================================================
# 3. SENSOR & ILLUMINATION HELPERS
# ==============================================================================
def read_average_adc():
    """Reads multiple samples from ADC pin and returns the arithmetic mean."""
    total = 0
    for _ in range(SAMPLES):
        total += adc.read()
        time.sleep_ms(2)
    return total / SAMPLES

def turn_off_leds():
    """Turns off all illumination LEDs."""
    brgb.fill((0, 0, 0))
    brgb.write()

def measure_reflection(r, g, b):
    """
    Sets the LED color, waits for optical settle time, reads sensor reflection,
    and turns off LEDs.
    Note: Many addressable LED strips follow GRB byte ordering.
    """
    turn_off_leds()
    color = (g, r, b)  # GRB order
    brgb.fill(color)
    brgb.write()
    time.sleep(SETTLE_TIME)
    val = read_average_adc()
    turn_off_leds()
    return val

def get_surface_profile():
    """
    Captures ambient background noise, subtracts it from Red, Green, Blue,
    and White reflection channels, and returns clean 4-feature values.
    """
    # 1. Measure background ambient noise without LED illumination
    ambient = measure_reflection(0, 0, 0)
    
    # 2. Sequentially measure light reflections per channel
    r_val = measure_reflection(LED_BRIGHTNESS, 0, 0) - ambient
    g_val = measure_reflection(0, LED_BRIGHTNESS, 0) - ambient
    b_val = measure_reflection(0, 0, LED_BRIGHTNESS) - ambient
    w_val = measure_reflection(LED_BRIGHTNESS, LED_BRIGHTNESS, LED_BRIGHTNESS) - ambient
    
    # Clip negative values caused by sensor variance
    return max(r_val, 0.0), max(g_val, 0.0), max(b_val, 0.0), max(w_val, 0.0)

# ==============================================================================
# 4. CALIBRATION
# ==============================================================================
def calibrate_white_reference():
    """
    Calibrates baseline reflection intensity using a reference white surface.
    Used to normalize all subsequent readings against environmental variances.
    """
    print("=========================================")
    print("   [ CALIBRATION MODE ]                  ")
    print("=========================================")
    print("Please place a WHITE reference surface under the sensor...")
    time.sleep(3)

    ref_r, ref_g, ref_b, ref_w = get_surface_profile()
    
    # Guard against division by zero during normalization
    ref_r = max(ref_r, 1.0)
    ref_g = max(ref_g, 1.0)
    ref_b = max(ref_b, 1.0)
    ref_w = max(ref_w, 1.0)

    print("-> Calibration complete:")
    print("   Ref R: {:.1f} | Ref G: {:.1f} | Ref B: {:.1f} | Ref White: {:.1f}".format(
        ref_r, ref_g, ref_b, ref_w
    ))
    print("=========================================\n")
    return ref_r, ref_g, ref_b, ref_w

# ==============================================================================
# 5. DATASET COLLECTION ROUTINE
# ==============================================================================
def run_data_collection():
    """Runs interactive dataset collection loop and writes results to CSV."""
    gc.collect()
    
    ref_r, ref_g, ref_b, ref_w = calibrate_white_reference()
    
    print("[*] Initializing dataset file: {}".format(CSV_FILENAME))
    with open(CSV_FILENAME, "w") as f:
        f.write("Red_Value,Green_Value,Blue_Value,White_Value,label\n")
    
    for color in COLORS:
        print("-----------------------------------------")
        print(">>> Ready to sample class: [{}] <<<".format(color.upper()))
        input("Press ENTER when target surface is placed under the sensor...")
        time.sleep(1)
        
        with open(CSV_FILENAME, "a") as f:
            for sample_idx in range(1, SAMPLES_PER_COLOR + 1):
                raw_r, raw_g, raw_b, raw_w = get_surface_profile()
                
                # Normalize features against white reference
                norm_r = raw_r / ref_r
                norm_g = raw_g / ref_g
                norm_b = raw_b / ref_b
                norm_w = raw_w / ref_w
                
                # Append sample to CSV
                f.write("{:.5f},{:.5f},{:.5f},{:.5f},{}\n".format(
                    norm_r, norm_g, norm_b, norm_w, color
                ))
                f.flush()
                
                print("   Sample {:02d}/{:02d}: R={:.2f} G={:.2f} B={:.2f} W={:.2f}".format(
                    sample_idx, SAMPLES_PER_COLOR, norm_r, norm_g, norm_b, norm_w
                ))
                time.sleep(0.1)
                
        print(">>> Finished logging class [{}] <<<\n".format(color.upper()))
        
    print("Dataset collection finished successfully! Saved to '{}'".format(CSV_FILENAME))

if __name__ == "__main__":
    run_data_collection()
