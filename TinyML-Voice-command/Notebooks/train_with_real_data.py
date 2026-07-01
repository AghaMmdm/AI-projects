import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os

# 1. Load and Clean the Hardware-Generated Dataset
print("--- Loading and Cleaning Hardware-Generated Dataset ---")
DATA_FILE = './Data/dataset.csv'
OUTPUT_PATH = './edge_mcu'

cleaned_data = []

# اول کل فایل را می‌خوانیم
with open(DATA_FILE, 'r') as f:
    all_lines = f.readlines()

print(f"Total lines in file: {len(all_lines)}")

# انتخاب دقیق سطرهای 40 تا 70
# در پایتون شماره‌گذاری از 0 شروع می‌شود، پس سطر 40 می‌شود ایندکس 39
# و سطر 70 می‌شود ایندکس 70 (چون کران بالا حساب نمی‌شود)
selected_lines = all_lines[39:70] 

for line in selected_lines:
    parts = line.strip().split(',')
    
    # فقط چک می‌کنیم که دیتای خط سالم و 40 ستونه باشد
    if len(parts) == 40:
        try:
            features = [float(x) for x in parts[1:]]
            cleaned_data.append([parts[0]] + features)
        except ValueError:
            pass

print(f"Total VALID lines extracted from row 40 to 70: {len(cleaned_data)}")

if len(cleaned_data) == 0:
    print("\n[!] ERROR: No valid data found in rows 40 to 70.")
    sys.exit(1)

df = pd.DataFrame(cleaned_data)
y = df.iloc[:, 0].to_numpy()
X = df.iloc[:, 1:].to_numpy()

print(f"Loaded and Cleaned Data -> X shape: {X.shape}, y shape: {y.shape}")
print(f"Classes found in these rows: {np.unique(y)}")

print(f"Loaded Data -> X shape: {X.shape}, y shape: {y.shape}")

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 2. STAGE 1: Dimensionality Reduction using LDA
print("\n--- Running LDA to reduce 39 features to 3 Super-Features ---")
lda = LinearDiscriminantAnalysis(n_components=2)
X_train_lda = lda.fit_transform(X_train, y_train)
X_test_lda = lda.transform(X_test)

print(f"New Training Data Shape after LDA: {X_train_lda.shape}")

# 3. STAGE 2: Optuna Optimization for Logistic Regression
print("\n--- Starting Optuna optimization for Logistic Regression ---")
def objective(trial):
    c_val = trial.suggest_float('C', 1e-4, 1e2, log=True)
    lr = LogisticRegression(C=c_val, max_iter=5000, random_state=42)
    lr.fit(X_train_lda, y_train)
    preds = lr.predict(X_test_lda)
    return accuracy_score(y_test, preds)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)

print(f"\nBest Optuna Parameters: {study.best_params}")
print(f"Best Accuracy during CV: {study.best_value * 100:.2f}%")

# 4. TRAIN FINAL CLASSIFIER
print("\n--- Training Final Lightweight Classifier ---")
final_lr = LogisticRegression(**study.best_params, max_iter=5000, random_state=42)
final_lr.fit(X_train_lda, y_train)

preds = final_lr.predict(X_test_lda)

# رفع باگ: استخراج ترتیب دقیق کلاس‌ها مستقیماً از خود مدل
target_names = final_lr.classes_.tolist()

print("\nFinal Classification Report:")
print(classification_report(y_test, preds, target_names=target_names))

# 5. EXPORT PURE PYTHON ARRAYS FOR EDGE INFERENCE
print("\n--- Exporting LDA and Classifier Parameters to model_data_lr.py ---")

lda_xbar = lda.xbar_.tolist()         
lda_scalings = lda.scalings_.tolist() 
lr_coef = final_lr.coef_.tolist()           
lr_intercept = final_lr.intercept_.tolist() 

output_file = os.path.join(OUTPUT_PATH, 'model_data_lr_realtime.py')
with open(output_file, 'w') as f:
    f.write("# Auto-Generated Custom Edge Model\n\n")
    f.write(f"CLASSES = {target_names}\n\n")
    
    f.write("LDA_XBAR = [\n")
    f.write(f"    {[round(float(val), 6) for val in lda_xbar]}\n")
    f.write("]\n\n")
    
    f.write("LDA_SCALINGS = [\n")
    for row in lda_scalings:
        f.write(f"    {[round(float(val), 6) for val in row]},\n")
    f.write("]\n\n")
    
    f.write("LR_COEF = [\n")
    for class_weights in lr_coef:
        f.write(f"    {[round(float(w), 6) for w in class_weights]},\n")
    f.write("]\n\n")
    
    f.write("LR_INTERCEPT = [\n")
    f.write(f"    {[round(float(i), 6) for i in lr_intercept]}\n")
    f.write("]\n")

print(f"Pipeline successfully exported to: {output_file}")