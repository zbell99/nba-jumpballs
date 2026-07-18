**Date**: 2026-07-18 00:15 ET  
**Branch**: main  
**Summary**: docs-update

---

# Documentation Sync & README Update

## Objective
Update README.md and code documentation to reflect current project structure and capabilities after adding data processing module.

## Changes Made

### 1. README.md Expansion
Updated README with comprehensive sections:
- Added project title and goal statement
- Added **Project Structure** diagram showing `src/data_processing/`, `models/`, `tests/`, and `data/` directories
- Added **Setup & Installation** section with venv and requirements installation steps
- Added **Data Pipeline** section documenting:
  - `download_nba_pbp()` function for downloading SportsDataverse data
  - `process_jumpball_pbp()` function for extracting and classifying jumpballs
  - Jumpball classification types: start-of-game, start-of-ot, in-game
  - Output format and processing details
- Added **Usage** section with example command to run the pipeline
- Added **Dependencies** section listing key packages by category

### 2. Code Documentation
Enhanced `src/data_processing/jumpball_pbp.py`:
- Added module-level docstring explaining purpose, key functions, and SportsDataverse quirks
- Cleaned up inline comment about SportsDataverse bugs

## Key Findings

**Project Structure**:
- `src/data_processing/jumpball_pbp.py` contains main pipeline logic
- Well-structured functions with comprehensive docstrings already in place
- Data output saves to `data/jumpballs.csv`

**Dependencies Detected**:
- Data processing: pandas, polars, numpy
- NBA data source: sportsdataverse
- ML/Analytics: scikit-learn, xgboost, scipy
- Visualization: matplotlib, pillow
- Data cleaning: pyjanitor
- Total of 41 packages in requirements.txt

## Files Updated
1. `/Users/zbell/Dev/GitHub/nba-jumpballs/README.md` — Complete restructure with full documentation
2. `/Users/zbell/Dev/GitHub/nba-jumpballs/src/data_processing/jumpball_pbp.py` — Added module docstring

## Status
✅ Complete — Documentation now accurately reflects current codebase state and capabilities
