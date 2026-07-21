import json
import pickle
import os
from datetime import datetime

import pandas as pd
import numpy as np

import statsmodels.api as sm
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

from src.helpers.plotting_helpers import feature_importance_table, plot_auc_curves, visualize_cart_tree


DATA_PATH = "data/filtered-jumpballs.csv"

def clean_data(df):
    #1. strip rows with missing values in the 'athlete_id_1' and 'athlete_id_2' and 'athlete_id_3' columns
    df = df.dropna(subset=['team_1_jumpball_win', 'athlete_draft_height_1', 'athlete_draft_height_2', 'athlete_draft_weight_1', 'athlete_draft_weight_2', 'athlete_draft_weight_3'])

    #2. convert boolean target to numeric (True -> 1, False -> 0)
    df['team_1_jumpball_win'] = df['team_1_jumpball_win'].astype(int)
    print(df['team_1_jumpball_win'].value_counts())

    #3. new columns "height_diff" and "weight_diff" 
    df['height_diff'] = df['athlete_draft_height_1'] - df['athlete_draft_height_2']
    df['weight_diff'] = df['athlete_draft_weight_1'] - df['athlete_draft_weight_2']

    #4. simplify the dataframe to only include the following columns: 'team_1_jumpball_win', 'height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff'
    df = df[['season', 'home_team_id', 'away_team_id', 'team_1_jumpball_win', 'height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff']]
    
    return df


def class_balancer(df, target_column, random_state=170):
    """
    For this specific use case, we can easily balance the classes since every data point is two-sided. Thus, we can multiply the point by -1 at random so that our classes are balanced.
    """
    np.random.seed(random_state)
    df_balanced = df.copy()
    mask = np.random.rand(len(df_balanced)) < 0.5
    df_balanced.loc[mask, 'height_diff'] *= -1
    df_balanced.loc[mask, 'weight_diff'] *= -1
    df_balanced.loc[mask, 'team_1_score_diff'] *= -1
    df_balanced.loc[mask, target_column] = 1 - df_balanced.loc[mask, target_column]

    return df_balanced

def split_specific_team_season(df, season, team_id):
    #1. filter the dataframe to only include rows from the specified season and team_id
    df = df[(df['season'] == season) & ((df['home_team_id'] == team_id) | (df['away_team_id'] == team_id))]

    #2. save the dataframe to a csv file
    df.to_csv(f"data/model/wp/team_{team_id}_season_{season}.csv", index=False)

    return df

def split_data(df, split=[0.7, 0.15, 0.15], random_state=170):
    #1. split the dataframe into train, validation, and test sets (70%, 15%, 15%)
    train_frac, val_frac, test_frac = split
    train_df = df.sample(frac=train_frac, random_state=random_state)
    val_test_df = df.drop(train_df.index)
    val_df = val_test_df.sample(frac=val_frac / (val_frac + test_frac), random_state=random_state)
    test_df = val_test_df.drop(val_df.index)

    #2. save the dataframes to csv files
    train_df.to_csv("data/model/wp/train.csv", index=False)
    val_df.to_csv("data/model/wp/val.csv", index=False)
    test_df.to_csv("data/model/wp/test.csv", index=False)

    return train_df, val_df, test_df


def run_modeling_suite(regressors, target, train_df, val_df, test_df):
    X_train = train_df[regressors]
    y_train = train_df[target]

    X_val = val_df[regressors]
    y_val = val_df[target]

    X_test = test_df[regressors]
    y_test = test_df[target]

    datasets = {
        "train": (X_train, y_train),
        "validation": (X_val, y_val),
        "test": (X_test, y_test),
    }
    results = {}
    results['Features'] = regressors
    results['Target'] = target
    results['Logistic Regression'] = build_logistic_regression_statsmodels(datasets)
    results['XGBoost'] = build_model_sklearn(xgb.XGBClassifier(max_depth=3, random_state=170), datasets)
    results['CART'] = build_model_sklearn(DecisionTreeClassifier(random_state=170, max_depth=3, min_samples_split=100, min_samples_leaf=50), datasets)
    
    export_results(results, train_df)


def build_model_sklearn(model, datasets):
    X_train, y_train = datasets['train']
    X_val, y_val = datasets['validation']
    X_test, y_test = datasets['test']

    model.fit(X=X_train, y=y_train)

    val_preds = model.predict(X_val)
    test_preds = model.predict(X_test)
    
    val_proba = model.predict_proba(X_val)[:, 1]
    test_proba = model.predict_proba(X_test)[:, 1]

    return {
        "Model": model,
        "Hyperparameters": model.get_params(),
        "Validation Accuracy": accuracy_score(y_val, val_preds),
        "Test Accuracy": accuracy_score(y_test, test_preds),
        "Validation Classification Report": classification_report(y_val, val_preds, output_dict=True),
        "Test Classification Report": classification_report(y_test, test_preds, output_dict=True),
        "Validation Predictions": val_preds,
        "Test Predictions": test_preds,
        "Validation Probabilities": val_proba,
        "Test Probabilities": test_proba,
        "Validation Truth": y_val,
        "Test Truth": y_test,
    }


def build_logistic_regression_statsmodels(datasets):
    """Build logistic regression using statsmodels for automatic p-values and statistics."""
    X_train, y_train = datasets['train']
    X_val, y_val = datasets['validation']
    X_test, y_test = datasets['test']
    
    # Add constant (intercept) for statsmodels
    X_train_sm = sm.add_constant(X_train)
    X_val_sm = sm.add_constant(X_val)
    X_test_sm = sm.add_constant(X_test)
    
    # Fit logistic regression
    logit_model = sm.Logit(y_train, X_train_sm)
    results = logit_model.fit(disp=0)
    
    # Get predictions
    val_preds_proba = results.predict(X_val_sm)
    test_preds_proba = results.predict(X_test_sm)
    val_preds = (val_preds_proba > 0.5).astype(int)
    test_preds = (test_preds_proba > 0.5).astype(int)
    
    return {
        "Model": results,
        "Hyperparameters": {},
        "Validation Accuracy": accuracy_score(y_val, val_preds),
        "Test Accuracy": accuracy_score(y_test, test_preds),
        "Validation Classification Report": classification_report(y_val, val_preds, output_dict=True),
        "Test Classification Report": classification_report(y_test, test_preds, output_dict=True),
        "Validation Predictions": val_preds,
        "Test Predictions": test_preds,
        "Validation Probabilities": val_preds_proba,
        "Test Probabilities": test_preds_proba,
        "Validation Truth": y_val,
        "Test Truth": y_test,
    }



def export_results(results, train_df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"models/wp/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare metrics dict (exclude model objects for JSON)
    metrics = {}
    metrics['Features'] = results.get('Features')
    metrics['Target'] = results.get('Target')
    
    for model_name in ['Logistic Regression', 'XGBoost', 'CART']:
        if model_name in results:
            model_results = results[model_name]
            metrics[model_name] = {
                k: v for k, v in model_results.items() if k != "Model" 
                and k not in ["Validation Predictions", "Test Predictions", "Validation Probabilities", "Test Probabilities", "Validation Truth", "Test Truth"]
            }
            # Save model object separately
            model = model_results["Model"]
            model_file = f"{output_dir}/{model_name.lower().replace(' ', '_')}_model.pkl"
            with open(model_file, "wb") as f:
                pickle.dump(model, f)
    
    # Generate and save logistic regression coefficient table and R^2
    if 'Logistic Regression' in results:
        lr_model = results['Logistic Regression']['Model']
        
        coef_df = lr_model.summary2().tables[1].reset_index().rename(columns={'index': 'Feature', 'Coef.': 'Coefficient', 'Std.Err.': 'Std Error', 'z': 'Z-Score', 'P>|z|': 'P-Value'})
        coef_df['Significant'] = ['***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '' for p in coef_df['P-Value']]
        coef_csv = f"{output_dir}/logistic_regression_coefficients.csv"
        coef_df.to_csv(coef_csv, index=False)
        print("\nLogistic Regression Coefficients:")
        print(coef_df.to_string(index=False))
    
    # Generate and save feature importance table
    importance_df = feature_importance_table(results, results['Features'])
    importance_csv = f"{output_dir}/feature_importance.csv"
    importance_df.to_csv(importance_csv, index=False)
    print("\n\nFeature Importance:")
    print(importance_df.to_string(index=False))
    
    # Plot AUC curves for XGBoost and CART
    print("\n\nGenerating AUC curves...")
    plot_auc_curves(results, output_dir)
    
    # Visualize and save CART tree
    if 'CART' in results:
        cart_model = results['CART']['Model']
        tree_path = f"{output_dir}/cart_tree.png"
        visualize_cart_tree(cart_model, results['Features'], tree_path)
    
    # Save metrics as JSON (handle NaN values)
    metrics_file = f"{output_dir}/results.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=4, default=lambda x: None if isinstance(x, float) and np.isnan(x) else x)


def main():
    # Set random seed for reproducibility
    RANDOM_STATE = 170
    np.random.seed(RANDOM_STATE)
    
    df = pd.read_csv(DATA_PATH)
    df = clean_data(df)

    nets_test_df = split_specific_team_season(df, season=2025, team_id=17) # Brooklyn Nets team_id
    filtered_df = df.drop(nets_test_df.index) # Remove Nets test data from the main dataframe
    train_df, val_df, test_df = split_data(filtered_df, split=[0.7, 0.15, 0.15], random_state=RANDOM_STATE)
    
    features = ['height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff']
    target = 'team_1_jumpball_win'
    train_df = class_balancer(train_df, target_column=target, random_state=RANDOM_STATE)
    run_modeling_suite(regressors=features, target=target, train_df=train_df, val_df=val_df, test_df=test_df)


if __name__ == "__main__":
    main()