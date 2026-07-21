# NBA Jumpballs

This is version one of the jump ball repository. The goal of this project is to assess the frequency and impact of jump balls in NBA games.

## Project Structure

```
src/
├── data_exploration/
│   └── jumpball_explo.py      # Data inspection and cleaning utilities
├── data_processing/
│   ├── __init__.py
│   ├── jumpball_pbp.py        # NBA play-by-play data processing and jumpball extraction
│   ├── filter_jumpball_data.py # Data cleaning and deduplication pipeline
│   ├── player_data.py         # Player metadata enrichment
│   └── jumpball_wp_modelling.py # Win probability model with grid search for features and hyperparameters
├── helpers/
│   └── plotting_helpers.py     # Visualization utilities
├── __init__.py
.github/
└── skills/                     # Custom workflow skills
```

## Setup & Installation

1. **Create and activate virtual environment**:
   ```bash
   python3 -m venv jumpball-venv
   source jumpball-venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Pipeline

**Data Processing** (`src/data_processing/`):
- `jumpball_pbp.py`: Downloads NBA play-by-play data from SportsDataverse and extracts jumpball events (seasons 2002-2026). Classifies jumpballs as start-of-game, start-of-overtime, or in-game. Output: `data/jumpballs.csv`
- `player_data.py`: Loads and processes player metadata (height, weight, position)
- `filter_jumpball_data.py`: Cleans jumpball data by removing violations, deduplicating sparse rows, and enriching with player/team metadata and win probability leverage values. Output: `data/filtered-jumpballs.csv`
- `jumpball_wp_modelling.py`: Win probability model for jumpball outcomes with grid search optimization. Searches across feature combinations (2-4 features from pool of 4) and model-specific hyperparameters for Logistic Regression, XGBoost, and CART/Decision Tree models. Selects best model per type based on validation accuracy. Generates per-model feature importance, AUC curves, and tree visualizations.

**Data Exploration** (`src/data_exploration/`): Inspects, cleans, and visualizes jumpball data. Detects data quality issues, removes duplicates and anomalies, and generates analysis visualizations.

**Helpers** (`src/helpers/`): Provides reusable utilities like visualization helpers for analysis plots.

**Win Probability Model** (`src/data_processing/jumpball_wp_modelling.py`):
- Grid search across feature combinations and hyperparameters
- Model types: Logistic Regression (statsmodels), XGBoost (4 hyperparameter configs), CART (3 hyperparameter configs)
- Feature pool: `['height_diff', 'weight_diff', 'time_elapsed', 'team_1_score_diff']`
- Model selection: Best validation accuracy for each model type (avoids test set overfitting)
- Candidate tracking: Exports CSVs for all candidate models per type
- Visualization: Feature importance, AUC curves, and decision tree diagrams for best models

- **Sensitivity analysis**: Quantifies expected win probability gains if jump ball win probability improved by 5%, 10%, 20%.

## Usage

```bash
# Generate jumpball dataset
python src/data_processing/jumpball_pbp.py

# Analyze and visualize
python src/data_exploration/jumpball_explo.py
```
