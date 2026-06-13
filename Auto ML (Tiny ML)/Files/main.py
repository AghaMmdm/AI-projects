import pandas as pd
import numpy as np
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
        
    elif task_type in ["unsupervised", "anomaly"]:
        X = pd.get_dummies(df, drop_first=True)
        return X, None, None

def tune_classification_models(X_train, X_test, y_train, y_test, n_trials=30):
    print(f"      -> Running Optuna Tuning ({n_trials} trials per model)...")
    
    # 1. Decision Tree
    def obj_dt(trial):
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        clf = DecisionTreeClassifier(max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
        
    study_dt = optuna.create_study(direction='maximize')
    study_dt.optimize(obj_dt, n_trials=n_trials)
    best_dt = DecisionTreeClassifier(**study_dt.best_params, random_state=42).fit(X_train, y_train)
    
    # 2. Logistic Regression
    def obj_lr(trial):
        C = trial.suggest_float('C', 1e-3, 1e2, log=True)
        clf = LogisticRegression(C=C, max_iter=200, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
        
    study_lr = optuna.create_study(direction='maximize')
    study_lr.optimize(obj_lr, n_trials=n_trials)
    best_lr = LogisticRegression(**study_lr.best_params, max_iter=200, random_state=42).fit(X_train, y_train)

    # 3. Micro Random Forest
    def obj_rf(trial):
        max_depth = trial.suggest_int('max_depth', 3, 6)
        n_estimators = trial.suggest_int('n_estimators', 3, 5) # Limited for TinyML RAM
        clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        clf.fit(X_train, y_train)
        return accuracy_score(y_test, clf.predict(X_test))
        
    study_rf = optuna.create_study(direction='maximize')
    study_rf.optimize(obj_rf, n_trials=n_trials)
    best_rf = RandomForestClassifier(**study_rf.best_params, random_state=42).fit(X_train, y_train)

    # 4. Gaussian Naive Bayes (No tuning required)
    best_gnb = GaussianNB()
    best_gnb.fit(X_train, y_train)
    gnb_acc = accuracy_score(y_test, best_gnb.predict(X_test))

    results = {
        'Decision Tree': (best_dt, study_dt.best_value),
        'Logistic Regression': (best_lr, study_lr.best_value),
        'Random Forest': (best_rf, study_rf.best_value),
        'Gaussian Naive Bayes': (best_gnb, gnb_acc)
    }
    
    return results

def tune_regression_models(X_train, X_test, y_train, y_test, n_trials=30):
    print(f"      -> Running Optuna Tuning ({n_trials} trials per model)...")
    
    # 1. Decision Tree Regressor
    def obj_dt(trial):
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
        reg = DecisionTreeRegressor(max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
        
    study_dt = optuna.create_study(direction='minimize')
    study_dt.optimize(obj_dt, n_trials=n_trials)
    best_dt = DecisionTreeRegressor(**study_dt.best_params, random_state=42).fit(X_train, y_train)
    
    # 2. Ridge Regression
    def obj_ridge(trial):
        alpha = trial.suggest_float('alpha', 1e-3, 1e3, log=True)
        reg = Ridge(alpha=alpha, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
        
    study_ridge = optuna.create_study(direction='minimize')
    study_ridge.optimize(obj_ridge, n_trials=n_trials)
    best_ridge = Ridge(**study_ridge.best_params, random_state=42).fit(X_train, y_train)

    # 3. Micro Random Forest Regressor
    def obj_rf(trial):
        max_depth = trial.suggest_int('max_depth', 3, 6)
        n_estimators = trial.suggest_int('n_estimators', 3, 5)
        reg = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        reg.fit(X_train, y_train)
        return mean_squared_error(y_test, reg.predict(X_test))
        
    study_rf = optuna.create_study(direction='minimize')
    study_rf.optimize(obj_rf, n_trials=n_trials)
    best_rf = RandomForestRegressor(**study_rf.best_params, random_state=42).fit(X_train, y_train)

    results = {
        'Decision Tree Regressor': (best_dt, study_dt.best_value),
        'Linear Regression (Ridge)': (best_ridge, study_ridge.best_value),
        'Random Forest Regressor': (best_rf, study_rf.best_value)
    }
    
    return results

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
        f.write("# Auto-Generated by TinyML AutoML\n")
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
        f.write("# Auto-Generated by TinyML AutoML\n")
        
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
    theta = np.round(model.theta_, 4).tolist()
    var = np.round(model.var_, 4).tolist()
    prior = np.round(model.class_prior_, 4).tolist()
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML\n")
        f.write("model_type = 'gaussian_nb'\n")
        f.write(f"theta = {theta}\n")
        f.write(f"var = {var}\n")
        f.write(f"prior = {prior}\n")
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
            val = [[round(float(c), 4) for c in v[0]] for v in tree.value]
            trees_values.append(val)
        else:
            val = [round(float(v[0][0]), 4) for v in tree.value]
            trees_values.append(val)
            
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-Generated by TinyML AutoML\n")
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
        f.write("# Auto-Generated by TinyML AutoML\n")
        f.write("model_type = 'isolation_forest'\n")
        f.write(f"trees_features = {trees_features}\n")
        f.write(f"trees_thresholds = {trees_thresholds}\n")
        f.write(f"trees_left = {trees_left}\n")
        f.write(f"trees_right = {trees_right}\n")

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
    print("4. Anomaly Detect (Unsupervised - Find outliers/faults)")
    
    task_choice = input("Enter 1, 2, 3, or 4: ")
    
    try:
        df = pd.read_csv(csv_path)
        
        # ---------------------------------------------
        # TASK 1: CLASSIFICATION
        # ---------------------------------------------
        if task_choice == '1':
            target_column = input("Enter the target column name (Label): ")
            X, y, classes = preprocess_data(df, target_column, "classification")
            
            num_classes = len(classes)
            class_mode = "Binary" if num_classes == 2 else f"Multi-class ({num_classes} classes)"
            print(f"  -> Detected Problem Type: {class_mode} Classification")
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            print("\n[2/4] Optimizing Hyperparameters with Optuna...")
            results = tune_classification_models(X_train, X_test, y_train, y_test)
            
            print("\n[3/4] Optimization Results (Accuracy):")
            best_model_name = ""
            best_model_obj = None
            best_score = -1
            
            for name, (model, acc) in results.items():
                print(f"  -> {name}: {acc * 100:.2f}%")
                if acc > best_score:
                    best_score = acc
                    best_model_name = name
                    best_model_obj = model
            
            print(f"\n[4/4] Exporting the best model ({best_model_name})...")
            if "Decision Tree" in best_model_name:
                export_decision_tree(best_model_obj, is_classifier=True, classes=classes)
            elif "Logistic Regression" in best_model_name:
                export_linear_model(best_model_obj, is_classifier=True, classes=classes)
            elif "Random Forest" in best_model_name:
                export_random_forest(best_model_obj, is_classifier=True, classes=classes)
            elif "Gaussian Naive Bayes" in best_model_name:
                export_gnb(best_model_obj, classes=classes)
                
            print(f"🏆 Exported: {best_model_name}")

        # ---------------------------------------------
        # TASK 2: REGRESSION
        # ---------------------------------------------
        elif task_choice == '2':
            target_column = input("Enter the target column name (Label): ")
            X, y, _ = preprocess_data(df, target_column, "regression")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            print("\n[2/4] Optimizing Hyperparameters with Optuna...")
            results = tune_regression_models(X_train, X_test, y_train, y_test)
            
            print("\n[3/4] Optimization Results (Lower MSE is better):")
            best_model_name = ""
            best_model_obj = None
            best_score = float('inf')
            
            for name, (model, mse) in results.items():
                print(f"  -> {name} MSE: {mse:.4f}")
                if mse < best_score:
                    best_score = mse
                    best_model_name = name
                    best_model_obj = model
            
            print(f"\n[4/4] Exporting the best model ({best_model_name})...")
            if "Decision Tree" in best_model_name:
                export_decision_tree(best_model_obj, is_classifier=False)
            elif "Linear Regression" in best_model_name:
                export_linear_model(best_model_obj, is_classifier=False)
            elif "Random Forest" in best_model_name:
                export_random_forest(best_model_obj, is_classifier=False)
                
            print(f"🏆 Exported: {best_model_name}")

        # ---------------------------------------------
        # TASK 3: CLUSTERING
        # ---------------------------------------------
        elif task_choice == '3':
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

        # ---------------------------------------------
        # TASK 4: ANOMALY DETECTION
        # ---------------------------------------------
        elif task_choice == '4':
            X, _, _ = preprocess_data(df, task_type="anomaly")
            print("\n[2/4] Training model: Isolation Forest (Anomaly Detection)...")
            
            # Use a limited number of trees for TinyML memory constraints
            iso_forest = IsolationForest(n_estimators=5, random_state=42)
            iso_forest.fit(X)
            
            print("  -> Isolation Forest trained successfully.")
            print("\n[3/4] Exporting Isolation Forest Model...")
            export_isolation_forest(iso_forest)
            print("🏆 Exported: Isolation Forest Model")

        else:
            print("❌ Invalid selection. Please restart.")

        print("\n✅ Success! 'tinyml_model.py' is ready for your Pyboard.")

    except Exception as e:
        print(f"❌ Error during execution: {e}")