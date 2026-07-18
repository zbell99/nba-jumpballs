# NBA Jumpballs

This is version one of the jump ball repository. The goal of this project is to assess the frequency and impact of jump balls in NBA games.

## Project Structure

```
src/
├── data_processing/
│   ├── __init__.py
│   └── jumpball_pbp.py       # NBA play-by-play data processing and jumpball extraction
├── __init__.py
models/                         # Model training and analysis (planned)
tests/
├── unit/                       # Unit tests
└── __init__.py
data/
├── jumpballs.csv              # Processed jumpball events
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

## Data Pipeline

### Processing NBA Jumpballs

The main pipeline is in `src/data_processing/jumpball_pbp.py`:

- **`download_nba_pbp(seasons, return_as_pandas=True)`**: Downloads NBA play-by-play data from SportsDataverse (seasons >= 2002)
- **`process_jumpball_pbp()`**: Filters for jumpball events and classifies them as:
  - `start-of-game`: Opening tip (game_play_number ≤ 2)
  - `start-of-ot`: Overtime tips (period ≥ 5, clock at 5:00)
  - `in-game`: All other jumpballs

**Output**: Processes seasons 2002-2026 and saves results to `data/jumpballs.csv`

## Usage

Run the jumpball processing pipeline:
```bash
python src/data_processing/jumpball_pbp.py
```

This generates `data/jumpballs.csv` with classifications and prints summary statistics.
