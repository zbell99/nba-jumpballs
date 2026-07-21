**Date**: 2026-07-20 23:01:30 (ET)  
**Branch**: jumpball-wp-model  
**Summary**: sensitivity analysis

---

## Decisions

### Decision: Implement Expected Leverage Sensitivity Analysis
- **Your choice:** Build sensitivity analysis on nets test set using best model (logistic/xg/cart)
- **Reasoning:** Quantify value of improved jump ball win probability at different confidence levels
- **Method:** Use formula `p*leverage - (1-p)*leverage` to calculate expected win probability gains
- **Increments:** Model probability improvements of +5%, +10%, +20% percentage points

### Decision: Select Best Model Automatically
- **Your choice:** Automatically identify best model by validation accuracy
- **Reasoning:** Ensures reproducible model selection based on held-out validation performance
- **Details:** Compare across three model types and select highest performing one

---

## Conversation Transcript

👤 **You:** I want to create a sensitivity analysis on my nets test df. Picking the best model between logistic/xg/cart, I want to then predict the probabilities on my test set and assess the expected wp_leverage gained if I increased those probabilities by 5%, 10%, 20%.

Before starting, let me know if this makes sense.

🤖 **Copilot:** This makes sense! Here's what I understand you're trying to do:

1. **Select best model**: Compare logistic regression, XGBoost, and CART on the nets test set (Brooklyn Nets 2025 season data held out separately) and pick the one with best performance

2. **Generate predictions**: Use that best model to predict jump ball win probabilities for each game in the nets test set

3. **Sensitivity analysis**: For each jump ball, calculate the expected win probability impact (`wp_leverage`) under different scenarios:
   - Current: based on actual predicted probabilities
   - +5%: if your jump ball win probability improved by 5 percentage points
   - +10%: if it improved by 10 percentage points  
   - +20%: if it improved by 20 percentage points

4. **Quantify gains**: Sum up the `wp_leverage` across all jump balls in each scenario to see the total expected win probability gain

This is a smart analysis—it essentially asks "if we were 5%/10%/20% better at winning jump balls, how many more games would we win?" It uses the actual leverage values already in your data, which accounts for the game state (close games count more than blowouts).

**One clarification**: When you say "increase probabilities by 5%", do you mean:
- **A)** Increase by 5 percentage points (e.g., 50% → 55%)?
- **B)** Multiply by 1.05 (e.g., 50% → 52.5%)?

I'd recommend **A** (percentage points) since it's more interpretable for this analysis.

Does this align with what you want to do?

👤 **You:** A. Yes this aligns. Just remember that expected leverage for a jumpball would be p*leverage + (1-p)*-leverage

🤖 **Copilot:** Perfect! That makes complete sense. Expected leverage accounts for both the upside (team wins) and downside (team loses) scenarios weighted by probability.

I've implemented a `sensitivity_analysis` function that:

1. Loads the nets test set 
2. Identifies the best model from the three candidates (based on validation accuracy)
3. Generates predictions on the nets test set
4. Calculates expected leverage at current probabilities and at +5%, +10%, +20% scenarios
5. Returns a summary showing total expected wins gained at each sensitivity level

The function has been added to your jumpball_wp_modelling.py file with the correct expected leverage formula: `p*leverage - (1-p)*leverage`.

The results get printed to console and saved to `models/wp/sensitivity_analysis.csv`. This will show you exactly how many additional games the Nets could expect to win if they improved their jump ball win probability by 5, 10, or 20 percentage points.

---

## Implementation Details

### Changes Made
- Added `sensitivity_analysis()` function to `src/data_processing/jumpball_wp_modelling.py`
- Function selects best model by validation accuracy
- Generates predictions on nets 2025 test set
- Calculates expected leverage using formula: `p*leverage - (1-p)*leverage`
- Supports probability improvements of +5%, +10%, +20% (clipped to [0,1])
- Outputs summary table with total and average expected win probability gains
- Saves results to `models/wp/sensitivity_analysis.csv`

### Key Formula
Expected Leverage = p × leverage - (1-p) × leverage = leverage × (2p - 1)

Where:
- p = predicted jump ball win probability
- leverage = game state win probability significance from data
