import pandas as pd

JUMPBALL_DATA_PATH = "data/jumpballs.csv"
PLAYER_DATA_PATH = "data/draft_data.csv"
GAME_ROSTERS_PATH = "data/game_rosters.csv"
WIN_PROB_PATH = "data/wpa_challenge_values_sim.parquet" #dataset derived from inpredictable.com to estimate value of winning a challenge


def inspect_empty_rows(df):
    """
    Inspect rows in the DataFrame where 'text' is "vs.". Is it always followed by a jumpball from the same game? Are there any other patterns? This function prints the number of such rows and displays the relevant columns for inspection.
    """
    empty_rows = df[df['athlete_id_1'].isnull() & df['text'].str.contains("vs.")].copy()
    print(empty_rows['text'].value_counts())

    print(f"Number of rows where 'text' is 'vs.': {len(empty_rows)}")
    print(empty_rows[['game_id', 'game_play_number', 'text']])

    # check if these rows are always followed by a jumpball from the same game
    count_followed_by_jumpball = 0
    for index, row in empty_rows.iterrows():
        game_id = row['game_id']
        game_play_number = row['game_play_number']
        next_row = df[(df['game_id'] == game_id) & (df['game_play_number'] == game_play_number + 1)]
        prev_row = df[(df['game_id'] == game_id) & (df['game_play_number'] == game_play_number - 1)]
        if not next_row.empty or not prev_row.empty:
            count_followed_by_jumpball += 1
        
    print(f"Number of 'vs.' rows followed by a jumpball from the same game: {count_followed_by_jumpball}")
            
    return empty_rows


def inspect_dupes(df):
    """
    Inspect rows in the DataFrame based on 'game_id' and 'game_play_number'. This function prints the occasions where two consecutive game plays are in the data, which should not happen. It returns a DataFrame of the duplicate rows for further inspection.
    """
    # Find consecutive game plays in the data -- 404
    dupes = df[(df['game_play_number'].diff() == 1) & (df['game_id'] == df['game_id'].shift())].copy()
    print(f"Number of consecutive game plays in the data: {len(dupes)}")

    #what about three consecutive game plays? -- 7
    three_consecutive_dupes = df[(df['game_play_number'].diff() == 1) & (df['game_id'] == df['game_id'].shift()) & (df['game_play_number'].diff().shift() == 1)].copy()
    print(f"Number of three consecutive game plays in the data: {len(three_consecutive_dupes)}")
    print(three_consecutive_dupes[['game_id', 'game_play_number', 'text']])

    #what about four consecutive game plays? -- 1
    four_consecutive_dupes = df[(df['game_play_number'].diff() == 1) & (df['game_id'] == df['game_id'].shift()) & (df['game_play_number'].diff().shift() == 1) & (df['game_play_number'].diff().shift(2) == 1)].copy()
    print(f"Number of four consecutive game plays in the data: {len(four_consecutive_dupes)}")
    print(four_consecutive_dupes[['game_id', 'game_play_number', 'text']])
    
    #what about five consecutive game plays? -- 0
    five_consecutive_dupes = df[(df['game_play_number'].diff() == 1) & (df['game_id'] == df['game_id'].shift()) & (df['game_play_number'].diff().shift() == 1) & (df['game_play_number'].diff().shift(2) == 1) & (df['game_play_number'].diff().shift(3) == 1)].copy()
    print(f"Number of five consecutive game plays in the data: {len(five_consecutive_dupes)}")
    
    return dupes



def collect_dupes(df):
    """
    Collect all sets of consecutive game plays in the data. Returns a list of dictionaries,
    each containing game_id, start_game_play_number, and end_game_play_number for every
    group of 2+ consecutive plays. This helps identify potential data bugs.
    """
    df = df.sort_values(['game_id', 'game_play_number']).reset_index(drop=True)
    
    consecutive_groups = []
    current_group_start = None
    current_group_end = None
    current_game_id = None
    
    for idx, row in df.iterrows():
        game_id = row['game_id']
        play_num = row['game_play_number']
        
        if idx == 0:
            current_group_start = play_num
            current_group_end = play_num
            current_game_id = game_id
        else:
            prev_row = df.iloc[idx - 1]
            prev_game_id = prev_row['game_id']
            prev_play_num = prev_row['game_play_number']
            
            # Check if this play is consecutive to the previous one in the same game
            if game_id == prev_game_id and play_num == prev_play_num + 1:
                current_group_end = play_num
            else:
                # End of a group - save it if it has 2+ plays
                if current_group_end - current_group_start >= 1:
                    consecutive_groups.append({
                        'game_id': current_game_id,
                        'start_game_play_number': current_group_start,
                        'end_game_play_number': current_group_end,
                        'length': current_group_end - current_group_start + 1
                    })
                current_group_start = play_num
                current_group_end = play_num
                current_game_id = game_id
    
    # Don't forget the last group
    if current_group_end - current_group_start >= 1:
        consecutive_groups.append({
            'game_id': current_game_id,
            'start_game_play_number': current_group_start,
            'end_game_play_number': current_group_end,
            'length': current_group_end - current_group_start + 1
        })

    
    # consecutive_df = pd.DataFrame(consecutive_groups)
    # consecutive_df.to_csv("data/consecutive_jumpballs.csv", index=False)

    return consecutive_groups


def clean_dupes_by_sparsity(df, consecutive_groups):
    """
    Remove rows from consecutive play groups that are strictly sparser.
    Sparsity is determined by comparing the SET of athlete IDs across athlete_id_1 and athlete_id_2 
    (treated as interchangeable) plus athlete_id_3.
    A row is removed if its athlete ID set is a strict subset of another row's set in the same group.
    """
    df = df.sort_values(['game_id', 'game_play_number']).reset_index(drop=True)
    athlete_cols = ['athlete_id_1', 'athlete_id_2', 'athlete_id_3']
    rows_to_remove = set()
    
    for group in consecutive_groups:
        game_id = group['game_id']
        start_play = group['start_game_play_number']
        end_play = group['end_game_play_number']
        
        # Get all rows in this group
        group_rows = df[(df['game_id'] == game_id) & 
                        (df['game_play_number'] >= start_play) & 
                        (df['game_play_number'] <= end_play)]
        
        if len(group_rows) < 2:
            continue
        
        # Build athlete ID sets for each row
        athlete_sets = {}
        for idx, row in group_rows.iterrows():
            athlete_set = set(row[athlete_cols].dropna())
            athlete_sets[idx] = athlete_set
        
        # Compare each row against all others
        for idx, athlete_set in athlete_sets.items():
            for other_idx, other_set in athlete_sets.items():
                if idx != other_idx:
                    # If this row's athletes are a strict subset of another row's, mark for removal
                    if athlete_set < other_set:  # strict subset
                        rows_to_remove.add(idx)
                        break
    
    return df.drop(list(rows_to_remove))


def clean_duplicates(df):
    """
    Clean the DataFrame by removing rows that are strictly sparser within consecutive play groups.
    This function identifies consecutive play groups and removes rows that have a strict subset of athlete IDs compared to other rows in the same group.
    """
    consecutive_groups = collect_dupes(df) #397 instances of consecutive plays
    cleaned_df = clean_dupes_by_sparsity(df, consecutive_groups) #244 rows cleaned across 397 instances
    return cleaned_df


def clean_violations(df):
    """
    Clean the DataFrame by removing rows that contain the word "violation" in the 'text' column. This function returns a DataFrame with those rows removed.
    """
    violations = df[df['text'].str.contains("violation", case=False, na=False)]
    print(f"Number of rows containing 'violation': {len(violations)}")
    return df.drop(violations.index)


def merge_player_data(df, player_data, game_data):
    """
    Merge player data into the jumpball DataFrame to get athlete teams and metadata.
    This function merges the jumpball DataFrame with player data and game rosters to enrich the dataset with additional information about the athletes involved in each jumpball event.
    """
    # Pre-merge game_data with player_data to avoid multiple joins
    enriched_roster = game_data[['game_id', 'athlete_id', 'team_id', 'athlete_position', 'athlete_guid']].merge(
        player_data[['athlete_guid', 'athlete_height', 'athlete_weight']], 
        on='athlete_guid', 
        how='left'
    )
    # Deduplicate on (game_id, athlete_id) to preserve row count in left merge
    enriched_roster = enriched_roster.drop_duplicates(subset=['game_id', 'athlete_id'])
    
    # Now do 3 merges instead of 6
    df = df.drop(columns=['team_id'])  # Drop to avoid confusion during merges -- this id value adds no value. I believe it was meant to signal the winner but is clearly noisy
    for athlete_num in [1, 2, 3]:
        athlete_id_col = f'athlete_id_{athlete_num}'
        df = df.merge(
            enriched_roster,
            how='left',
            left_on=['game_id', athlete_id_col],
            right_on=['game_id', 'athlete_id']
        )
        df = df.drop('athlete_id', axis=1)
        df = df.rename(columns={
            'team_id': f'team_id_{athlete_num}',
            'athlete_position': f'athlete_position_{athlete_num}',
            'athlete_guid': f'athlete_guid_{athlete_num}',
            'athlete_height': f'athlete_draft_height_{athlete_num}',
            'athlete_weight': f'athlete_draft_weight_{athlete_num}'
        })
    
    return df


def merge_win_prob_data(df):
    """
    Merge win probability data into the jumpball DataFrame to get the estimated value of winning a challenge.
    This function merges the jumpball DataFrame with win probability data to enrich the dataset with additional information about the potential impact of each jumpball event on the game's outcome.
    """
    def calculate_time_elapsed(row):
        period_time = min(row['period']-1,3) * 12 * 60 #assuming 12-minute periods, 5 min in OT equivalent to 5 min left in 4th quarter
        quarter_mins = (12 - row['clock_minutes'] - 1) * 60
        quarter_secs = 60 - row['clock_seconds']
        return period_time + quarter_mins + quarter_secs
    
    def clip_value(value, lower=-20, upper=20):
        return int(max(lower, min(upper, value)))
    
    
    df['time_elapsed'] = df.apply(calculate_time_elapsed, axis=1)
    df['time_rounded'] = df['time_elapsed'].apply(lambda x: ((x // 45.0) + 1) * 45) #round up to nearest 45 seconds to match with win prob data
    df['score_diff'] = df['home_score'] - df['away_score']
    df['score_diff_clipped'] = df['score_diff'].apply(clip_value, lower=-20, upper=20)
    df['spread_clipped'] = df['home_team_spread'].apply(clip_value, lower=-15, upper=15)

    win_prob_data = pd.read_parquet(WIN_PROB_PATH)

    df = df.merge(
        win_prob_data[['gt', 'm', 'line', 'oob_challenge']],
        how='left',
        left_on=['time_rounded', 'score_diff_clipped', 'spread_clipped'],
        right_on=['gt', 'm', 'line']
    )

    df['wp_leverage'] = round(df['oob_challenge'] / 2, 4)
    df = df.drop(columns=['gt', 'm', 'line', 'oob_challenge', 'time_elapsed', 'time_rounded', 'score_diff_clipped', 'spread_clipped'])
    
    return df


def determine_jumpball_winner(df):
    """
    Determine the winner of each jumpball event in the DataFrame. This function adds a new column 'jumpball_winner' to the DataFrame, indicating which athlete won the jumpball event based on the 'text' column.
    """
    def home_winner(row):
        if pd.isna(row['team_id_3']):
            # If athlete_id_3 is NaN, we don't know who won possession
            return None
        else:
            if row['team_id_3'] == row['home_team_id']:
                return True  # Home team won the jumpball
            elif row['team_id_3'] == row['away_team_id']:
                return False  # Away team won the jumpball
            else:
                return None  # Unknown winner, athlete_id_3 does not match either team

    def get_result(row):
        if row['home_won_jumpball'] is True:
            return row['home_team_id'], row['away_team_id'], row['home_team_name'], row['away_team_name']
        elif row['home_won_jumpball'] is False: 
            return row['away_team_id'], row['home_team_id'], row['away_team_name'], row['home_team_name']
        return None, None, None, None  # If we don't know who won, return None for all
           
    df['home_won_jumpball'] = df.apply(home_winner, axis=1)
    df[['jumpball_winner_id', 'jumpball_loser_id', 'jumpball_winner_team', 'jumpball_loser_team']] = df.apply(get_result, axis=1, result_type='expand')

    # count the number of times jumpball winner is not equal to winning_team_id assuming jumpball_winner_id is populated correctly
    # mismatch_count = df[~df['jumpball_winner_id'].isna() & (df['jumpball_winner_id'] != df['winning_team_id'])].shape[0]
    # print(f"Number of mismatches between jumpball_winner_id and winning_team_id: {mismatch_count}") 
    # there where 5254 mismatches, so the dataset was wrong to give us an additional team_id column. We need to use the id of the third player.
    
    return df


def main():
    jumpball_df = pd.read_csv(JUMPBALL_DATA_PATH)
    player_data = pd.read_csv(PLAYER_DATA_PATH)
    game_data = pd.read_csv(GAME_ROSTERS_PATH)
    
    # Get all consecutive play groups
    consecutive_groups = collect_dupes(jumpball_df)
    print(f"Total consecutive play groups: {len(consecutive_groups)}\n")
    
    # Clean sparse rows from groups
    cleaned_df = clean_dupes_by_sparsity(jumpball_df, consecutive_groups)
    rows_removed = len(jumpball_df) - len(cleaned_df)
    print(f"Rows removed due to sparsity: {rows_removed}\n")

    # Clean rows with invalid teams
    cleaned_teams_df = cleaned_df[(cleaned_df['home_team_id']<=30) & (cleaned_df['away_team_id']<=30)].copy()
    rows_removed_invalid_teams = len(cleaned_df) - len(cleaned_teams_df)
    print(f"Rows removed due to invalid teams: {rows_removed_invalid_teams}\n")
    
    # Clean rows containing 'violation'
    final_df = clean_violations(cleaned_teams_df)
    rows_removed_violations = len(cleaned_teams_df) - len(final_df)
    print(f"Total rows after cleaning violations: {len(final_df)}\n")

    # Merge player data to get athlete teams and metadata
    final_df = merge_player_data(final_df, player_data, game_data)
    print(f"Total rows after merging player data: {len(final_df)}\n")

    final_df = merge_win_prob_data(final_df)
    print(f"Total rows after merging win probability data: {len(final_df)}\n")

    final_df = determine_jumpball_winner(final_df)
    print(final_df.value_counts(subset=['home_won_jumpball']))

    final_df.to_csv("data/filtered-jumpballs.csv", index=False)
    final_df.sample(10, random_state=42).to_csv("src/data_processing/filtered-jumpballs-sample.csv", index=False)


if __name__ == "__main__":
    main()