# End-to-End Credit Card Fraud Detection Pipeline

An advanced, production-grade Machine Learning pipeline designed to detect fraudulent credit card transactions. This project tackles the extreme class imbalance challenge (0.172% fraud rate) using state-of-the-art ensemble techniques, hyperparameter optimization, and model explainability frameworks.

## 📌 Project Overview
Financial fraud detection requires high-precision modeling where traditional metrics like standard Accuracy fail completely. This repository demonstrates a rigorous machine learning workflow from Advanced Exploratory Data Analysis (EDA) to model interpretation, achieving an exceptional **F1-Score of 0.87** on highly skewed real-world banking data.

## 📊 Dataset & Storage Notice
The dataset used is the **Kaggle Credit Card Fraud Detection** dataset containing 284,807 transactions.
* **Important:** Due to GitHub's file size limitations, the raw `creditcard.csv` file is excluded from this repository via `.gitignore`.
* **Data Source:** You can download the official dataset directly from [Kaggle Credit Card Fraud Detection Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).
* **Setup:** Place the downloaded `creditcard.csv` into your root directory before running the notebook.

## 🛠️ Key Pipeline Architecture

### 1. Exploratory Data Analysis & Feature Scaling
* **Statistical Alignment:** Employed the Kolmogorov-Smirnov test (`ks_2samp`) to rigorously analyze distribution variance between genuine and fraudulent classes across anonymized PCA features ($V_1$ to $V_{28}$).
* **Robust Scaling:** Implemented `RobustScaler` on `Time` and `Amount` features to nullify the leverage of heavy financial outliers.

### 2. Overcoming Extreme Imbalance
Instead of distorting the feature space with synthetic data generation (such as SMOTE/SMOTEENN) which led to high False Positive rates during testing, this architecture leverages the native cost-sensitive learning of gradient boosted trees via dynamically computed class weights:
$$
\text{scale\_pos\_weight} = \frac{\text{Total Negative Samples}}{\text{Total Positive Samples}}
$$

### 3. Hyperparameter Tuning via Optuna
Rather than optimizing for generic ROC-AUC, an automated **Optuna** study was constructed to directly maximize **PR-AUC (Average Precision)**. This forces the optimizer to focus exclusively on the minority class performance, avoiding the "Imbalance Trap."

### 4. Custom Decision Threshold Tuning
In production fraud detection, the default $0.5$ classification threshold is rarely optimal. By extracting raw probabilities (`predict_proba`) and mapping the Precision-Recall curve, the optimal decision boundary was located at **Threshold = 0.9**, striking the ultimate balance between stopping fraud and preventing genuine card blocks.

## 📈 Experimental Results

### Final XGBoost Classifier Performance (Optimized Threshold = 0.9)

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **0 (Genuine)** | 1.00 | 1.00 | 1.00 | 56,864 |
| **1 (Fraudulent)** | **0.90** | **0.84** | **0.87** | 98 |
| **Macro Average** | 0.95 | 0.92 | 0.93 | 56,962 |

## 🔮 Model Explainability (SHAP Interpretation)
To eliminate the "black-box" nature of Gradient Boosting, **SHAP (SHapley Additive exPlanations)** was integrated. 
* The post-training analysis explicitly shows that latent features **V14**, **V4**, and **V12** hold the highest predictive power and global importance when evaluating a transaction's risk profile.
<img width="599" height="453" alt="image" src="https://github.com/user-attachments/assets/e6ace591-c2e1-4955-a27b-76d80be7c202" />
