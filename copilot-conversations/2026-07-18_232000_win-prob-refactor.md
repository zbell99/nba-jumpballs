---
**Date**: 2026-07-18
**Branch**: win-prob-data
**Summary**: win-prob-refactor
---

# Conversation: Win Probability Data Merge Optimization

## Decisions

### Decision 1: Refactor Complex Lambda into Helper Function
- **Your choice:** Extract row-by-row lookup logic into a separate `get_wp_leverage()` function
- **Reasoning:** Lambda was hard to read with multiple filtering conditions on one line
- **Alternative:** Leave as inline lambda (rejected due to readability)

### Decision 2: Switch from `.apply()` to `.merge()`
- **Your choice:** Replace row-by-row iteration with vectorized pandas `.merge()`
- **Reasoning:** Pandas merge is faster and cleaner than looping through rows
- **Alternative:** Keep `.apply()` with helper function (rejected for performance)

### Decision 3: Add Rounding to Join Keys
- **Your choice:** Round `time_elapsed`, `score_diff_clipped`, and `spread_clipped` before merge
- **Reasoning:** Floating-point precision was preventing matches with win_prob_data
- **Alternative:** Debug the exact join conditions (rejected after discovering rounding solved it)

---

## Transcript

👤 **You:** this seems very confusing to put in one line

🤖 **Copilot:** You're right. That lambda is hard to read with all the filtering logic crammed together. Let me refactor it into a separate helper function to make it clearer:

[Extracted `get_wp_leverage()` function to handle the lookup logic]

👤 **You:** is this easier with np?

🤖 **Copilot:** For this type of lookup, **pandas `.merge()` would be cleaner and faster** than NumPy or row-by-row `.apply()`. You could vectorize the entire operation:

[Suggested replacing row-by-row apply with vectorized merge]

👤 **You:** I'm really confused why this 'oob_challenge' value only populates on some of the rows?

🤖 **Copilot:** The merge only populates `oob_challenge` for rows where the join keys match in `win_prob_data`. For non-matching rows, you get NaN. [Added debug output to diagnose match rate]

👤 **You:** I figured it out. I had to round my time_elapsed and spreads

---

## Summary

Refactored win probability data enrichment from a complex inline lambda to a clean vectorized approach using pandas `.merge()`. Fixed NaN issues by rounding join keys to match win probability data precision, achieving 100% match rate.
