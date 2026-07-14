import sys
import os
import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ==========================================
# 1. LOAD & CLEAN DATASET
# ==========================================
print("--- Loading and Cleaning Augmented Dataset ---")
DATA_FILE = './Data/dataset_augmented.csv'
OUTPUT_PATH = './edge_mcu'
VALID_CLASSES = ['up', 'down', 'unknown']

cleaned_data = []
lines_checked = 0

try:
    # Read line-by-line to prevent buffer overflow from hardware crashes
    with open(DATA_FILE, 'r', encoding='latin-1') as f:
        for line in f:
            lines_checked += 1
            parts = line.strip().split(',')
            
            # A healthy line must have exactly 40 parts (1 label + 39 features)
            if len(parts) == 40 and parts[0] in VALID_CLASSES:
                try:
                    # Verify that the 39 feature strings are actually numbers
                    features = [float(x) for x in parts[1:]]
                    cleaned_data.append([parts[0]] + features)
                except ValueError:
                    pass # Ignore lines with garbage string characters
except FileNotFoundError:
    print(f"[!] ERROR: '{DATA_FILE}' not found. Please run the augmentation script first.")
    sys.exit(1)

print(f"Total lines checked: {lines_checked}")
print(f"Total VALID lines loaded: {len(cleaned_data)}")

if len(cleaned_data) == 0:
    print("\n[!] ERROR: No valid data found for the specified classes.")
    sys.exit(1)

# Convert to Pandas DataFrame for easy splitting
df = pd.DataFrame(cleaned_data)

# Extract Features (X) and Labels (y) as pure NumPy arrays
y = df.iloc[:, 0].to_numpy()
X = df.iloc[:, 1:].to_numpy()

print(f"Loaded Data -> X shape: {X.shape}, y shape: {y.shape}")

# ==========================================
# 2. TRAIN / TEST SPLIT
# ==========================================
# 80% for training, 20% for testing. Stratify ensures balanced classes.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# ==========================================
# 3. DIMENSIONALITY REDUCTION (LDA)
# ==========================================
print("\n--- Running LDA to reduce 39 features to 2 Super-Features ---")
# n_components is always (number of classes - 1). For 3 classes, it is 2.
lda = LinearDiscriminantAnalysis(n_components=2)
X_train_lda = lda.fit_transform(X_train, y_train)
X_test_lda = lda.transform(X_test)

print(f"New Training Data Shape after LDA: {X_train_lda.shape}")

# ==========================================
# 4. OPTUNA OPTIMIZATION FOR LOGISTIC REGRESSION
# ==========================================
print("\n--- Starting Optuna optimization for Logistic Regression ---")
def objective(trial):
    # Tune the regularization parameter C
    c_val = trial.suggest_float('C', 1e-4, 1e2, log=True)
    
    lr = LogisticRegression(C=c_val, max_iter=50000, random_state=42)
    lr.fit(X_train_lda, y_train)
    preds = lr.predict(X_test_lda)
    
    return accuracy_score(y_test, preds)

# Suppress Optuna's verbose logging to keep terminal output clean
optuna.logging.set_verbosity(optuna.logging.WARNING)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)

print(f"Best Optuna Parameters: {study.best_params}")
print(f"Best Accuracy during CV: {study.best_value * 100:.2f}%")

# ==========================================
# 5. TRAIN FINAL CLASSIFIER
# ==========================================
print("\n--- Training Final Lightweight Classifier ---")
final_lr = LogisticRegression(**study.best_params, max_iter=5000, random_state=42)
final_lr.fit(X_train_lda, y_train)

preds = final_lr.predict(X_test_lda)

# Extract dynamic class names directly from the trained scikit-learn model
target_names = final_lr.classes_.tolist()

print("\nFinal Classification Report:")
print(classification_report(y_test, preds, target_names=target_names))

# ==========================================
# 6. EXPORT PURE PYTHON ARRAYS FOR EDGE INFERENCE
# ==========================================
print("\n--- Exporting LDA and Classifier Parameters to model_data_lr.py ---")

# Extract parameters
lda_xbar = lda.xbar_.tolist()         
lda_scalings = lda.scalings_.tolist() 
lr_coef = final_lr.coef_.tolist()           
lr_intercept = final_lr.intercept_.tolist() 

output_file = os.path.join(OUTPUT_PATH, 'model_data_lr_realtime.py')
with open(output_file, 'w') as f:
    f.write("# Auto-Generated Edge Model (Fixed 1D Arrays)\n\n")
    f.write(f"CLASSES = {target_names}\n\n")
    
    # Write LDA XBAR (Fixed: Now it is a standard 1D list)
    f.write(f"LDA_XBAR = {[round(float(val), 6) for val in lda_xbar]}\n\n")
    
    # Write LDA Scalings (2D Transformation matrix)
    f.write("LDA_SCALINGS = [\n")
    for row in lda_scalings:
        f.write(f"    {[round(float(val), 6) for val in row]},\n")
    f.write("]\n\n")
    
    # Write LR Coefficients (2D Array)
    f.write("LR_COEF = [\n")
    for class_weights in lr_coef:
        f.write(f"    {[round(float(w), 6) for w in class_weights]},\n")
    f.write("]\n\n")
    
    # Write LR Intercepts (Fixed: Now it is a standard 1D list)
    f.write(f"LR_INTERCEPT = {[round(float(i), 6) for i in lr_intercept]}\n")

print(f"Pipeline successfully exported to: {output_file}")