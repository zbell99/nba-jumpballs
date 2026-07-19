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
│   └── player_data.py         # Player metadata enrichment
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

**Data Exploration** (`src/data_exploration/`): Inspects, cleans, and visualizes jumpball data. Detects data quality issues, removes duplicates and anomalies, and generates analysis visualizations.

**Helpers** (`src/helpers/`): Provides reusable utilities like visualization helpers for analysis plots.

## Usage

```bash
# Generate jumpball dataset
python src/data_processing/jumpball_pbp.py

# Analyze and visualize
python src/data_exploration/jumpball_explo.py
```
