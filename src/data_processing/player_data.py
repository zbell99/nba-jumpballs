from sportsdataverse.nba.nba_loaders import load_nba_game_rosters, load_nba_draft
import pandas as pd

def download_game_rosters(seasons=[], return_as_pandas=True):
    """Load espn_nba_game_rosters (sportsdataverse-data release).

    Source: https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_nba_game_rosters

    Args:
        seasons: an int or iterable of seasons (>= 2002).
        return_as_pandas: return a pandas DataFrame instead of polars.

    Returns:
        A polars (or pandas) DataFrame; seasons with no published asset are
        skipped with a warning rather than raising (404-safe).

        |col_name             |type    |
        |:--------------------|:-------|
        |season               |Int32   |
        |game_id              |String  |
        |team_id              |Int32   |
        |team_slug            |String  |
        |team_abbreviation    |String  |
        |team_display_name    |String  |
        |home_away            |String  |
        |athlete_id           |Int32   |
        |athlete_uid          |String  |
        |athlete_guid         |String  |
        |athlete_display_name |String  |
        |athlete_short_name   |String  |
        |athlete_first_name   |String  |
        |athlete_last_name    |String  |
        |athlete_jersey       |String  |
        |athlete_position     |String  |
        |athlete_headshot     |String  |
        |starter              |Boolean |
        |did_not_play         |Boolean |
        |active               |Boolean |
        |ejected              |Boolean |
        |reason               |String  |

    Example:
        Quick start::

            download_game_rosters(seasons=2002)
    """

    # Schema change in 2020, so we need to load each season separately and concatenate them together
    dfs = []
    for season in seasons:
        df = load_nba_game_rosters(seasons=[season], return_as_pandas=return_as_pandas)
        dfs.append(df)
    game_rosters = pd.concat(dfs, ignore_index=True)
    return game_rosters


def download_draft_data(seasons=[], return_as_pandas=True):
    """Load espn_nba_draft (sportsdataverse-data release).

    Source: https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_nba_draft

    Args:
        seasons: an int or iterable of seasons (>= 2003).
        return_as_pandas: return a pandas DataFrame instead of polars.

    Returns:
        A polars (or pandas) DataFrame; seasons with no published asset are
        skipped with a warning rather than raising (404-safe).

        |col_name                      |type   |
        |:-----------------------------|:------|
        |season                        |Int32  |
        |round                         |Int32  |
        |round_display_name            |String |
        |pick                          |Int32  |
        |overall_pick                  |Int32  |
        |pick_traded                   |String |
        |pick_notes                    |String |
        |athlete_id                    |Int32  |
        |athlete_uid                   |String |
        |athlete_guid                  |String |
        |athlete_first_name            |String |
        |athlete_last_name             |String |
        |athlete_full_name             |String |
        |athlete_display_name          |String |
        |athlete_short_name            |String |
        |athlete_height                |String |
        |athlete_weight                |String |
        |athlete_position_abbreviation |String |
        |athlete_position_name         |String |
        |athlete_headshot_href         |String |
        |college_id                    |Int32  |
        |college_name                  |String |
        |college_short_name            |String |
        |college_abbreviation          |String |
        |team_id                       |Int32  |
        |team_uid                      |String |
        |team_slug                     |String |
        |team_location                 |String |
        |team_name                     |String |
        |team_abbreviation             |String |
        |team_display_name             |String |
        |team_short_display_name       |String |
        |team_color                    |String |
        |team_alternate_color          |String |
        |team_logo                     |String |

    Example:
        Quick start::

            download_draft_data(seasons=2025)
    """
    dfs = []
    for season in seasons:
        df = load_nba_draft(seasons=[season], return_as_pandas=return_as_pandas)
        dfs.append(df)
    draft_data = pd.concat(dfs, ignore_index=True)
    return draft_data


def convert_player_heights_and_weights(df):
    """Convert player heights and weights to numeric values.

    Args:
        df: A pandas DataFrame containing player data with 'athlete_height' and 'athlete_weight' columns.

        Example: Height: 6' 3", but double quotes for inches for weird formatting choice, Weight: 171 lbs

    Returns:
        A pandas DataFrame with 'athlete_height' and 'athlete_weight' columns converted to numeric values.
    """
    # Convert height from feet-inches to inches
    def height_to_inches(height_str):
        if pd.isna(height_str):
            return None
        try:
            feet, inches = height_str.split("' ")
            inches = inches.rstrip('"')  # Remove the double quote from inches
            return int(feet) * 12 + int(inches)
        except ValueError:
            return None

    # Extract numeric value from weight string
    def weight_to_numeric(weight_str):
        if pd.isna(weight_str):
            return None
        try:
            return int(weight_str.split()[0])
        except (ValueError, IndexError):
            return None

    df['athlete_height'] = df['athlete_height'].apply(height_to_inches)
    df['athlete_weight'] = df['athlete_weight'].apply(weight_to_numeric)

    return df


def process_player_data():
    game_df = download_game_rosters(seasons=range(2003, 2027), return_as_pandas=True)
    game_df.to_csv("data/game_rosters.csv", index=False)
    draft_df = download_draft_data(seasons=range(2003, 2027), return_as_pandas=True)
    draft_df = convert_player_heights_and_weights(draft_df)
    draft_df.to_csv("data/draft_data.csv", index=False)
    return


if __name__ == "__main__":
    process_player_data()