# Ultra-Lightweight Edge AI: Voice Command Recognition (TinyML)

An end-to-end Machine Learning pipeline for real-time Keyword Spotting (KWS), heavily optimized for microcontrollers with extreme resource constraints (e.g., < 100KB RAM). 

This project tackles the classic TinyML bottleneck: fitting a robust audio classification model into a microcontroller without sacrificing accuracy. By replacing deep learning bloat with aggressive mathematical dimensionality reduction, the final inference model requires **less than 3KB of storage** and runs natively on MicroPython.

## ✨ Key Features
* **Extreme Compression:** Reduced the model footprint from >500KB (Standard Tree Ensembles) to <3KB using custom statistical pipelines.
* **Smart Feature Engineering:** Replaced standard full-second MFCC averaging with **Dynamic Temporal Pooling** (extracting 39 features across the start, middle, and end of words) to preserve time-domain context.
* **Mathematical Dimensionality Reduction:** Utilized Linear Discriminant Analysis (LDA) with an 'eigen' solver to compress 39 audio features into 3 highly discriminative super-features.
* **Robust Target Focus:** Implemented Optuna for hyperparameter tuning with class-weight prioritization, ensuring high recall for critical commands (`on`, `off`, `stop`) while ignoring background noise (`unknown`).
* **Zero-Dependency Inference:** The edge inference engine relies purely on standard Python loops and basic math. No heavy frameworks (like TensorFlow Lite or Scikit-Learn) are required on the board.

## 🧠 System Architecture

1. **VAD (Voice Activity Detection):** Silence trimming via energy thresholds.
2. **MFCC Extraction:** Root reduction (extracting only the 13 most critical vocal frequencies).
3. **Temporal Pooling:** Splitting the active voice wave into 3 equal sequences (3 × 13 = 39 Features).
4. **LDA Transformation:** Mapping the 39 features into a 3-dimensional latent space.
5. **Logistic Regression:** Making the final classification using a highly optimized weight matrix.

## 📂 Repository Structure

```text
├── Data/                       # Audio datasets (.wav) and extracted arrays (.npy)
├── notebooks/                  
│   ├── 01_model_experiments.ipynb  # Benchmarking Random Forest, XGBoost, Gaussian Naive Bayes
│   └── 02_final_pipeline.ipynb     # The final highly-optimized LDA + LR pipeline
├── edge_mcu/                   
│   ├── model_data_lr.py            # Auto-generated weights and scalings matrix
│   └── main.py                     # MicroPython inference engine and I2S Mic handling
├── README.md                   
└── requirements.txt
```

## 🚀 Performance Benchmarks
1. **Cross-Validation Accuracy:** ~78.6%

2. **Model Export Size:** ~2.5 KB

3. **Inference Time (MicroPython):** < 3ms