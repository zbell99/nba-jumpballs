import json
import pickle
import os
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb

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


def class_balancer(df, target_column):
    """
    For this specific use case, we can easily balance the classes since every data point is two-sided. Thus, we can multiply the point by -1 at random so that our classes are balanced.
    """
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
    results['Logistic Regression'] = build_model(LogisticRegression(), datasets)
    results['XGBoost'] = build_model(xgb.XGBClassifier(), datasets)
    results['CART'] = build_model(DecisionTreeClassifier(random_state=170), datasets)
    
    export_results(results)


def build_model(model, datasets):
    X_train, y_train = datasets['train']
    X_val, y_val = datasets['validation']
    X_test, y_test = datasets['test']

    model.fit(X=X_train, y=y_train)

    val_preds = model.predict(X_val)
    test_preds = model.predict(X_test)

    return {
        "Model": model,
        "Hyperparameters": model.get_params(),
        "Validation Accuracy": accuracy_score(y_val, val_preds),
        "Test Accuracy": accuracy_score(y_test, test_preds),
        "Validation Classification Report": classification_report(y_val, val_preds, output_dict=True),
        "Test Classification Report": classification_report(y_test, test_preds, output_dict=True),
    }


def export_results(results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare metrics dict (exclude model objects for JSON)
    metrics = {}
    metrics['Features'] = results.get('Features')
    metrics['Target'] = results.get('Target')
    
    for model_name in ['Logistic Regression', 'XGBoost', 'CART']:
        if model_name in results:
            model_results = results[model_name]
            metrics[model_name] = {
                k: v for k, v in model_results.items() if k != "Model"
            }
            # Save model object separately
            model = model_results["Model"]
            model_file = f"models/wp/{timestamp}/{model_name.lower().replace(' ', '_')}_model.pkl"
            os.makedirs(os.path.dirname(model_file), exist_ok=True)
            with open(model_file, "wb") as f:
                pickle.dump(model, f)
    
    # Save metrics as JSON (handle NaN values)
    metrics_file = f"models/wp/{timestamp}/results.json"
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=4, default=lambda x: None if isinstance(x, float) and np.isnan(x) else x)


def main():
    df = pd.read_csv(DATA_PATH)
    df = clean_data(df)

    nets_test_df = split_specific_team_season(df, season=2025, team_id=17) # Brooklyn Nets team_id
    filtered_df = df.drop(nets_test_df.index) # Remove Nets test data from the main dataframe
    train_df, val_df, test_df = split_data(filtered_df, split=[0.7, 0.15, 0.15])
    
    features = ['height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff']
    target = 'team_1_jumpball_win'
    train_df = class_balancer(train_df, target_column=target)
    run_modeling_suite(regressors=features, target=target, train_df=train_df, val_df=val_df, test_df=test_df)


if __name__ == "__main__":
    main()