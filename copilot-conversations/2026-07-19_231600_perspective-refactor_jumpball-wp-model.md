**Date**: 2026-07-19 23:16:00 (ET)
**Branch**: jumpball-wp-model
**Summary**: perspective-refactor

---

## Decisions

### Decision: Restructure Dataset to Use Team_1 Perspective
- **Your choice:** Transform `home_won_jumpball` → `team_1_jumpball_win`, and create `team_1_score_diff` and `team_1_spread` fields
- **Reasoning:** Align all perspective-dependent fields with athlete_1's team instead of hardcoded home/away, making the dataset team-agnostic and more flexible
- **Fields created:**
  - `team_1_jumpball_win`: True if athlete_1's team won, False if athlete_2's team won, None otherwise
  - `team_1_score_diff`: Score differential from team_1's perspective (team_1_score - team_2_score)
  - `team_1_spread`: Spread from team_1's perspective (negated if team_1 is away team)
- **Fields left alone:** `home_score`, `away_score`, `home_team_spread`, and all other perspective-dependent fields remain for reference

---

## Conversation Transcript

👤 **You:** I need to update my dataset because home_team doesn't always align with athlete_1. Instead, I need team_1_jumpball_win and I need score and spread fields to be in the perspective of team_1

Let's talk through a plan before implementation

🤖 **Copilot:** I want to make sure I understand the restructuring correctly before we proceed. Let me clarify a few things:

**Current structure:**
- `home_won_jumpball` → boolean indicating if home team won
- `home_score`, `away_score` → scores from home/away perspective
- `home_team_spread` → spread from home team's perspective
- `athlete_id_1`, `athlete_id_2` → the two athletes in the jumpball
- `team_id_1`, `team_id_2` → their teams

**Desired structure:**
- `team_1_jumpball_win` → boolean indicating if athlete_1's team won the jumpball
- Score fields from team_1's perspective — so if athlete_1 is on the away team, we'd flip the scores
- Spread fields from team_1's perspective

**Clarifying questions:**

1. **Score/spread naming**: Should we rename to something like `team_1_score`, `team_2_score` and `team_1_spread`? Or keep the original names but with values flipped based on which team is team_1?

2. **Other fields that depend on perspective**: Are there other fields beyond score and spread that should be flipped? For example:
   - `away_timeout_called`, `home_timeout_called` → should these become `team_1_timeout_called`, `team_2_timeout_called`?
   - `lead_qtr`, `lead_game_half`, `lead_half` → these indicate which team had the lead; should they flip too?
   - `score_diff` → should this become team_1's score minus team_2's score?

3. **Scope**: Should we update the existing `determine_jumpball_winner()` function and the pipeline in `main()`, or create a separate transformation function?

Let me know your preferences and I'll build out the implementation plan!

👤 **You:** i want team_1_jumpball_win, team_1_score_diff, team_1_spread.

You can leave the others alone

🤖 **Copilot:** Perfect. Here's the plan:

**New function: `perspective_from_team_1()`**
- `team_1_jumpball_win`: True if `athlete_id_3` belongs to team_1, False if belongs to team_2, None otherwise
- `team_1_score_diff`: (team_1_score - team_2_score). If team_1 is home team, use `home_score - away_score`. If team_1 is away, use `away_score - home_score`
- `team_1_spread`: If team_1 is home team, use `home_team_spread` as-is. If team_1 is away team, negate it

**Integration:**
- Call this new function in `main()` after `determine_jumpball_winner()` 
- Keep all other fields untouched

Sound good? Ready to implement?

👤 **You:** yes

🤖 **Copilot:** [Implementation completed - added `perspective_from_team_1()` function to filter_jumpball_data.py and integrated it into the main pipeline]

---

## Implementation Details

The `perspective_from_team_1()` function:
- Determines team_1_jumpball_win by checking if athlete_id_3 matches team_id_1 (True) or team_id_2 (False)
- Calculates team_1_score_diff based on whether team_1 is the home or away team
- Calculates team_1_spread by negating `home_team_spread` if team_1 is away team
- Integrates seamlessly into the existing data processing pipeline in `main()`
