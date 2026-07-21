import json
import pickle
import os
from datetime import datetime
from itertools import combinations

import pandas as pd
import numpy as np

import statsmodels.api as sm
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

from src.helpers.plotting_helpers import feature_importance_table, plot_auc_curves, visualize_cart_tree


DATA_PATH = "data/filtered-jumpballs.csv"

# Grid search configuration
FEATURE_POOL = ['height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff', 'height_weight_interaction', 'height_time_interaction', 'weight_time_interaction']
MIN_FEATURES = 2
MAX_FEATURES = 4

HYPERPARAMETERS = {
    'XGBoost': [
        {'max_depth': 3, 'learning_rate': 0.1, 'n_estimators': 100},
        {'max_depth': 3, 'learning_rate': 0.05, 'n_estimators': 100},
        {'max_depth': 5, 'learning_rate': 0.1, 'n_estimators': 100},
        {'max_depth': 5, 'learning_rate': 0.05, 'n_estimators': 100},
    ],
    'CART': [
        {'max_depth': 3, 'min_samples_split': 100, 'min_samples_leaf': 50},
        {'max_depth': 5, 'min_samples_split': 50, 'min_samples_leaf': 20},
        {'max_depth': 7, 'min_samples_split': 30, 'min_samples_leaf': 10},
    ],
}

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
    df = df[['season', 'home_team_id', 'away_team_id', 'team_1_jumpball_win', 'height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff', 'wp_leverage', 'jumpball_type']]
    
    return df


def standardize_features(df, feature_columns):
    """Standardize the specified feature columns in the dataframe."""
    for col in feature_columns:
        mean = df[col].mean()
        std = df[col].std()
        df[f"{col}_std"] = (df[col] - mean) / std
    return df


def enhance_data(df):
    #1. interaction terms
    df['height_weight_interaction'] = df['height_diff'] * df['weight_diff']
    df['height_time_interaction'] = df['height_diff'] * df['time_elapsed']
    df['weight_time_interaction'] = df['weight_diff'] * df['time_elapsed']

    df['height_weight_interaction_std'] = df['height_diff_std'] * df['weight_diff_std']
    df['height_time_interaction_std'] = df['height_diff_std'] * df['time_elapsed']
    df['weight_time_interaction_std'] = df['weight_diff_std'] * df['time_elapsed']

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


def run_modeling_suite(regressors, target, train_df, val_df, test_df, xgb_hyperparams=None, cart_hyperparams=None):
    if xgb_hyperparams is None:
        xgb_hyperparams = {'max_depth': 3, 'random_state': 170}
    if cart_hyperparams is None:
        cart_hyperparams = {'random_state': 170, 'max_depth': 3, 'min_samples_split': 100, 'min_samples_leaf': 50}
    
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
    results['XGBoost'] = build_model_sklearn(xgb.XGBClassifier(**xgb_hyperparams), datasets)
    results['CART'] = build_model_sklearn(DecisionTreeClassifier(**cart_hyperparams), datasets)
    
    return results


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



def export_results(results, output_dir, generate_visualizations=True):
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare metrics dict (exclude model objects for JSON)
    metrics = {}
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
    
    # Generate and save logistic regression coefficient table
    if 'Logistic Regression' in results:
        lr_model = results['Logistic Regression']['Model']
        
        coef_df = lr_model.summary2().tables[1].reset_index().rename(columns={'index': 'Feature', 'Coef.': 'Coefficient', 'Std.Err.': 'Std Error', 'z': 'Z-Score', 'P>|z|': 'P-Value'})
        coef_df['Significant'] = ['***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '' for p in coef_df['P-Value']]
        coef_csv = f"{output_dir}/logistic_regression_coefficients.csv"
        coef_df.to_csv(coef_csv, index=False)
        print("\nLogistic Regression Coefficients:")
        print(coef_df.to_string(index=False))
    
    # Generate feature importance for each model
    for model_name in ['Logistic Regression', 'XGBoost', 'CART']:
        if model_name in results:
            features = results[model_name].get('Features')
            if features is not None:
                importance_df = feature_importance_table(results[model_name], features, model_name, output_dir)
                importance_csv = f"{output_dir}/{model_name.lower().replace(' ', '_')}_feature_importance.csv"
                importance_df.to_csv(importance_csv, index=False)
                print(f"\n{model_name} Feature Importance:")
                print(importance_df.to_string(index=False))
    
    if generate_visualizations:
        # Plot AUC curves
        print("\n\nGenerating AUC curves...")
        plot_auc_curves(results, output_dir)
        
        # Visualize and save CART tree
        if 'CART' in results:
            cart_model = results['CART']['Model']
            cart_features = results['CART'].get('Features')
            if cart_features is not None:
                tree_path = f"{output_dir}/cart_tree.png"
                visualize_cart_tree(cart_model, cart_features, tree_path)
    
    # Save metrics as JSON (handle NaN values)
    metrics_file = f"{output_dir}/results.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=4, default=lambda x: None if isinstance(x, float) and np.isnan(x) else x)
    
    return output_dir


def generate_feature_combinations(feature_pool, min_features, max_features):
    """Generate all combinations of features within specified length range."""
    combos = []
    for length in range(min_features, max_features + 1):
        combos.extend(list(combinations(feature_pool, length)))
    return [list(combo) for combo in combos]


def build_lr_candidates(feature_combos, target, train_df, val_df, test_df, random_state):
    """Grid search for Logistic Regression."""
    candidates = []
    best = {'score': -1, 'results': None}
    
    for features in feature_combos:
        datasets = {
            "train": (train_df[features], train_df[target]),
            "validation": (val_df[features], val_df[target]),
            "test": (test_df[features], test_df[target]),
        }
        lr_results = build_logistic_regression_statsmodels(datasets)
        lr_val_acc = lr_results['Validation Accuracy']
        
        candidates.append({
            'Features': str(features),
            'Hyperparameters': '{}',
            'Val Accuracy': lr_val_acc,
            'Test Accuracy': lr_results['Test Accuracy'],
        })
        
        if lr_val_acc > best['score']:
            best = {'score': lr_val_acc, 'results': (features, lr_results)}
    
    return candidates, best


def build_xgb_candidates(feature_combos, target, train_df, val_df, test_df, random_state):
    """Grid search for XGBoost."""
    candidates = []
    best = {'score': -1, 'results': None}
    
    for features in feature_combos:
        datasets = {
            "train": (train_df[features], train_df[target]),
            "validation": (val_df[features], val_df[target]),
            "test": (test_df[features], test_df[target]),
        }
        
        for hparams in HYPERPARAMETERS['XGBoost']:
            xgb_hparams = {**hparams, 'random_state': random_state}
            model = xgb.XGBClassifier(**xgb_hparams)
            xgb_results = build_model_sklearn(model, datasets)
            xgb_val_acc = xgb_results['Validation Accuracy']
            
            candidates.append({
                'Features': str(features),
                'Hyperparameters': str(hparams),
                'Val Accuracy': xgb_val_acc,
                'Test Accuracy': xgb_results['Test Accuracy'],
            })
            
            if xgb_val_acc > best['score']:
                best = {'score': xgb_val_acc, 'results': (features, xgb_results)}
    
    return candidates, best


def build_cart_candidates(feature_combos, target, train_df, val_df, test_df, random_state):
    """Grid search for CART."""
    candidates = []
    best = {'score': -1, 'results': None}
    
    for features in feature_combos:
        datasets = {
            "train": (train_df[features], train_df[target]),
            "validation": (val_df[features], val_df[target]),
            "test": (test_df[features], test_df[target]),
        }
        
        for hparams in HYPERPARAMETERS['CART']:
            cart_hparams = {**hparams, 'random_state': random_state}
            model = DecisionTreeClassifier(**cart_hparams)
            cart_results = build_model_sklearn(model, datasets)
            cart_val_acc = cart_results['Validation Accuracy']
            
            candidates.append({
                'Features': str(features),
                'Hyperparameters': str(hparams),
                'Val Accuracy': cart_val_acc,
                'Test Accuracy': cart_results['Test Accuracy'],
            })
            
            if cart_val_acc > best['score']:
                best = {'score': cart_val_acc, 'results': (features, cart_results)}
    
    return candidates, best


def sensitivity_analysis(results, nets_test_df, output_dir):
    """
    Conduct sensitivity analysis on nets test set using the best model.
    Calculate expected win probability gains if jump ball win probabilities increased by 5%, 10%, 20%.
    
    Expected leverage = p*leverage - (1-p)*leverage, where p is win probability.
    """
    target = results['Target']
    
    # Identify best model based on validation accuracy
    best_model_name = None
    best_val_acc = -1
    for model_name in ['Logistic Regression', 'XGBoost', 'CART']:
        if model_name in results:
            val_acc = results[model_name]['Validation Accuracy']
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model_name = model_name
    
    if best_model_name is None:
        print("No valid models found for sensitivity analysis")
        return None
    
    print(f"\n{'='*80}")
    print(f"SENSITIVITY ANALYSIS - Using best model: {best_model_name} (Val Acc: {best_val_acc:.4f})")
    print(f"{'='*80}\n")
    
    # Get best model info
    features = results[best_model_name]['Features']
    model = results[best_model_name]['Model']
    
    # Limit to in-game jump balls only for sensitivity analysis, since start-of-game and start-of-OT jump balls are more practiced
    nets_test_df = nets_test_df[nets_test_df['jumpball_type'] == 'in-game']

    # Prepare nets test data
    X_nets = nets_test_df[features]
    
    # Generate predictions on nets test set
    if best_model_name == 'Logistic Regression':
        X_nets_sm = sm.add_constant(X_nets)
        predicted_probs = model.predict(X_nets_sm).values
    else:
        predicted_probs = model.predict_proba(X_nets)[:, 1]
    
    # Get leverage values
    leverage = nets_test_df['wp_leverage'].values
    
    # Calculate expected leverage at different probability levels
    scenarios = {
        'Current': predicted_probs,
        '+5%': np.clip(predicted_probs + 0.05, 0, 1),
        '+10%': np.clip(predicted_probs + 0.10, 0, 1),
        '+20%': np.clip(predicted_probs + 0.20, 0, 1),
    }
    
    results_summary = []
    for scenario_name, probs in scenarios.items():
        # Expected leverage = p*leverage - (1-p)*leverage = leverage*(2p - 1)
        expected_leverage = leverage * (2 * probs - 1)
        total_expected_wp = expected_leverage.sum()
        avg_expected_wp = expected_leverage.mean()
        
        results_summary.append({
            'Scenario': scenario_name,
            'Total Expected Win Prob Gain': round(total_expected_wp, 4),
            'Avg Expected Win Prob Gain': round(avg_expected_wp, 4),
            'In-Game Jump Balls': len(nets_test_df),
        })
    
    sensitivity_df = pd.DataFrame(results_summary)
    
    # Calculate gains relative to current scenario
    current_total = sensitivity_df.iloc[0]['Total Expected Win Prob Gain']
    sensitivity_df['Wins Added'] = round(sensitivity_df['Total Expected Win Prob Gain'] - current_total, 2)
    
    print("Sensitivity Analysis Results (Nets 2025):")
    print(sensitivity_df.to_string(index=False))
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    sensitivity_csv = f"{output_dir}/sensitivity_analysis.csv"
    sensitivity_df.to_csv(sensitivity_csv, index=False)
    print(f"\nSensitivity analysis saved to: {sensitivity_csv}")
    
    return sensitivity_df


def main():
    # Set random seed for reproducibility
    RANDOM_STATE = 170
    np.random.seed(RANDOM_STATE)
    target = 'team_1_jumpball_win'
    
    df = pd.read_csv(DATA_PATH)
    df = clean_data(df)
    df = class_balancer(df, target_column=target, random_state=RANDOM_STATE)
    df = standardize_features(df, ['height_diff', 'weight_diff', 'team_1_score_diff']) 
    df = enhance_data(df)

    nets_test_df = split_specific_team_season(df, season=2025, team_id=17) # Brooklyn Nets team_id
    filtered_df = df.drop(nets_test_df.index) # Remove Nets test data from the main dataframe
    train_df, val_df, test_df = split_data(filtered_df, split=[0.7, 0.15, 0.15], random_state=RANDOM_STATE)
    
    # Setup output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"models/wp/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run grid search for each model type
    feature_combos = generate_feature_combinations(FEATURE_POOL, MIN_FEATURES, MAX_FEATURES)
    
    lr_candidates, lr_best = build_lr_candidates(feature_combos, target, train_df, val_df, test_df, RANDOM_STATE)
    xgb_candidates, xgb_best = build_xgb_candidates(feature_combos, target, train_df, val_df, test_df, RANDOM_STATE)
    cart_candidates, cart_best = build_cart_candidates(feature_combos, target, train_df, val_df, test_df, RANDOM_STATE)
    
    # Save candidate CSVs
    all_candidates = {
        'Logistic Regression': lr_candidates,
        'XGBoost': xgb_candidates,
        'CART': cart_candidates,
    }
    
    for model_name, candidates in all_candidates.items():
        df_candidates = pd.DataFrame(candidates)
        csv_file = f"{output_dir}/{model_name.lower().replace(' ', '_')}_candidates.csv"
        df_candidates.to_csv(csv_file, index=False)
        print(f"Saved {len(candidates)} {model_name} candidates to: {csv_file}")
    
    # Export best models with visualizations
    print("\n" + "=" * 80)
    best_models = {
        'Logistic Regression': lr_best,
        'XGBoost': xgb_best,
        'CART': cart_best,
    }
    
    # Build results dict with all three best models
    results = {
        'Target': target,
    }
    
    for model_name, best in best_models.items():
        if best['results']:
            features, model_results = best['results']
            # Add features to model results
            model_results['Features'] = features
            results[model_name] = model_results
            print(f"{model_name}: {features} (Val Acc: {best['score']:.4f})")
            
        else:
            print(f"No results found for {model_name}")
    
    # Export all best models once
    try:
        export_results(results, output_dir, generate_visualizations=True)
    except Exception as e:
        print(f"ERROR exporting results: {e}")
    
    print(f"\nResults saved to: {output_dir}")

    sensitivity_table = sensitivity_analysis(results, nets_test_df, output_dir)


if __name__ == "__main__":
    main()