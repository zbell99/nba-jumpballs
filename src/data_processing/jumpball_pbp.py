"""NBA Play-by-Play Data Processing Module

This module provides tools to download and process NBA play-by-play data
from SportsDataverse, with specific focus on identifying and classifying
jump ball events (opening tips, overtime tips, and in-game jumps).

Key functions:
- download_nba_pbp: Fetch raw PBP data from SportsDataverse
- process_jumpball_pbp: Extract and classify jump ball events

Note: SportsDataverse can be buggy; other league loaders may need uncommenting.
"""
from sportsdataverse.nba.nba_loaders import load_nba_pbp
import pandas as pd

def download_nba_pbp(seasons=[], return_as_pandas=True):
    """Load NBA play-by-play data. Docstring from the original source code below.

    Source: https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_nba_pbp

    Args:
        seasons: an int or iterable of seasons (>= 2002).
        return_as_pandas: return a pandas DataFrame instead of polars.

    Returns:
        A polars (or pandas) DataFrame; seasons with no published asset are
        skipped with a warning rather than raising (404-safe).

        |col_name                        |type                                                   |
        |:-------------------------------|:------------------------------------------------------|
        |id                              |Float64                                                |
        |sequence_number                 |String                                                 |
        |type_id                         |Int32                                                  |
        |type_text                       |String                                                 |
        |text                            |String                                                 |
        |away_score                      |Int32                                                  |
        |home_score                      |Int32                                                  |
        |period_number                   |Int32                                                  |
        |period_display_value            |String                                                 |
        |clock_display_value             |String                                                 |
        |scoring_play                    |Boolean                                                |
        |score_value                     |Int32                                                  |
        |shooting_play                   |Boolean                                                |
        |coordinate_x_raw                |Float64                                                |
        |coordinate_y_raw                |Float64                                                |
        |season                          |Int32                                                  |
        |season_type                     |Int32                                                  |
        |away_team_id                    |Int32                                                  |
        |away_team_name                  |String                                                 |
        |away_team_mascot                |String                                                 |
        |away_team_abbrev                |String                                                 |
        |away_team_name_alt              |String                                                 |
        |home_team_id                    |Int32                                                  |
        |home_team_name                  |String                                                 |
        |home_team_mascot                |String                                                 |
        |home_team_abbrev                |String                                                 |
        |home_team_name_alt              |String                                                 |
        |home_team_spread                |Float64                                                |
        |game_spread                     |Float64                                                |
        |home_favorite                   |Boolean                                                |
        |game_spread_available           |Boolean                                                |
        |game_id                         |Int32                                                  |
        |qtr                             |Int32                                                  |
        |time                            |String                                                 |
        |clock_minutes                   |Int32                                                  |
        |clock_seconds                   |Float64                                                |
        |half                            |String                                                 |
        |game_half                       |String                                                 |
        |lead_qtr                        |Int32                                                  |
        |lead_game_half                  |String                                                 |
        |start_quarter_seconds_remaining |Int32                                                  |
        |start_half_seconds_remaining    |Int32                                                  |
        |start_game_seconds_remaining    |Int32                                                  |
        |game_play_number                |Int32                                                  |
        |end_quarter_seconds_remaining   |Int32                                                  |
        |end_half_seconds_remaining      |Int32                                                  |
        |end_game_seconds_remaining      |Int32                                                  |
        |period                          |Int32                                                  |
        |team_id                         |Int32                                                  |
        |athlete_id_1                    |Int32                                                  |
        |athlete_id_2                    |Int32                                                  |
        |athlete_id_3                    |Int32                                                  |
        |lag_qtr                         |Int32                                                  |
        |lag_game_half                   |String                                                 |
        |coordinate_x                    |Float64                                                |
        |coordinate_y                    |Float64                                                |
        |game_date                       |Date                                                   |
        |game_date_time                  |Datetime(time_unit='us', time_zone='America/New_York') |
        |type_abbreviation               |String                                                 |

    Example:
        Quick start::

            load_nba_pbp(seasons=2024)
    """

    # Schema change in 2020, so we need to load each season separately and concatenate them together
    dfs = []
    for season in seasons:
        df = load_nba_pbp(seasons=[season], return_as_pandas=return_as_pandas)
        dfs.append(df)
    pbp_data = pd.concat(dfs, ignore_index=True)
    return pbp_data


def process_jumpball_pbp():
    df = download_nba_pbp(seasons=range(2002, 2027), return_as_pandas=True)

    JUMPBALL_IDENTIFIERS = [
        "Jump Ball", #pre 2020
        "Jumpball", #post 2020
    ]

    df = df[df['type_text'].isin(JUMPBALL_IDENTIFIERS)].copy()

    df['jumpball_type'] = "in-game"

    # Seasons before 2020 label the opening tip as game_play_number 2, while seasons 2020 and later label it as game_play_number 1.
    df.loc[df['game_play_number'] <= 2, 'jumpball_type'] = "start-of-game"

    #Captures any overtime tipoff
    df.loc[(df['period_number'] >= 5) & (df['clock_display_value'] == "5:00"), 'jumpball_type'] = "start-of-ot"
    
    return df


if __name__ == "__main__":
    jumpball_df = process_jumpball_pbp()
    jumpball_df.to_csv("data/jumpballs.csv", index=False)
    print(f"Processed {len(jumpball_df)} jumpball events and saved to jumpballs.csv")
    print(jumpball_df["jumpball_type"].value_counts())