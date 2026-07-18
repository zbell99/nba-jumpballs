# NBA Jumpballs

This is version one of the jump ball repository. The goal of this project is to assess the frequency and impact of jump balls in NBA games.

## Project Structure

```
src/
├── data_processing/
│   ├── __init__.py
│   └── jumpball_pbp.py       # NBA play-by-play data processing and jumpball extraction
├── data_exploration/
│   └── jumpball_explo.py      # Data inspection and cleaning utilities
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

**Data Processing** (`src/data_processing/`): Downloads NBA play-by-play data from SportsDataverse and extracts jumpball events (seasons 2002-2026). Classifies jumpballs as start-of-game, start-of-overtime, or in-game. Output: `data/jumpballs.csv`

**Data Exploration** (`src/data_exploration/`): Inspects, cleans, and visualizes jumpball data. Detects data quality issues, removes duplicates and anomalies, and generates analysis visualizations.

## Usage

```bash
# Generate jumpball dataset
python src/data_processing/jumpball_pbp.py

# Analyze and visualize
python src/data_exploration/jumpball_explo.py
```
