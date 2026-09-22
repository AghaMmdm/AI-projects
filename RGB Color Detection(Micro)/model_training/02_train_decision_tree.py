"""
Model Training and Decision Tree Exporter for Edge Deployment.

This script:
1. Loads RGB / 4-feature color dataset.
2. Trains a scikit-learn DecisionTreeClassifier with max-depth constraints for microcontrollers.
3. Evaluates model performance.
4. Exports model in two formats suitable for MicroPython:
   a) `model_data.py`: Compact Python lists for tree traversal (zero dependencies).
   b) `color_model.py`: Hardcoded nested if/else statements for instant C-like execution.
"""

import os
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def tree_to_python_code(tree, feature_names, class_names, function_name="predict_color"):
    """Converts a trained Decision Tree into static nested Python if/else code."""
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != -2 else "undefined!" for i in tree_.feature
    ]
    lines = [f"def {function_name}({', '.join(feature_names)}):"]

    def recurse(node, depth):
        indent = "    " * depth
        if tree_.feature[node] != -2:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            lines.append(f"{indent}if {name} <= {threshold:.5f}:")
            recurse(tree_.children_left[node], depth + 1)
            lines.append(f"{indent}else:")
            recurse(tree_.children_right[node], depth + 1)
        else:
            class_idx = np.argmax(tree_.value[node][0])
            class_name = str(class_names[class_idx]).replace('"', '\\"')
            lines.append(f'{indent}return "{class_name}"')

    recurse(0, 1)
    return "\n".join(lines)

def train_and_export():
    dataset_path = "../Data/color_dataset_4f.csv"
    if not os.path.exists(dataset_path):
        # Fallback to local Data if run from project root
        dataset_path = "Data/color_dataset_4f.csv"

    print(f"[*] Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)

    feature_cols = [c for c in df.columns if c != "label"]
    target_col = "label"

    X = df[feature_cols].values
    y = df[target_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train a compact decision tree suitable for microcontroller SRAM
    clf = DecisionTreeClassifier(max_depth=6, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[+] Test Accuracy: {acc * 100:.2f}%\n")
    print(classification_report(y_test, y_pred))

    # 1. Export as model_data.py (lists for index-based traversal)
    tree = clf.tree_
    unique_classes = list(clf.classes_)
    class_indices = [int(np.argmax(v)) for v in tree.value]

    model_data_content = f'''"""Exported Decision Tree Parameters for MicroPython."""
features = {tree.feature.tolist()}
thresholds = {[round(float(t), 5) for t in tree.threshold.tolist()]}
left = {tree.children_left.tolist()}
right = {tree.children_right.tolist()}
unique_classes = {unique_classes}
class_indices = {class_indices}
'''
    output_dir = "edge_mcu" if os.path.exists("edge_mcu") else "../edge_mcu"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "model_data.py"), "w", encoding="utf-8") as f:
        f.write(model_data_content)
    print(f"[+] Saved model arrays to {output_dir}/model_data.py")

    # 2. Export as nested Python if/else code
    if_else_code = tree_to_python_code(clf, ["norm_r", "norm_g", "norm_b", "norm_w"], clf.classes_)
    with open(os.path.join(output_dir, "color_model_rules.py"), "w", encoding="utf-8") as f:
        f.write(if_else_code + "\n")
    print(f"[+] Saved hardcoded rules to {output_dir}/color_model_rules.py")

if __name__ == "__main__":
    train_and_export()
