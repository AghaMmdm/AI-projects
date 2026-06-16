import pandas as pd
import numpy as np
import json
import argparse
import sys
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, mean_squared_error, silhouette_score
import optuna
import warnings

# Suppress warnings and Optuna logs for a cleaner UI output
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ==========================================
# TinyML Resource Profiler Class
# ==========================================
class TinyMLProfiler:
    """
    Analyzes compiled model files to estimate hardware resource utilization
    such as RAM, Flash memory, and computational complexity for TinyML devices.
    """
    @staticmethod
    def profile_model(filename="tinyml_model.py"):
        """
        Reads the exported Python file and calculates structural complexity metrics.
        """
        if not os.path.exists(filename):
            return
        
        # Calculate Flash size directly from the file size
        flash_size_kb = os.path.getsize(filename) / 1024.0
        
        # Read file to analyze internal structures for RAM and Complexity estimation
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            
        print("\n" + "="*60)
        print("📊 TINYML HARDWARE RESOURCE PROFILER REPORT")
        print("="*60)
        print(f"  -> Flash Memory Footprint : {flash_size_kb:.2f} KB")
        
        # Base overhead for MicroPython module tracking (approximate)
        estimated_ram_bytes = 512 
        ops_complexity = ""

        # 1. Profile Tree-Based Models (Decision Tree)
        if "decision_tree" in content:
            # Count elements in the feature list to determine number of nodes
            try:
                for line in content.split("\n"):
                    if line.startswith("features ="):
                        node_count = len(json.loads(line.split("=")[1].strip()))
                        # Each node stores integers/floats (approx. 16 bytes per node in RAM matrices)
                        estimated_ram_bytes += node_count * 16
                        print(f"  -> Total Tree Nodes       : {node_count}")
                        print(f"  -> Max Execution Steps    : O(log2({node_count})) comparisons")
                        break
            except Exception:
                pass

        # 2. Profile Linear Models (Regression / Logistic)
        elif "logistic_regression" in content or "linear_regression" in content:
            try:
                for line in content.split("\n"):
                    if line.startswith("weights ="):
                        raw_weights = json.loads(line.split("=")[1].strip())
                        # Check if weights matrix is 1D (binary) or 2D (multiclass)
                        if isinstance(raw_weights[0], list):
                            weight_count = len(raw_weights) * len(raw_weights[0])
                        else:
                            weight_count = len(raw_weights)
                        
                        estimated_ram_bytes += weight_count * 8 # 8 bytes per float64
                        print(f"  -> Total Model Weights    : {weight_count}")
                        print(f"  -> Compute Complexity     : {weight_count} MACs (Multiply-Accumulate)")
                        break
            except Exception:
                pass

        # 3. Profile Ensemble Models (Random Forest / Isolation Forest)
        elif "random_forest" in content or "isolation_forest" in content:
            try:
                for line in content.split("\n"):
                    if line.startswith("trees_features ="):
                        raw_trees = json.loads(line.split("=")[1].strip())
                        tree_count = len(raw_trees)
                        total_nodes = sum(len(t) for t in raw_trees)
                        estimated_ram_bytes += total_nodes * 16
                        print(f"  -> Parallel Estimators    : {tree_count} Trees")
                        print(f"  -> Total Combined Nodes   : {total_nodes}")
                        print(f"  -> Compute Complexity     : ~{tree_count} x Tree-Traversals")
                        break
            except Exception:
                pass

        # 4. Profile Distance-Based Models (K-Means)
        elif "kmeans_clustering" in content:
            try:
                for line in content.split("\n"):
                    if line.startswith("centroids ="):
                        centroids = json.loads(line.split("=")[1].strip())
                        cluster_count = len(centroids)
                        feature_count = len(centroids[0])
                        estimated_ram_bytes += cluster_count * feature_count * 8
                        print(f"  -> Cluster Centroids (K)  : {cluster_count}")
                        print(f"  -> Distance Computations  : {cluster_count * feature_count} Squared-Differences")
                        break
            except Exception:
                pass

        print(f"  -> Estimated RAM Occupancy: {estimated_ram_bytes / 1024.0:.2f} KB ({estimated_ram_bytes} Bytes)")
        print("="*60 + "\n")


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
            raise KeyError(f"Target column '{target_col}' not found in the dataset.")
        X = df.drop(columns=[target_col])
        y = df[target_col]
        X = pd.get_dummies(X, drop_first=True)
        classes = None
        if task_type == "classification":
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(y)
            classes = label_encoder.classes_
        return X, y, classes
    elif task_type in ["unsupervised", "anomaly"]:
        X = pd.get_dummies(df, drop_first=True)
        return X, None, None

# ==========================================
# AUTO MODE: Optuna Tuning Functions
# ==========================================
def tune_classification_models(X_train, X_test, y_train, y_test, n_trials=30):
    print(f"      -> Running Optuna Tuning ({n_trials} trials per model)...")
    
    def obj_dt(trial):
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        criterion = trial.suggest_categorical('criterion', ['gini', 'entropy'])
        clf = DecisionTreeClassifier(max_depth=max_depth, min_samples_split=min_samples_split, criterion=criterion, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
    study_dt = optuna.create_study(direction='maximize')
    study_dt.optimize(obj_dt, n_trials=n_trials)
    best_dt = DecisionTreeClassifier(**study_dt.best_params, random_state=42).fit(X_train, y_train)
    
    def obj_lr(trial):
        C = trial.suggest_float('C', 1e-3, 1e2, log=True)
        clf = LogisticRegression(C=C, max_iter=200, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
    study_lr = optuna.create_study(direction='maximize')
    study_lr.optimize(obj_lr, n_trials=n_trials)
    best_lr = LogisticRegression(**study_lr.best_params, max_iter=200, random_state=42).fit(X_train, y_train)

    def obj_rf(trial):
        max_depth = trial.suggest_int('max_depth', 3, 6)
        n_estimators = trial.suggest_int('n_estimators', 3, 5)
        criterion = trial.suggest_categorical('criterion', ['gini', 'entropy'])
        clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, criterion=criterion, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
    study_rf = optuna.create_study(direction='maximize')
    study_rf.optimize(obj_rf, n_trials=n_trials)
    best_rf = RandomForestClassifier(**study_rf.best_params, random_state=42).fit(X_train, y_train)

    best_gnb = GaussianNB().fit(X_train, y_train)
    gnb_acc = accuracy_score(y_test, best_gnb.predict(X_test))

    return {
        'Decision Tree': (best_dt, study_dt.best_value),
        'Logistic Regression': (best_lr, study_lr.best_value),
        'Random Forest': (best_rf, study_rf.best_value),
        'Gaussian Naive Bayes': (best_gnb, gnb_acc)
    }

def tune_regression_models(X_train, X_test, y_train, y_test, n_trials=30):
    print(f"      -> Running Optuna Tuning ({n_trials} trials per model)...")
    
    def obj_dt(trial):
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        reg = DecisionTreeRegressor(max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
    study_dt = optuna.create_study(direction='minimize')
    study_dt.optimize(obj_dt, n_trials=n_trials)
    best_dt = DecisionTreeRegressor(**study_dt.best_params, random_state=42).fit(X_train, y_train)
    
    def obj_ridge(trial):
        alpha = trial.suggest_float('alpha', 1e-3, 1e3, log=True)
        reg = Ridge(alpha=alpha, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
    study_ridge = optuna.create_study(direction='minimize')
    study_ridge.optimize(obj_ridge, n_trials=n_trials)
    best_ridge = Ridge(**study_ridge.best_params, random_state=42).fit(X_train, y_train)

    def obj_rf(trial):
        max_depth = trial.suggest_int('max_depth', 3, 6)
        n_estimators = trial.suggest_int('n_estimators', 3, 5)
        reg = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
    study_rf = optuna.create_study(direction='minimize')
    study_rf.optimize(obj_rf, n_trials=n_trials)
    best_rf = RandomForestRegressor(**study_rf.best_params, random_state=42).fit(X_train, y_train)

    return {
        'Decision Tree Regressor': (best_dt, study_dt.best_value),
        'Linear Regression (Ridge)': (best_ridge, study_ridge.best_value),
        'Random Forest Regressor': (best_rf, study_rf.best_value)
    }

# ==========================================
# MANUAL MODE: Training Functions
# ==========================================
def train_manual_classification_models(X_train, X_test, y_train, y_test, params):
    print("      -> Training models with manual extended hyperparameters...")
    dt_p, lr_p, rf_p = params.get('decision_tree', {}), params.get('logistic_regression', {}), params.get('random_forest', {})
    
    dt = DecisionTreeClassifier(max_depth=dt_p.get('max_depth', 5), min_samples_split=dt_p.get('min_samples_split', 2), min_samples_leaf=dt_p.get('min_samples_leaf', 1), criterion=dt_p.get('criterion', 'gini'), random_state=42).fit(X_train, y_train)
    lr = LogisticRegression(C=lr_p.get('C', 1.0), penalty=lr_p.get('penalty', 'l2'), solver=lr_p.get('solver', 'lbfgs'), max_iter=200, random_state=42).fit(X_train, y_train)
    rf = RandomForestClassifier(n_estimators=rf_p.get('n_estimators', 5), max_depth=rf_p.get('max_depth', 5), min_samples_split=rf_p.get('min_samples_split', 2), min_samples_leaf=rf_p.get('min_samples_leaf', 1), criterion=rf_p.get('criterion', 'gini'), random_state=42).fit(X_train, y_train)
    gnb = GaussianNB().fit(X_train, y_train)

    return {
        'Decision Tree': (dt, accuracy_score(y_test, dt.predict(X_test))),
        'Logistic Regression': (lr, accuracy_score(y_test, lr.predict(X_test))),
        'Random Forest': (rf, accuracy_score(y_test, rf.predict(X_test))),
        'Gaussian Naive Bayes': (gnb, accuracy_score(y_test, gnb.predict(X_test)))
    }

def train_manual_regression_models(X_train, X_test, y_train, y_test, params):
    print("      -> Training models with manual extended hyperparameters...")
    dt_p, ridge_p, rf_p = params.get('decision_tree', {}), params.get('ridge_regression', {}), params.get('random_forest', {})
    
    dt = DecisionTreeRegressor(max_depth=dt_p.get('max_depth', 5), min_samples_split=dt_p.get('min_samples_split', 2), min_samples_leaf=dt_p.get('min_samples_leaf', 1), random_state=42).fit(X_train, y_train)
    ridge = Ridge(alpha=ridge_p.get('alpha', 1.0), solver=ridge_p.get('solver', 'auto'), random_state=42).fit(X_train, y_train)
    rf = RandomForestRegressor(n_estimators=rf_p.get('n_estimators', 5), max_depth=rf_p.get('max_depth', 5), min_samples_split=rf_p.get('min_samples_split', 2), min_samples_leaf=rf_p.get('min_samples_leaf', 1), random_state=42).fit(X_train, y_train)

    return {
        'Decision Tree Regressor': (dt, mean_squared_error(y_test, dt.predict(X_test))),
        'Linear Regression (Ridge)': (ridge, mean_squared_error(y_test, ridge.predict(X_test))),
        'Random Forest Regressor': (rf, mean_squared_error(y_test, rf.predict(X_test)))
    }

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
        f.write("# Auto-Generated by TinyML AutoML Engine\n")
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
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML Engine\n")
        if is_classifier:
            if len(classes) > 2:
                f.write("model_type = 'logistic_regression_multiclass'\n")
                weights = np.round(model.coef_, 4).tolist()
                intercept = np.round(model.intercept_, 4).tolist()
            else:
                f.write("model_type = 'logistic_regression_binary'\n")
                weights = np.round(model.coef_[0], 4).tolist()
                intercept = round(float(model.intercept_[0]), 4)
            f.write(f"classes = {[str(c) for c in classes]}\n")
        else:
            f.write("model_type = 'linear_regression'\n")
            weights = np.round(model.coef_, 4).tolist()
            intercept = round(float(model.intercept_), 4)
        f.write(f"weights = {weights}\n")
        f.write(f"intercept = {intercept}\n")

def export_gnb(model, filename="tinyml_model.py", classes=None):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML Engine\n")
        f.write("model_type = 'gaussian_nb'\n")
        f.write(f"theta = {np.round(model.theta_, 4).tolist()}\n")
        f.write(f"var = {np.round(model.var_, 4).tolist()}\n")
        f.write(f"prior = {np.round(model.class_prior_, 4).tolist()}\n")
        f.write(f"classes = {[str(c) for c in classes]}\n")

def export_random_forest(model, filename="tinyml_model.py", is_classifier=True, classes=None):
    trees_features, trees_thresholds, trees_left, trees_right, trees_values = [], [], [], [], []
    for estimator in model.estimators_:
        tree = estimator.tree_
        trees_features.append(tree.feature.tolist())
        trees_thresholds.append([round(x, 4) for x in tree.threshold.tolist()])
        trees_left.append(tree.children_left.tolist())
        trees_right.append(tree.children_right.tolist())
        if is_classifier:
            trees_values.append([[round(float(c), 4) for c in v[0]] for v in tree.value])
        else:
            trees_values.append([round(float(v[0][0]), 4) for v in tree.value])
            
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML Engine\n")
        f.write(f"model_type = 'random_forest_{'classifier' if is_classifier else 'regressor'}'\n")
        f.write(f"trees_features = {trees_features}\n")
        f.write(f"trees_thresholds = {trees_thresholds}\n")
        f.write(f"trees_left = {trees_left}\n")
        f.write(f"trees_right = {trees_right}\n")
        f.write(f"trees_values = {trees_values}\n")
        if is_classifier and classes is not None:
            f.write(f"classes = {[str(c) for c in classes]}\n")

def export_isolation_forest(model, filename="tinyml_model.py"):
    trees_features, trees_thresholds, trees_left, trees_right = [], [], [], []
    for estimator in model.estimators_:
        tree = estimator.tree_
        trees_features.append(tree.feature.tolist())
        trees_thresholds.append([round(x, 4) for x in tree.threshold.tolist()])
        trees_left.append(tree.children_left.tolist())
        trees_right.append(tree.children_right.tolist())
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML Engine\n")
        f.write("model_type = 'isolation_forest'\n")
        f.write(f"trees_features = {trees_features}\n")
        f.write(f"trees_thresholds = {trees_thresholds}\n")
        f.write(f"trees_left = {trees_left}\n")
        f.write(f"trees_right = {trees_right}\n")

def export_kmeans(model, filename="tinyml_model.py"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML Engine\n")
        f.write(f"model_type = 'kmeans_clustering'\n")
        f.write(f"centroids = {np.round(model.cluster_centers_, 4).tolist()}\n")
        f.write("n_clusters = len(centroids)\n")

# ==========================================
# Main Application Pipeline Execution
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TinyML AutoML Engine")
    parser.add_argument("--config", required=True, help="Path to the JSON configuration file")
    args = parser.parse_args()

    try:
        with open(args.config, 'r', encoding='utf-8') as file:
            config = json.load(file)
            
        csv_path = config.get("csv_path")
        task_choice = str(config.get("task_type"))
        target_column = config.get("target_column")
        exec_mode = config.get("execution_mode", "auto").lower()
        hyperparams = config.get("hyperparameters", {})
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file '{csv_path}' not found.")
            
        df = pd.read_csv(csv_path)
        print(f"[*] Configuration Loaded. Mode: {exec_mode.upper()} | Task Type: {task_choice}")
        
        # 1. CLASSIFICATION
        if task_choice == '1':
            X, y, classes = preprocess_data(df, target_column, "classification")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            results = train_manual_classification_models(X_train, X_test, y_train, y_test, hyperparams) if exec_mode == "manual" else tune_classification_models(X_train, X_test, y_train, y_test)
            best_model_name, best_model_obj, best_score = "", None, -1
            for name, (model, acc) in results.items():
                print(f"  -> {name}: {acc * 100:.2f}%")
                if acc > best_score: best_score, best_model_name, best_model_obj = acc, name, model
            if "Decision Tree" in best_model_name: export_decision_tree(best_model_obj, is_classifier=True, classes=classes)
            elif "Logistic Regression" in best_model_name: export_linear_model(best_model_obj, is_classifier=True, classes=classes)
            elif "Random Forest" in best_model_name: export_random_forest(best_model_obj, is_classifier=True, classes=classes)
            elif "Gaussian Naive Bayes" in best_model_name: export_gnb(best_model_obj, classes=classes)

        # 2. REGRESSION
        elif task_choice == '2':
            X, y, _ = preprocess_data(df, target_column, "regression")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            results = train_manual_regression_models(X_train, X_test, y_train, y_test, hyperparams) if exec_mode == "manual" else tune_regression_models(X_train, X_test, y_train, y_test)
            best_model_name, best_model_obj, best_score = "", None, float('inf')
            for name, (model, mse) in results.items():
                print(f"  -> {name} MSE: {mse:.4f}")
                if mse < best_score: best_score, best_model_name, best_model_obj = mse, name, model
            if "Decision Tree" in best_model_name: export_decision_tree(best_model_obj, is_classifier=False)
            elif "Linear Regression" in best_model_name: export_linear_model(best_model_obj, is_classifier=False)
            elif "Random Forest" in best_model_name: export_random_forest(best_model_obj, is_classifier=False)

        # 3. CLUSTERING
        elif task_choice == '3':
            X, _, _ = preprocess_data(df, task_type="unsupervised")
            if exec_mode == "manual":
                km_p = hyperparams.get('kmeans', {})
                best_model = KMeans(n_clusters=km_p.get('n_clusters', 3), init=km_p.get('init', 'k-means++'), max_iter=km_p.get('max_iter', 300), random_state=42).fit(X)
            else:
                best_k, best_score, best_model = 2, -1, None
                for k in range(2, min(6, len(X))):
                    kmeans = KMeans(n_clusters=k, random_state=42)
                    labels = kmeans.fit_predict(X)
                    score = silhouette_score(X, labels)
                    if score > best_score: best_score, best_k, best_model = score, k, kmeans
            export_kmeans(best_model)

        # 4. ANOMALY DETECTION
        elif task_choice == '4':
            X, _, _ = preprocess_data(df, task_type="anomaly")
            n_est = hyperparams.get('isolation_forest', {}).get('n_estimators', 5) if exec_mode == "manual" else 5
            iso_forest = IsolationForest(n_estimators=n_est, random_state=42).fit(X)
            export_isolation_forest(iso_forest)

        # Trigger the Hardware Profiler post-generation
        TinyMLProfiler.profile_model("tinyml_model.py")
        print("\n✅ Success! Execution pipeline completed cleanly.")

    except Exception as e:
        print(f"❌ Error during execution: {e}")