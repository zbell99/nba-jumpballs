import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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


def plot_jumpballs_per_game_per_season(df):
    """
    Plot the average number of in-game jumpball events per game for each season.
    """
    
    # Count in-game jumpballs per game per season
    in_game_mask = df['jumpball_type'] == "in-game"
    jumpballs_per_game = df[in_game_mask].groupby(['season', 'game_id']).size().reset_index(name='in_game_count')
    
    # Get all unique games per season (including those with zero in-game jumpballs)
    all_games = df.groupby(['season', 'game_id']).size().reset_index(name='_').drop('_', axis=1)
    
    # Merge and fill missing games with 0 in-game jumpballs
    all_games_with_counts = all_games.merge(jumpballs_per_game, on=['season', 'game_id'], how='left')
    all_games_with_counts['in_game_count'] = all_games_with_counts['in_game_count'].fillna(0)
    
    # Calculate average per season
    avg_per_season = all_games_with_counts.groupby('season')['in_game_count'].mean().reset_index(name='avg_jumpballs_per_game')
    
    print(avg_per_season)
    
    # Plotting
    plt.figure(figsize=(12, 6))
    sns.barplot(x='season', y='avg_jumpballs_per_game', data=avg_per_season)
    plt.title('Average In-Game Jumpballs per Game per Season')
    plt.xlabel('Season')
    plt.ylabel('Jumpballs per Game - not including tipoffs')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig("data/avg_jumpballs_per_game_per_season.png")


def chart_team_jumpball_player_variance(df):
    """
    Chart the proportion of the number of jumpball events that go to top 1 player and top 3 players in a season, considering start-game and start-ot only.

    Returns: Color coded table with teams on the left, season on the top, and the proportion of jumpball events that go to top 1 player and top 3 players in a season.
    """

    #next commit
    



def main():
    jumpball_df = pd.read_csv("data/jumpballs.csv")
    
    # Get all consecutive play groups
    consecutive_groups = collect_dupes(jumpball_df)
    print(f"Total consecutive play groups: {len(consecutive_groups)}\n")
    
    # Clean sparse rows from groups
    cleaned_df = clean_dupes_by_sparsity(jumpball_df, consecutive_groups)
    rows_removed = len(jumpball_df) - len(cleaned_df)
    print(f"Rows removed due to sparsity: {rows_removed}\n")
    
    # Clean rows containing 'violation'
    final_df = clean_violations(cleaned_df)
    rows_removed_violations = len(cleaned_df) - len(final_df)

    plot_jumpballs_per_game_per_season(final_df)


if __name__ == "__main__":
    main()