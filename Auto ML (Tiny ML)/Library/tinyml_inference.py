import math

class TinyMLPredictor:
    """Ultra-Lightweight Inference Engine for Microcontrollers"""
    
    def __init__(self, model_module):
        self.model = model_module
        self.type = getattr(self.model, 'model_type', 'unknown')

    @staticmethod
    def print_help():
        """Prints the official TinyML Inference documentation safely in MicroPython."""
        print("\n" + "="*50)
        print("  TINYML INFERENCE ENGINE - OFFICIAL DOCUMENTATION  ")
        print("="*50)
        print("\n[Overview]")
        print("This is an ultra-lightweight, zero-dependency inference")
        print("engine designed specifically for MicroPython devices.")
        print("It dynamically reads exported model parameters and")
        print("executes pure mathematical predictions without Pandas.")
        
        print("\n[Supported Models]")
        print("- Decision Tree (Classifier / Regressor)")
        print("- Random Forest (Classifier / Regressor)")
        print("- Logistic Regression (Binary / Multi-class)")
        print("- Linear Regression (Ridge)")
        print("- Gaussian Naive Bayes")
        print("- K-Means Clustering")
        print("- Isolation Forest (Anomaly Detection)")
        
        print("\n[Usage Example]")
        print("import tinyml_model")
        print("import tinyml_inference")
        print("engine = tinyml_inference.TinyMLPredictor(tinyml_model)")
        print("\n# Predict using a raw sensor dictionary:")
        print("data = {'Sensor_A': 120, 'Sensor_B': 0.5}")
        print("result = engine.predict(data)")
        print("print(result)")
        
        print("\n[Available Methods]")
        print("1. predict(raw_inputs)    : Runs the inference process.")
        print("2. transform_input(data)  : Handles missing values and One-Hot Encoding.")
        print("="*50 + "\n")

    def transform_input(self, raw_input):
        # [BACKWARD COMPATIBILITY]
        if not hasattr(self.model, 'pipeline_features'):
            if type(raw_input) == dict:
                return [float(v) for v in raw_input.values() if v is not None]
            return raw_input

        # [NEW PREPROCESSING LOGIC]
        if type(raw_input) == list:
            cleaned_list = []
            for idx, val in enumerate(raw_input):
                if val is None or val == "":
                    feature_keys = list(self.model.pipeline_impute.keys())
                    val = self.model.pipeline_impute[feature_keys[idx]]
                cleaned_list.append(val)
            return cleaned_list

        imputed_data = {}
        pipeline_impute = getattr(self.model, 'pipeline_impute', {})
        for feature_name, fallback_value in pipeline_impute.items():
            user_val = raw_input.get(feature_name, None)
            if user_val is None or user_val == "":
                imputed_data[feature_name] = fallback_value
            else:
                imputed_data[feature_name] = user_val

        final_vector = []
        pipeline_features = getattr(self.model, 'pipeline_features', [])
        for feature in pipeline_features:
            if "_" in feature:
                parts = feature.split("_")
                base_col = parts[0]
                category = feature[len(base_col)+1:] 
                
                if base_col in imputed_data:
                    final_vector.append(1 if str(imputed_data[base_col]) == category else 0)
                else:
                    final_vector.append(0)
            else:
                val = imputed_data.get(feature, 0.0)
                try:
                    final_vector.append(float(val))
                except ValueError:
                    final_vector.append(0.0)

        return final_vector

    def predict(self, raw_inputs):
        processed_inputs = self.transform_input(raw_inputs)
        
        if self.type == 'decision_tree_classifier': return self._predict_dt_class(processed_inputs)
        elif self.type == 'decision_tree_regressor': return self._predict_dt_reg(processed_inputs)
        elif self.type == 'logistic_regression_binary': return self._predict_lr_bin(processed_inputs)
        elif self.type == 'logistic_regression_multiclass': return self._predict_lr_multi(processed_inputs)
        elif self.type == 'linear_regression': return self._predict_lin_reg(processed_inputs)
        elif self.type == 'random_forest_classifier': return self._predict_rf_class(processed_inputs)
        elif self.type == 'random_forest_regressor': return self._predict_rf_reg(processed_inputs)
        elif self.type == 'gaussian_nb': return self._predict_gnb(processed_inputs)
        elif self.type == 'kmeans_clustering': return self._predict_kmeans(processed_inputs)
        elif self.type == 'isolation_forest': return self._predict_anomaly(processed_inputs)
        else: return "Error: Unknown model type"

    # ==========================================
    # Algorithmic Backends (Pure Math)
    # ==========================================
    def _traverse_tree(self, inputs, features, thresholds, left, right):
        node = 0
        while left[node] != -1:
            if inputs[features[node]] <= thresholds[node]: node = left[node]
            else: node = right[node]
        return node

    def _predict_dt_class(self, inputs):
        node = self._traverse_tree(inputs, self.model.features, self.model.thresholds, self.model.left, self.model.right)
        return self.model.unique_classes[self.model.class_indices[node]]

    def _predict_dt_reg(self, inputs):
        node = self._traverse_tree(inputs, self.model.features, self.model.thresholds, self.model.left, self.model.right)
        return self.model.values[node]

    def _predict_lr_bin(self, inputs):
        score = self.model.intercept
        for j in range(len(inputs)): score += self.model.weights[j] * inputs[j]
        return self.model.classes[1 if score > 0 else 0]

    def _predict_lr_multi(self, inputs):
        best_score, best_class = -float('inf'), None
        for i in range(len(self.model.classes)):
            score = self.model.intercept[i]
            for j in range(len(inputs)): score += self.model.weights[i][j] * inputs[j]
            if score > best_score: best_score, best_class = score, self.model.classes[i]
        return best_class

    def _predict_lin_reg(self, inputs):
        score = self.model.intercept
        for j in range(len(inputs)): score += self.model.weights[j] * inputs[j]
        return score

    def _predict_rf_class(self, inputs):
        votes = {}
        for i in range(len(self.model.trees_features)):
            node = self._traverse_tree(inputs, self.model.trees_features[i], self.model.trees_thresholds[i], self.model.trees_left[i], self.model.trees_right[i])
            leaf_values = self.model.trees_values[i][node]
            
            max_val = -float('inf')
            max_idx = 0
            for v_idx, v_val in enumerate(leaf_values):
                if v_val > max_val:
                    max_val = v_val
                    max_idx = v_idx
            
            votes[max_idx] = votes.get(max_idx, 0) + 1
            
        best_vote_idx = -1
        max_votes = -1
        for k, v in votes.items():
            if v > max_votes:
                max_votes = v
                best_vote_idx = k
                
        return self.model.classes[best_vote_idx]

    def _predict_rf_reg(self, inputs):
        total = 0.0
        for i in range(len(self.model.trees_features)):
            node = self._traverse_tree(inputs, self.model.trees_features[i], self.model.trees_thresholds[i], self.model.trees_left[i], self.model.trees_right[i])
            total += self.model.trees_values[i][node]
        return total / len(self.model.trees_features)

    def _predict_gnb(self, inputs):
        max_log_prob, best_class = -float('inf'), None
        for i in range(len(self.model.classes)):
            log_prob = math.log(self.model.prior[i])
            for j in range(len(inputs)):
                var = self.model.var[i][j]
                if var < 1e-9: var = 1e-9
                log_prob -= 0.5 * math.log(2 * math.pi * var) + ((inputs[j] - self.model.theta[i][j]) ** 2) / (2 * var)
            if log_prob > max_log_prob: max_log_prob, best_class = log_prob, self.model.classes[i]
        return best_class

    def _predict_kmeans(self, inputs):
        best_cluster, min_dist = -1, float('inf')
        for i, centroid in enumerate(self.model.centroids):
            dist = 0
            for j in range(len(inputs)): dist += (inputs[j] - centroid[j]) ** 2
            if dist < min_dist: min_dist, best_cluster = dist, i
        return "Cluster_" + str(best_cluster)

    def _predict_anomaly(self, inputs):
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
# Core Batch API (MicroPython Compatible)
# ==========================================
def run_batch_inference(csv_path, model_name="tinyml_model", output_path="predicted_results.csv"):
    try:
        module_name = model_name.replace(".py", "")
        model_module = __import__(module_name)
        
        engine = TinyMLPredictor(model_module)
        print("[*] Engine Ready. Type:", engine.type)

        print("[*] Processing rows...")
        results = []
        
        with open(csv_path, 'r') as f:
            header_line = f.readline().strip()
            headers = header_line.split(',')
            
            row_index = 1
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                values = line.split(',')
                row_dict = {}
                for i in range(len(headers)):
                    val_str = values[i].strip()
                    if val_str == "":
                        row_dict[headers[i]] = None
                    else:
                        try:
                            row_dict[headers[i]] = float(val_str)
                        except ValueError:
                            row_dict[headers[i]] = val_str
                
                prediction = engine.predict(row_dict)
                results.append(str(prediction))
                print("  -> Row " + str(row_index) + ": " + str(prediction))
                row_index += 1

        with open(csv_path, 'r') as f_in, open(output_path, 'w') as f_out:
            header = f_in.readline().strip()
            f_out.write(header + ",AutoML_Prediction\n")
            
            for i, line in enumerate(f_in):
                line = line.strip()
                if line:
                    f_out.write(line + "," + results[i] + "\n")
                    
        print("[*] Success! Saved to:", output_path)
        return {"status": "success", "processed": len(results)}

    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--csv" and len(sys.argv) > 2:
            csv_file = sys.argv[2]
            run_batch_inference(csv_file, "tinyml_model")
        else:
            print("Usage: python tinyml_inference.py --csv <data.csv>")
    else:
        print("Waiting for imports...")