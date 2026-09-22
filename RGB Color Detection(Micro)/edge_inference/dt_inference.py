"""
MicroPython Lightweight Decision Tree Inference Engine.

Alternative zero-dependency inference implementation for memory-constrained MCUs.
Requires only standard Python math/lists, without external libraries.
"""

# Import model weights generated from training (exported as model_data.py)
try:
    import model_data
except ImportError:
    model_data = None


def predict_decision_tree(r, g, b, model=None):
    """
    Traverses an exported Decision Tree using left/right branch indices.
    
    Args:
        r (float): Red channel intensity
        g (float): Green channel intensity
        b (float): Blue channel intensity
        model: Module or dictionary containing features, thresholds, left, right, unique_classes, class_indices
        
    Returns:
        str: Predicted color class name
    """
    m = model if model is not None else model_data
    if m is None:
        raise ValueError("No model structure provided. Please import model_data.")

    features = m.features
    thresholds = m.thresholds
    left = m.left
    right = m.right
    unique_classes = m.unique_classes
    class_indices = m.class_indices

    node = 0
    inputs = [r, g, b]

    # -1 indicates a leaf node
    while left[node] != -1:
        feat_idx = features[node]
        thresh = thresholds[node]

        if inputs[feat_idx] <= thresh:
            node = left[node]
        else:
            node = right[node]

    predicted_class_idx = class_indices[node]
    return unique_classes[predicted_class_idx]
