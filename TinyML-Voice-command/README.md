# Ultra-Lightweight Edge AI: Voice Command Recognition (TinyML)

An end-to-end Machine Learning pipeline for real-time Keyword Spotting (KWS), optimized for microcontrollers with extreme resource constraints (e.g., < 100KB RAM).

## 📂 Repository Structure

The project is organized into a clear pipeline:
* `/edge_data_collection`: Tools for recording and building your dataset on the hardware.
* `/model_training`: Scripts for data augmentation, training, and model optimization.
* `/edge_inference`: Production code to run directly on the microcontroller.
* `/experiments`: Jupyter notebooks used for model research and benchmarking.

## ✨ Key Features
* **Extreme Compression:** Optimized model footprint (< 3KB) running natively on MicroPython.
* **Smart Feature Engineering:** Dynamic Temporal Pooling (extracting 39 features across the start, middle, and end of words).
* **Dimensionality Reduction:** Used LDA (Eigen solver) to compress 39 features into 3 highly discriminative super-features.
* **Robust Performance:** Optuna-tuned hyperparameters with class-weight prioritization for critical commands.

## 🚀 Getting Started

### 1. Data Collection
Run the script to collect audio samples on your board:
```bash
python edge_data_collection/01_record_dataset.py
```

### 2. Training
Follow the pipeline to augment, train, and export your model:
1. **Augmentation:** `python model_training/02_augment_data.py`
2. **Training:** `python model_training/03_train_lda_lr.py`
3. **Exploration:** View `experiments/models_comparison.ipynb` for benchmarking different architectures.

### 3. Deployment
Copy the generated parameters from `edge_mcu/model_data_lr.py` (or the `.bin` file) to your board. Ensure your `main.py` is loaded:
```bash
# Upload to your board using ampy or rshell
ampy put edge_inference/main.py
```

## 🚀 Performance Benchmarks
* **Cross-Validation Accuracy:** ~78.6%
* **Model Export Size:** ~2.5 KB
* **Inference Time (MicroPython):** < 3ms

## 🛠 Prerequisites
Install the required environment:
```bash
pip install -r requirements.txt
```