import pandas as pd
import importlib.util
import math
import os

class TinyMLPredictor:
    """Smart Inference Engine for processing trained TinyML models.

    This engine automatically inspects the internal structural parameters 
    of an exported TinyML model file, identifies its underlying machine 
    learning algorithm, and executes the precise mathematically optimized 
    prediction workflow using zero external dependencies (pure Python).

    Attributes:
        model (module): The dynamically loaded Python module containing the model parameters.
        type (str): The architectural identifier string of the loaded model.
    """

    def __init__(self, model_module):
        """Initializes the TinyMLPredictor with a model module.

        Args:
            model_module (module): A dynamically imported module containing 
                the exported model parameters (e.g., weights, feature thresholds).
        """
        self.model = model_module
        self.type = self.model.model_type

    def predict(self, inputs):
        """Routes raw numerical features to the corresponding model prediction logic.

        Args:
            inputs (list of float/int): The raw feature vector extracted from 
                the target sensors or data row.

        Returns:
            str or float: The categorical class label (for classifiers/clustering/anomaly)
                or a continuous numerical value (for regressors).
        """
        if self.type == 'decision_tree_classifier': return self._predict_dt_class(inputs)
        elif self.type == 'decision_tree_regressor': return self._predict_dt_reg(inputs)
        elif self.type == 'logistic_regression_binary': return self._predict_lr_bin(inputs)
        elif self.type == 'logistic_regression_multiclass': return self._predict_lr_multi(inputs)
        elif self.type == 'linear_regression': return self._predict_lin_reg(inputs)
        elif self.type == 'random_forest_classifier': return self._predict_rf_class(inputs)
        elif self.type == 'random_forest_regressor': return self._predict_rf_reg(inputs)
        elif self.type == 'gaussian_nb': return self._predict_gnb(inputs)
        elif self.type == 'kmeans_clustering': return self._predict_kmeans(inputs)
        elif self.type == 'isolation_forest': return self._predict_anomaly(inputs)
        else: return "Error: Unknown model type"

    # ==========================================
    # Tree-Based Operations
    # ==========================================
    def _traverse_tree(self, inputs, features, thresholds, left, right):
        """Traverses a single compiled decision tree matrix down to a leaf node.

        Args:
            inputs (list): Feature values to evaluate.
            features (list): Feature index tested at each internal node.
            thresholds (list): Splitting boundaries for each feature node.
            left (list): Array mapping to the left child nodes.
            right (list): Array mapping to the right child nodes.

        Returns:
            int: The resulting leaf node index.
        """
        node = 0
        while left[node] != -1:
            if inputs[features[node]] <= thresholds[node]: node = left[node]
            else: node = right[node]
        return node

    def _predict_dt_class(self, inputs):
        """Predicts class labels using a single Decision Tree Classifier."""
        node = self._traverse_tree(inputs, self.model.features, self.model.thresholds, self.model.left, self.model.right)
        return self.model.unique_classes[self.model.class_indices[node]]

    def _predict_dt_reg(self, inputs):
        """Predicts continuous targets using a single Decision Tree Regressor."""
        node = self._traverse_tree(inputs, self.model.features, self.model.thresholds, self.model.left, self.model.right)
        return self.model.values[node]

    # ==========================================
    # Linear / Logistic Operations
    # ==========================================
    def _predict_lr_bin(self, inputs):
        """Computes the dot product for a binary Logistic Regression model."""
        score = self.model.intercept + sum(self.model.weights[j] * inputs[j] for j in range(len(inputs)))
        return self.model.classes[1 if score > 0 else 0]

    def _predict_lr_multi(self, inputs):
        """Evaluates weight matrices across all classes for Multiclass Logistic Regression."""
        best_score, best_class = -float('inf'), None
        for i in range(len(self.model.classes)):
            score = self.model.intercept[i] + sum(self.model.weights[i][j] * inputs[j] for j in range(len(inputs)))
            if score > best_score:
                best_score, best_class = score, self.model.classes[i]
        return best_class

    def _predict_lin_reg(self, inputs):
        """Computes plain multi-variable linear equation: y = wX + b."""
        return self.model.intercept + sum(self.model.weights[j] * inputs[j] for j in range(len(inputs)))

    # ==========================================
    # Ensemble Operations (Random Forest)
    # ==========================================
    def _predict_rf_class(self, inputs):
        """Aggregates democratic votes across multiple tree estimators for classification."""
        votes = {}
        for i in range(len(self.model.trees_features)):
            node = self._traverse_tree(inputs, self.model.trees_features[i], self.model.trees_thresholds[i], self.model.trees_left[i], self.model.trees_right[i])
            leaf_values = self.model.trees_values[i][node]
            pred_idx = leaf_values.index(max(leaf_values))
            votes[pred_idx] = votes.get(pred_idx, 0) + 1
        return self.model.classes[max(votes, key=votes.get)]

    def _predict_rf_reg(self, inputs):
        """Averages continuous values calculated by all tree estimators for regression."""
        total = 0.0
        for i in range(len(self.model.trees_features)):
            node = self._traverse_tree(inputs, self.model.trees_features[i], self.model.trees_thresholds[i], self.model.trees_left[i], self.model.trees_right[i])
            total += self.model.trees_values[i][node]
        return total / len(self.model.trees_features)

    # ==========================================
    # Math & Distance-Based Operations
    # ==========================================
    def _predict_gnb(self, inputs):
        """Applies Bayes theorem using Gaussian log-likelihood distributions."""
        max_log_prob, best_class = -float('inf'), None
        for i in range(len(self.model.classes)):
            log_prob = math.log(self.model.prior[i])
            for j in range(len(inputs)):
                var = max(self.model.var[i][j], 1e-9)
                log_prob -= 0.5 * math.log(2 * math.pi * var) + ((inputs[j] - self.model.theta[i][j]) ** 2) / (2 * var)
            if log_prob > max_log_prob:
                max_log_prob, best_class = log_prob, self.model.classes[i]
        return best_class

    def _predict_kmeans(self, inputs):
        """Calculates closest multidimensional Euclidean distance to cluster centroids."""
        best_cluster, min_dist = -1, float('inf')
        for i, centroid in enumerate(self.model.centroids):
            dist = sum((inputs[j] - centroid[j]) ** 2 for j in range(len(inputs)))
            if dist < min_dist:
                min_dist, best_cluster = dist, i
        return f"Cluster_{best_cluster}"

    def _predict_anomaly(self, inputs):
        """Evaluates average path isolation depth to determine out-of-bounds data."""
        total_depth, num_trees = 0, len(self.model.trees_features)
        for i in range(num_trees):
            node, depth = 0, 0
            while self.model.trees_left[i][node] != -1:
                if inputs[self.model.trees_features[i][node]] <= self.model.trees_thresholds[i][node]: node = self.model.trees_left[i][node]
                else: node = self.model.trees_right[i][node]
                depth += 1
            total_depth += depth
        return "ANOMALY" if (total_depth / num_trees) <= 3.0 else "Normal"


# ==========================================
# Core Library API 
# ==========================================
def run_batch_inference(csv_path, model_path="tinyml_model.py", output_path="predicted_results.csv"):
    """Executes row-by-row batch predictions on a raw CSV file via a compiled TinyML model.

    This function reads unlabelled raw datasets, dynamically injects the model parameters 
    from the target path into a standalone runtime instance, executes prediction loops, 
    and appends a clean 'AutoML_Prediction' results column back onto disk.

    Args:
        csv_path (str): File system path pointing to the unlabelled target data CSV file.
        model_path (str, optional): File system path targeting the generated TinyML 
            compiled python parameter file. Defaults to "tinyml_model.py".
        output_path (str, optional): Target destination file path where completed 
            prediction rows will be mapped and saved. Defaults to "predicted_results.csv".

    Returns:
        dict: Operational telemetry metadata reporting pipeline status.
            Examples:
                {"status": "success", "output_file": "...", "processed_rows": 140}
                {"status": "error", "message": "..."}
    """
    if not os.path.exists(csv_path):
        return {"status": "error", "message": f"CSV file not found: {csv_path}"}
    if not os.path.exists(model_path):
        return {"status": "error", "message": f"Model file not found: {model_path}"}

    try:
        print(f"[*] Loading model from: {model_path}")
        spec = importlib.util.spec_from_file_location("custom_model", model_path)
        model_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model_module)

        engine = TinyMLPredictor(model_module)
        print(f"[*] Engine Ready. Active Model Type: {engine.type}")

        print(f"[*] Reading data from: {csv_path}")
        df = pd.read_csv(csv_path)
        
        print("[*] Processing rows...")
        results = []
        for index, row in df.iterrows():
            prediction = engine.predict(row.tolist())
            results.append(prediction)
            print(f"  -> Row {index + 1}: {prediction}")

        df['AutoML_Prediction'] = results
        df.to_csv(output_path, index=False)
        print(f"[*] Success! Results successfully saved to: {output_path}")
        
        return {"status": "success", "output_file": output_path, "processed_rows": len(df)}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TinyML Batch Inference Engine")
    parser.add_argument("--csv", required=True, help="Path to the test data CSV file")
    parser.add_argument("--model", default="tinyml_model.py", help="Path to the trained model file")
    parser.add_argument("--output", default="predicted_results.csv", help="Path to save the output CSV")
    
    args = parser.parse_args()
    run_batch_inference(args.csv, args.model, args.output)