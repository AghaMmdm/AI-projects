import model_data

def predict_audio_class(mfcc_features):
    """
    Runs the MFCC features through the exported Random Forest arrays.
    Returns the index of the predicted class: 
    0: 'on', 1: 'off', 2: 'stop', 3: 'unknown'
    """
    # Array to hold votes for each of the 4 classes
    class_votes = [0, 0, 0, 0]
    
    for tree in model_data.TREES:
        node = 0 # Start at the root node (index 0) of the tree
        
        # Traverse the tree: scikit-learn uses -2 in 'feature' array to mark leaf nodes
        while tree['feature'][node] != -2:
            feat_idx = tree['feature'][node]
            
            # Compare feature value with the threshold
            if mfcc_features[feat_idx] <= tree['threshold'][node]:
                node = tree['left'][node]  # Go to left child
            else:
                node = tree['right'][node] # Go to right child
                
        # Leaf node reached: cast a vote for the final class
        predicted_class = tree['classes'][node]
        class_votes[predicted_class] += 1
        
    # Find the class with the maximum votes (Majority Voting)
    best_class = 0
    max_votes = -1
    for i in range(len(class_votes)):
        if class_votes[i] > max_votes:
            max_votes = class_votes[i]
            best_class = i
            
    return best_class

# --- Example Usage on Board ---
# classes = ['on', 'off', 'stop', 'unknown']
# features = [1.2, -0.5, 3.4, ...] # These are the 13 MFCC features extracted from mic
# result_idx = predict_audio_class(features)
# print("Predicted Word:", classes[result_idx])