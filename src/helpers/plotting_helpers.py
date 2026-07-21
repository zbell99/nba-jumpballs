import pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.tree import plot_tree
from sklearn.metrics import roc_curve, auc


def feature_importance_table(model_result, feature_names, model_name, output_dir):
    """Extract feature importance from a model result dict. Load from pickle if needed."""
    importance_data = {'Feature': feature_names}
    
    # Try to get model from results dict, fall back to pickle file
    if 'Model' in model_result:
        model = model_result['Model']
    else:
        model_file = f"{output_dir}/{model_name.lower().replace(' ', '_')}_model.pkl"
        with open(model_file, "rb") as f:
            model = pickle.load(f)
    
    # Extract importance based on model type
    if hasattr(model, 'params'):
        # statsmodels logistic regression
        importance_data['Importance'] = np.abs(model.params[1:].values)
    elif hasattr(model, 'feature_importances_'):
        # sklearn models (CART, XGBoost)
        importance_data['Importance'] = model.feature_importances_
    
    importance_df = pd.DataFrame(importance_data)
    return importance_df


def visualize_cart_tree(model, feature_names, output_path):
    """Visualize the CART decision tree."""
    plt.figure(figsize=(20, 10))
    plot_tree(model, feature_names=feature_names, class_names=['Team 2 Wins', 'Team 1 Wins'], 
              filled=True, rounded=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"CART tree saved to {output_path}")


def plot_auc_curves(results, output_dir):
    """Plot ROC curves with AUC for XGBoost and CART models."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    
    for idx, model_name in enumerate(['Logistic Regression', 'XGBoost', 'CART']):
        if model_name not in results:
            continue
            
        model_result = results[model_name]
        y_test = model_result['Test Truth'].values
        test_proba = model_result['Test Probabilities']
        
        # Calculate ROC curve
        fpr, tpr, _ = roc_curve(y_test, test_proba)
        roc_auc = auc(fpr, tpr)
        
        # Plot
        ax = axes[idx]
        ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title(f'{model_name} ROC Curve')
        ax.legend(loc="lower right")
        ax.grid(alpha=0.3)
        
        print(f"\n{model_name} AUC: {roc_auc:.4f}")
    
    plt.tight_layout()
    auc_path = f"{output_dir}/auc_curves.png"
    plt.savefig(auc_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"AUC curves saved to {auc_path}")