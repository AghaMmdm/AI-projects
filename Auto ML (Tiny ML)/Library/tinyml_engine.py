import math

class TinyMLPredictor:
    def __init__(self, model_module):
        """
        مدل خروجی گرفته شده را دریافت کرده و نوع آن را تشخیص می‌دهد.
        """
        self.model = model_module
        self.type = self.model.model_type

    def predict(self, inputs):
        """
        دریافت دیتای جدید سنسورها و ارجاع به الگوریتم مناسب
        """
        if self.type == 'decision_tree_classifier':
            return self._predict_dt_class(inputs)
        elif self.type == 'decision_tree_regressor':
            return self._predict_dt_reg(inputs)
        elif self.type == 'logistic_regression_binary':
            return self._predict_lr_bin(inputs)
        elif self.type == 'logistic_regression_multiclass':
            return self._predict_lr_multi(inputs)
        elif self.type == 'linear_regression':
            return self._predict_lin_reg(inputs)
        elif self.type == 'random_forest_classifier':
            return self._predict_rf_class(inputs)
        elif self.type == 'random_forest_regressor':
            return self._predict_rf_reg(inputs)
        elif self.type == 'gaussian_nb':
            return self._predict_gnb(inputs)
        elif self.type == 'kmeans_clustering':
            return self._predict_kmeans(inputs)
        elif self.type == 'isolation_forest':
            return self._predict_anomaly(inputs)
        else:
            return "Error: Unknown model type"

    # ==========================================
    # توابع پردازش الگوهای درختی (Tree-Based)
    # ==========================================
    def _traverse_tree(self, inputs, features, thresholds, left, right):
        node = 0
        while left[node] != -1:
            if inputs[features[node]] <= thresholds[node]:
                node = left[node]
            else:
                node = right[node]
        return node

    def _predict_dt_class(self, inputs):
        node = self._traverse_tree(inputs, self.model.features, self.model.thresholds, self.model.left, self.model.right)
        idx = self.model.class_indices[node]
        return self.model.unique_classes[idx]

    def _predict_dt_reg(self, inputs):
        node = self._traverse_tree(inputs, self.model.features, self.model.thresholds, self.model.left, self.model.right)
        return self.model.values[node]

    # ==========================================
    # توابع پردازش الگوهای خطی (Linear/Logistic)
    # ==========================================
    def _predict_lr_bin(self, inputs):
        score = self.model.intercept
        for j in range(len(inputs)):
            score += self.model.weights[j] * inputs[j]
        idx = 1 if score > 0 else 0
        return self.model.classes[idx]

    def _predict_lr_multi(self, inputs):
        best_score = -float('inf')
        best_class = None
        for i in range(len(self.model.classes)):
            score = self.model.intercept[i]
            for j in range(len(inputs)):
                score += self.model.weights[i][j] * inputs[j]
            if score > best_score:
                best_score = score
                best_class = self.model.classes[i]
        return best_class

    def _predict_lin_reg(self, inputs):
        score = self.model.intercept
        for j in range(len(inputs)):
            score += self.model.weights[j] * inputs[j]
        return score

    # ==========================================
    # توابع پردازش جنگل تصادفی (Ensemble)
    # ==========================================
    def _predict_rf_class(self, inputs):
        votes = {}
        for i in range(len(self.model.trees_features)):
            node = self._traverse_tree(inputs, self.model.trees_features[i], self.model.trees_thresholds[i], self.model.trees_left[i], self.model.trees_right[i])
            # استخراج ایندکس کلاسی که بیشترین رای را در این برگ داشته است
            leaf_values = self.model.trees_values[i][node]
            pred_idx = leaf_values.index(max(leaf_values))
            votes[pred_idx] = votes.get(pred_idx, 0) + 1
            
        best_idx = max(votes, key=votes.get)
        return self.model.classes[best_idx]

    def _predict_rf_reg(self, inputs):
        total = 0.0
        for i in range(len(self.model.trees_features)):
            node = self._traverse_tree(inputs, self.model.trees_features[i], self.model.trees_thresholds[i], self.model.trees_left[i], self.model.trees_right[i])
            total += self.model.trees_values[i][node]
        return total / len(self.model.trees_features)

    # ==========================================
    # توابع احتمالاتی و فاصله‌ای (Math-Based)
    # ==========================================
    def _predict_gnb(self, inputs):
        best_class = None
        max_log_prob = -float('inf')
        for i in range(len(self.model.classes)):
            log_prob = math.log(self.model.prior[i])
            for j in range(len(inputs)):
                var = max(self.model.var[i][j], 1e-9) # جلوگیری از تقسیم بر صفر
                mean = self.model.theta[i][j]
                log_prob -= 0.5 * math.log(2 * math.pi * var)
                log_prob -= ((inputs[j] - mean) ** 2) / (2 * var)
            if log_prob > max_log_prob:
                max_log_prob = log_prob
                best_class = self.model.classes[i]
        return best_class

    def _predict_kmeans(self, inputs):
        best_cluster = -1
        min_dist = float('inf')
        for i, centroid in enumerate(self.model.centroids):
            dist = sum((inputs[j] - centroid[j]) ** 2 for j in range(len(inputs)))
            if dist < min_dist:
                min_dist = dist
                best_cluster = i
        return f"Cluster_{best_cluster}"

    def _predict_anomaly(self, inputs):
        total_depth = 0
        num_trees = len(self.model.trees_features)
        for i in range(num_trees):
            node = 0
            depth = 0
            while self.model.trees_left[i][node] != -1:
                if inputs[self.model.trees_features[i][node]] <= self.model.trees_thresholds[i][node]:
                    node = self.model.trees_left[i][node]
                else:
                    node = self.model.trees_right[i][node]
                depth += 1
            total_depth += depth
            
        avg_depth = total_depth / num_trees
        # در Isolation Forest اگر مسیر رسیدن به برگ خیلی کوتاه باشد، یعنی داده غیرعادی است
        # اینجا عمق کمتر از 3 به عنوان ناهنجاری در نظر گرفته شده است (قابل تنظیم)
        if avg_depth <= 3.0:
            return "ANOMALY DETECTED!"
        else:
            return "Normal"