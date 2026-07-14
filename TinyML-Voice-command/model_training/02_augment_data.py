import sys
import numpy as np
import pandas as pd

# ==========================================
# 1. CONFIGURATION
# ==========================================
INPUT_FILE = './Data/dataset.csv'          # The original hardware dataset
OUTPUT_FILE = './Data/dataset_augmented.csv' # The new multiplied dataset
VALID_CLASSES = ['up', 'down', 'unknown']

# How many synthetic copies to create for EACH original sample
# Example: 4 means 1 original + 4 synthetic = 5x dataset size
SYNTHETIC_COPIES = 4 

# ==========================================
# 2. LOAD & CLEAN ORIGINAL DATA
# ==========================================
print(f"--- Loading Original Dataset: {INPUT_FILE} ---")
cleaned_data = []

try:
    with open(INPUT_FILE, 'r', encoding='latin-1') as f:
        for line in f:
            parts = line.strip().split(',')
            # Strict filtering to ignore any broken lines from hardware power-cuts
            if len(parts) == 40 and parts[0] in VALID_CLASSES:
                try:
                    features = [float(x) for x in parts[1:]]
                    cleaned_data.append([parts[0]] + features)
                except ValueError:
                    pass
except FileNotFoundError:
    print(f"[!] ERROR: {INPUT_FILE} not found in this directory.")
    sys.exit(1)

if len(cleaned_data) == 0:
    print("[!] ERROR: No valid data found. Check your class names or file content.")
    sys.exit(1)

df_original = pd.DataFrame(cleaned_data)
y_orig = df_original.iloc[:, 0].to_numpy()
X_orig = df_original.iloc[:, 1:].to_numpy()

print(f"Original Samples Loaded: {X_orig.shape[0]}")

# ==========================================
# 3. FEATURE-SPACE AUGMENTATION ENGINE
# ==========================================
print(f"--- Starting Data Augmentation (Multiplier: {SYNTHETIC_COPIES + 1}x) ---")
augmented_X = []
augmented_y = []

# Loop through every single recorded sample
for i in range(len(X_orig)):
    label = y_orig[i]
    features = X_orig[i]
    
    # 1. Always keep the original, unmodified sample
    augmented_X.append(features)
    augmented_y.append(label)
    
    # 2. Generate Synthetic variations
    for _ in range(SYNTHETIC_COPIES):
        # Technique A: Gaussian Noise 
        # Calculate standard deviation to keep noise proportional to the signal
        feature_std = np.std(features) if np.std(features) > 0 else 1.0
        noise = np.random.normal(0, 0.05 * feature_std, size=features.shape)
        
        # Technique B: Magnitude Scaling
        # Randomly scale the volume between 85% and 115%
        scale = np.random.uniform(0.85, 1.15)
        
        # Apply mathematically
        synthetic_features = (features + noise) * scale
        
        # Add to the new dataset
        augmented_X.append(synthetic_features)
        augmented_y.append(label)

augmented_X = np.array(augmented_X)
augmented_y = np.array(augmented_y)

print(f"Augmented Samples Generated: {augmented_X.shape[0]}")

# ==========================================
# 4. EXPORT TO NEW CSV
# ==========================================
# Combine labels and features back into a single dataframe
final_df = pd.DataFrame(augmented_X)
final_df.insert(0, 'label', augmented_y)

# Save to disk without headers or indices (hardware-style CSV)
final_df.to_csv(OUTPUT_FILE, index=False, header=False)

print(f"--- SUCCESS ---")
print(f"Your huge, robust dataset is saved as: {OUTPUT_FILE}")
print(f"Update your training script to read from '{OUTPUT_FILE}'!")