import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, mean_squared_error, silhouette_score
import optuna
import warnings

# Suppress warnings and Optuna logs for a cleaner CLI
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

def preprocess_data(df, target_col=None, task_type="classification"):
    print("\n[1/4] Preprocessing data...")
    
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna(df[col].mode()[0])
            else:
                df[col] = df[col].fillna(df[col].mean())
                
    if task_type in ["classification", "regression"]:
        if target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' not found.")
            
        X = df.drop(columns=[target_col])
        y = df[target_col]
        X = pd.get_dummies(X, drop_first=True)
        
        classes = None
        if task_type == "classification":
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(y)
            classes = label_encoder.classes_
            
        return X, y, classes
        
    elif task_type == "unsupervised":
        X = pd.get_dummies(df, drop_first=True)
        return X, None, None

# ==========================================
# Optuna Tuning Functions
# ==========================================
def tune_classification_models(X_train, X_test, y_train, y_test, n_trials=30):
    print(f"      -> Running Optuna Tuning ({n_trials} trials per model)...")
    
    # 1. Tune Decision Tree
    def obj_dt(trial):
        # Constrain max_depth for TinyML (RAM limits)
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        clf = DecisionTreeClassifier(max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
        
    study_dt = optuna.create_study(direction='maximize')
    study_dt.optimize(obj_dt, n_trials=n_trials)
    best_dt = DecisionTreeClassifier(**study_dt.best_params, random_state=42).fit(X_train, y_train)
    
    # 2. Tune Logistic Regression
    def obj_lr(trial):
        C = trial.suggest_float('C', 1e-3, 1e2, log=True)
        clf = LogisticRegression(C=C, max_iter=200, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
        
    study_lr = optuna.create_study(direction='maximize')
    study_lr.optimize(obj_lr, n_trials=n_trials)
    best_lr = LogisticRegression(**study_lr.best_params, max_iter=200, random_state=42).fit(X_train, y_train)
    
    return best_dt, study_dt.best_value, best_lr, study_lr.best_value

def tune_regression_models(X_train, X_test, y_train, y_test, n_trials=30):
    print(f"      -> Running Optuna Tuning ({n_trials} trials per model)...")
    
    # 1. Tune Decision Tree Regressor
    def obj_dt(trial):
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        reg = DecisionTreeRegressor(max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
        
    study_dt = optuna.create_study(direction='minimize') # Minimize MSE
    study_dt.optimize(obj_dt, n_trials=n_trials)
    best_dt = DecisionTreeRegressor(**study_dt.best_params, random_state=42).fit(X_train, y_train)
    
    # 2. Tune Ridge Regression (Linear Model with L2 Regularization)
    def obj_ridge(trial):
        alpha = trial.suggest_float('alpha', 1e-3, 1e3, log=True)
        reg = Ridge(alpha=alpha, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
        
    study_ridge = optuna.create_study(direction='minimize') # Minimize MSE
    study_ridge.optimize(obj_ridge, n_trials=n_trials)
    best_ridge = Ridge(**study_ridge.best_params, random_state=42).fit(X_train, y_train)
    
    return best_dt, study_dt.best_value, best_ridge, study_ridge.best_value

# ==========================================
# TinyML Export Functions
# ==========================================
def export_decision_tree(model, filename="tinyml_model.py", is_classifier=True, classes=None):
    tree = model.tree_
    features = tree.feature.tolist()
    thresholds = [round(x, 4) for x in tree.threshold.tolist()]
    left = tree.children_left.tolist()
    right = tree.children_right.tolist()
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML with Optuna\n")
        f.write(f"model_type = 'decision_tree_{'classifier' if is_classifier else 'regressor'}'\n")
        f.write(f"features = {features}\n")
        f.write(f"thresholds = {thresholds}\n")
        f.write(f"left = {left}\n")
        f.write(f"right = {right}\n")
        
        if is_classifier and classes is not None:
            node_classes = [str(classes[np.argmax(v)]) for v in tree.value]
            unique_classes = list(set(node_classes))
            class_indices = [unique_classes.index(c) for c in node_classes]
            f.write(f"unique_classes = {unique_classes}\n")
            f.write(f"class_indices = {class_indices}\n")
        else:
            values = [round(float(v[0][0]), 4) for v in tree.value]
            f.write(f"values = {values}\n")

def export_linear_model(model, filename="tinyml_model.py", is_classifier=True, classes=None):
    weights = np.round(model.coef_[0] if is_classifier else model.coef_, 4).tolist()
    intercept = round(float(model.intercept_[0] if is_classifier else model.intercept_), 4)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML with Optuna\n")
        f.write(f"model_type = '{'logistic_regression' if is_classifier else 'linear_regression'}'\n")
        f.write(f"weights = {weights}\n")
        f.write(f"intercept = {intercept}\n")
        if is_classifier and classes is not None:
            f.write(f"classes = {[str(c) for c in classes]}\n")

def export_kmeans(model, filename="tinyml_model.py"):
    centroids = np.round(model.cluster_centers_, 4).tolist()
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML\n")
        f.write(f"model_type = 'kmeans_clustering'\n")
        f.write(f"centroids = {centroids}\n")
        f.write("n_clusters = len(centroids)\n")

# ==========================================
# Main Application CLI
# ==========================================
if __name__ == "__main__":
    print("=== Welcome to TinyML AutoML Platform ===")
    csv_path = input("Please enter the path to your CSV file: ")
    
    print("\nSelect the Machine Learning Task Type:")
    print("1. Classification (Supervised - Predict a category/class)")
    print("2. Regression     (Supervised - Predict a continuous number)")
    print("3. Clustering     (Unsupervised - Grouping data without labels)")
    
    task_choice = input("Enter 1, 2, or 3: ")
    
    try:
        df = pd.read_csv(csv_path)
        
        if task_choice == '1':
            target_column = input("Enter the target column name (Label): ")
            X, y, classes = preprocess_data(df, target_column, "classification")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            print("\n[2/4] Optimizing Hyperparameters with Optuna...")
            best_dt, dt_acc, best_lr, lr_acc = tune_classification_models(X_train, X_test, y_train, y_test)
            
            print("\n[3/4] Optimization Results:")
            print(f"  -> Optimized Decision Tree Accuracy: {dt_acc * 100:.2f}%")
            print(f"  -> Optimized Logistic Regression Accuracy: {lr_acc * 100:.2f}%")
            
            print("\n[4/4] Exporting the best classification model...")
            if dt_acc >= lr_acc:
                export_decision_tree(best_dt, is_classifier=True, classes=classes)
                print("🏆 Exported: Decision Tree Classifier")
            else:
                export_linear_model(best_lr, is_classifier=True, classes=classes)
                print("🏆 Exported: Logistic Regression")

        elif task_choice == '2':
            target_column = input("Enter the target column name (Label): ")
            X, y, _ = preprocess_data(df, target_column, "regression")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            print("\n[2/4] Optimizing Hyperparameters with Optuna...")
            best_dt, dt_mse, best_ridge, ridge_mse = tune_regression_models(X_train, X_test, y_train, y_test)
            
            print("\n[3/4] Optimization Results (Lower MSE is better):")
            print(f"  -> Optimized Decision Tree MSE: {dt_mse:.4f}")
            print(f"  -> Optimized Linear (Ridge) Regression MSE: {ridge_mse:.4f}")
            
            print("\n[4/4] Exporting the best regression model...")
            if dt_mse <= ridge_mse:
                export_decision_tree(best_dt, is_classifier=False)
                print("🏆 Exported: Decision Tree Regressor")
            else:
                export_linear_model(best_ridge, is_classifier=False)
                print("🏆 Exported: Linear Regression")

        elif task_choice == '3':
            # Unsupervised flow remains unchanged (Silhouette Score logic is already an optimizer)
            X, _, _ = preprocess_data(df, task_type="unsupervised")
            print("\n[2/4] Training model: K-Means Clustering...")
            best_k, best_score, best_model = 2, -1, None
            
            for k in range(2, min(6, len(X))):
                kmeans = KMeans(n_clusters=k, random_state=42)
                labels = kmeans.fit_predict(X)
                score = silhouette_score(X, labels)
                if score > best_score:
                    best_score, best_k, best_model = score, k, kmeans
                    
            print(f"  -> Best K found: {best_k} (Silhouette Score: {best_score:.4f})")
            print("\n[3/4] Exporting K-Means Centroids...")
            export_kmeans(best_model)
            print("🏆 Exported: K-Means Clustering Model")

        else:
            print("❌ Invalid selection. Please restart.")

        print("\n✅ Success! 'tinyml_model.py' is ready for your Pyboard.")

    except Exception as e:
        print(f"❌ Error during execution: {e}")