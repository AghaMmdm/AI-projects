# 🎨 Ultra-Lightweight Edge AI: RGB & Surface Color Detection (TinyML)

An end-to-end TinyML embedded intelligence pipeline designed to capture optical surface reflections, eliminate ambient noise, and classify surface colors in real-time on resource-constrained microcontrollers (e.g., STM32 running MicroPython) with **< 5KB RAM and < 5ms inference latency**.

---

## 📌 Architecture Overview

Instead of relying on heavy camera sensors or power-hungry image processing units, this system uses an ultra-minimalist optical setup:
- **Active Illumination:** Addressable RGB LEDs (e.g., WS2812B) sequentially pulse `Ambient (OFF)`, `Red`, `Green`, `Blue`, and `White` light onto the target surface.
- **Optical Sensor:** An inexpensive analog light sensor / LDR connected to an ADC channel.
- **Ambient Light Cancellation:** Ambient environmental luminance is sampled and dynamically subtracted from the reflection channels:
  $$\text{Feature}_c = \max(\text{Sensor}_c - \text{Sensor}_{\text{Ambient}}, 0)$$
- **White Surface Normalization:** Optical features are normalized against a calibrated white reference surface to guarantee environmental robustness across varying lighting conditions.
- **Embedded TinyML Model:** A pruned Decision Tree converted into ultra-compact MicroPython arrays / hardcoded conditional rules for instant on-device execution.

```
       ┌────────────────────────┐
       │   Active LED Pulse     │
       │  (R -> G -> B -> W)    │
       └───────────┬────────────┘
                   │ Reflectance
                   ▼
       ┌────────────────────────┐
       │ Analog Optical Sensor  │
       │       (LDR / ADC)      │
       └───────────┬────────────┘
                   │ Raw Voltages
                   ▼
┌──────────────────────────────────────┐
│        MicroPython Firmware          │
│ 1. Ambient Light Subtraction         │
│ 2. White Reference Normalization     │
│ 3. TinyML Decision Tree Inference    │
└──────────────────┬───────────────────┘
                   │
                   ▼
         🎯 Output: Color Class
        (e.g., "Red", "Blue")
```

---

## 📂 Repository Structure

The project is organized into modular pipelines following industry best practices for TinyML projects:

```
RGB Color Detection(Micro)/
├── Data/                             # Datasets and color palette databases
│   ├── color_dataset_4f.csv          # 4-feature normalized experimental dataset (R, G, B, W)
│   ├── color_dataset_rgb.csv         # 3-feature raw RGB dataset
│   ├── colours_rgb_shades.csv        # Comprehensive shade lookup dataset
│   ├── palette.txt                   # Standard hex/decimal color references
│   └── simple_colors.txt             # Primary color definitions
│
├── edge_data_collection/             # Microcontroller data acquisition firmware
│   └── 01_collect_dataset.py         # Calibrates & logs live reflection datasets to flash/CSV
│
├── model_training/                   # Offline training & model quantization
│   └── 02_train_decision_tree.py     # Trains scikit-learn model & generates MCU-ready weights
│
├── edge_inference/                   # Production firmware deployed on hardware
│   ├── main.py                       # Live inference using TinyML inference engine
│   └── dt_inference.py               # Standalone zero-dependency Decision Tree engine
│
├── edge_mcu/                         # Exported model files and binaries
│   ├── color_model.bin               # Quantized binary model
│   ├── model_data.py                 # Compact index-based tree traversal arrays
│   └── model.json                    # Model architecture definition
│
├── experiments/                      # Research notebooks and benchmarking
│   └── 01_color_classification_exploration.ipynb
│
├── .gitignore                        # Git exclusion rules
├── README.md                         # Project documentation
└── requirements.txt                  # Python dependencies for training
```

---

## ✨ Key Features

- **Extreme Resource Efficiency:** Total memory footprint under 3 KB — operates comfortably on any microcontroller with MicroPython.
- **Ambient Interference Resistance:** Actively compensates for fluctuating room lights and shadow effects via synchronized background subtraction.
- **Dual Deployment Modes:**
  1. `TinyMLPredictor` integration for standardized edge architectures.
  2. Native zero-dependency `dt_inference.py` / nested rules requiring no external libraries.
- **High Speed:** Sub-5ms execution time per classification cycle on a 168MHz STM32 MCU.

---

## 🚀 Getting Started

### 1. Hardware Setup
- **MCU:** STM32 board running MicroPython (or ESP32 / Raspberry Pi Pico).
- **Illuminator:** Addressable RGB LED (Pin `X1`, GRB format).
- **Light Sensor:** Phototransistor / LDR voltage divider connected to ADC (Pin `X19`).

---

### 2. Data Collection (On Board)
Upload `edge_data_collection/01_collect_dataset.py` to the microcontroller.
```bash
# Calibrate with white surface, then follow prompts to log classes
python edge_data_collection/01_collect_dataset.py
```
This logs normalized readings directly to `color_dataset_4f.csv`.

---

### 3. Model Training & Export (PC / Host)
Install host dependencies:
```bash
pip install -r requirements.txt
```
Run the training script to train the model and generate deployment weights:
```bash
python model_training/02_train_decision_tree.py
```
This produces:
- `edge_mcu/model_data.py` (Tree traversal tables)
- `edge_mcu/color_model_rules.py` (C-style nested if-else rules)

---

### 4. Edge Deployment
Copy the inference script and model weights to the board:
```bash
# Using ampy, rshell or mpremote
ampy put edge_inference/main.py
ampy put edge_mcu/model_data.py
```

---

## 📊 Performance Benchmarks

| Metric | Measured Value |
| :--- | :--- |
| **Model Type** | Constrained Decision Tree (Max Depth = 6) |
| **Test Accuracy** | > 95% on distinct primary & secondary surface colors |
| **Model Footprint** | ~3.1 KB (.bin) / < 1.5 KB (Python array) |
| **RAM Consumption** | < 4 KB |
| **Inference Latency** | ~2.8 ms (MicroPython on STM32 @ 168MHz) |

---

## 📜 License
This project is open-source and available under the MIT License.
