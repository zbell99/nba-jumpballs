import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


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
    Chart the proportion of the number of jumpball events that go to top players in a season, considering start-game and start-ot only.
    Accounts for both athletes in each jumpball event.

    Returns: Filled bar for each team with proportion of each player who jumped for the team in that season.
    """

    start_mask = df['jumpball_type'].isin(["start-of-game", "start-ot"])
    start_jumpballs = df[start_mask].copy()

    # Create two dataframes - one for each athlete in the jumpball
    athlete1 = start_jumpballs[['season', 'team_id_1', 'athlete_id_1']].rename(
        columns={'team_id_1': 'team_id', 'athlete_id_1': 'athlete_id'}
    ).dropna()
    athlete2 = start_jumpballs[['season', 'team_id_2', 'athlete_id_2']].rename(
        columns={'team_id_2': 'team_id', 'athlete_id_2': 'athlete_id'}
    ).dropna()
    
    # Combine both athletes
    all_athletes = pd.concat([athlete1, athlete2], ignore_index=True)
    
    # Count jumpballs per team per player per season
    season_team_player_counts = all_athletes.groupby(['season', 'team_id', 'athlete_id']).size().reset_index(name='count')
    
    # Get totals per season per team
    season_team_totals = all_athletes.groupby(['season', 'team_id']).size().reset_index(name='total')
    
    # Merge to calculate proportions per season
    season_proportions = season_team_player_counts.merge(season_team_totals, on=['season', 'team_id'])
    season_proportions['proportion'] = season_proportions['count'] / season_proportions['total']
    
    # Rank players by proportion within each season and team (highest proportion = rank 1)
    season_proportions['rank'] = season_proportions.groupby(['season', 'team_id'])['proportion'].rank(method='first', ascending=False).astype(int)
    
    # Create all possible combinations of team, season, and rank per team (only for ranks that team has)
    season_proportions_filled_list = []
    
    for team in season_proportions['team_id'].unique():
        team_data = season_proportions[season_proportions['team_id'] == team]
        all_seasons = team_data['season'].unique()
        all_ranks = team_data['rank'].unique()
        
        # Create combinations for this team only
        team_index = pd.MultiIndex.from_product([all_seasons, [team], all_ranks], names=['season', 'team_id', 'rank'])
        team_full_df = pd.DataFrame(index=team_index).reset_index()
        
        # Merge with actual proportions for this team
        team_filled = team_full_df.merge(team_data[['season', 'team_id', 'rank', 'proportion']], 
                                         on=['season', 'team_id', 'rank'], how='left')
        team_filled['proportion'] = team_filled['proportion'].fillna(0)
        season_proportions_filled_list.append(team_filled)
    
    season_proportions_filled = pd.concat(season_proportions_filled_list, ignore_index=True)
    
    # Average proportions across seasons for each team/rank
    rank_proportions = season_proportions_filled.groupby(['team_id', 'rank'])['proportion'].mean().reset_index()

    # Plotting - stacked bar chart
    pivot_data = rank_proportions.pivot_table(
        index='team_id',
        columns='rank',
        values='proportion',
        fill_value=0
    )
    
    plt.figure(figsize=(14, 6))
    pivot_data.plot(kind='bar', stacked=True, ax=plt.gca(), width=0.7, legend=False)
    plt.title('Jumpball Player Distribution by Team (Start-of-Game & Start-OT)')
    plt.xlabel('Team ID')
    plt.ylabel('Proportion')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("data/team_jumpball_player_variance.png", dpi=150, bbox_inches='tight')


def chart_team_jumpball_winrate(df):
    """
    Chart the proportion of jumpball events won by each team in a season, considering start-game and start-ot only.
    Accounts for both athletes in each jumpball event.

    Returns: Heatmap with teams on rows and seasons on columns, showing win proportions.
    """

    start_mask = df['jumpball_type'].isin(["in-game"])
    start_jumpballs = df[start_mask].copy()

    # Count jumpballs won per team per season
    team_wins = start_jumpballs.groupby(['season', 'jumpball_winner_team']).size().reset_index(name='wins')
    
    # Count total jumpballs per team per season
    team_losses = start_jumpballs.groupby(['season', 'jumpball_loser_team']).size().reset_index(name='losses')
    
    # Merge to calculate win proportions
    team_win_proportions = team_wins.merge(team_losses, left_on=['season', 'jumpball_winner_team'], right_on=['season', 'jumpball_loser_team'], how='left')
    team_win_proportions['losses'] = team_win_proportions['losses'].fillna(0)
    team_win_proportions['proportion'] = team_win_proportions['wins'] / (team_win_proportions['wins'] + team_win_proportions['losses'])
    
    # Pivot data for heatmap: teams as rows, seasons as columns
    heatmap_data = team_win_proportions.pivot_table(
        index='jumpball_winner_team',
        columns='season',
        values='proportion'
    )
    
    # Create heatmap with red (0) -> white (0.5) -> green (1) gradient
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        heatmap_data,
        cmap='RdYlGn',
        center=0.5,
        vmin=0,
        vmax=1,
        cbar_kws={'label': 'Win Proportion'},
        linewidths=0.5,
        linecolor='gray'
    )
    plt.title('Jumpball Win Rate by Team and Season')
    plt.xlabel('Season')
    plt.ylabel('Team')
    plt.tight_layout()
    plt.savefig("data/team_jumpball_winrate.png", dpi=150, bbox_inches='tight')
    

def chart_positional_jumpball_winrate(df):
    """
    Display a table of jumpball win rates across different positions.
    Aggregated across all seasons. Shows % of total jumpballs and winrate for each matchup.
    """

    start_jumpballs = df.copy()

    # Define position matchups
    matchups = {
        'GvG': ('G', 'G'),
        'GvF': ('G', 'F'),
        'GvC': ('G', 'C'),
        'FvF': ('F', 'F'),
        'FvC': ('F', 'C'),
        'CvC': ('C', 'C')
    }

    position_mapping = {
        'G': {'PG', 'SG', 'G'},
        'F': {'SF', 'PF', 'F'},
        'C': {'C'}
    }
    
    # Reverse mapping: from individual position to category
    position_to_category = {}
    for category, positions in position_mapping.items():
        for pos in positions:
            position_to_category[pos] = category

    results = []
    total_jumpballs = 0
    
    for label, (pos1, pos2) in matchups.items():
        matchup_data = start_jumpballs[
            ((start_jumpballs['athlete_position_1'].isin(position_mapping[pos1])) & (start_jumpballs['athlete_position_2'].isin(position_mapping[pos2]))) |
            ((start_jumpballs['athlete_position_1'].isin(position_mapping[pos2])) & (start_jumpballs['athlete_position_2'].isin(position_mapping[pos1])))
        ]
        
        # Filter out rows where jumpball_winner_pos is null
        matchup_data = matchup_data.dropna(subset=['jumpball_winner_pos'])
        
        # Map winner positions to categories
        matchup_data = matchup_data.copy()
        matchup_data['winner_position_category'] = matchup_data['jumpball_winner_pos'].map(position_to_category)
        
        total = len(matchup_data)
        total_jumpballs += total
        
        # Count how many times position_1 won
        pos1_wins = (matchup_data['winner_position_category'] == pos1).sum()
        winrate = pos1_wins / total if total > 0 else 0
        
        results.append({
            'matchup': label,
            'count': total,
            'pos1_wins': pos1_wins,
            'winrate': winrate
        })

    results_df = pd.DataFrame(results)
    results_df['pct_of_total'] = (results_df['count'] / total_jumpballs * 100).round(1)
    results_df['winrate_pct'] = (results_df['winrate'] * 100).round(1)
    
    # Create table image
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare table data
    table_data = []
    table_data.append(['Matchup', 'Count', '% of Total', 'Winrate %'])
    for _, row in results_df.iterrows():
        matchup = row['matchup']
        # Show dashes for same-position matchups
        if matchup in ['GvG', 'FvF', 'CvC']:
            winrate_display = "--"
        else:
            winrate_display = f"{row['winrate_pct']:.1f}"
        table_data.append([
            matchup,
            str(row['count']),
            f"{row['pct_of_total']:.1f}",
            winrate_display
        ])
    
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.2, 0.2, 0.2, 0.2])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style data rows with alternating colors
    for i in range(1, len(table_data)):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
            else:
                table[(i, j)].set_facecolor('#ffffff')
    
    plt.title('Positional Jumpball Analysis (Aggregated Across All Seasons)', 
              fontsize=14, weight='bold', pad=20)
    plt.savefig("data/positional_jumpball_winrate.png", dpi=150, bbox_inches='tight')
    print("\nTable saved to data/positional_jumpball_winrate.png")


def scatterplot_jumpball_leverage(df):
    """
    Create a scatter plot of time (x) vs margin (y) for each jumpball event. The hue of the scatter plot should be the wp_leverage
    Uses aggregated bins with dot size representing density.
    """
    start_mask = df['jumpball_type'].isin(["in-game"])
    data = df[start_mask].copy()

    # Create bins for aggregation
    data['time_bin'] = pd.cut(data['time_elapsed'], bins=48)
    data['margin_bin'] = pd.cut(data['score_diff'], bins=30)
    
    # Aggregate: count points in each bin and calculate mean wp_leverage
    aggregated = data.groupby(['time_bin', 'margin_bin']).agg({
        'wp_leverage': 'mean',
        'time_elapsed': 'mean',
        'score_diff': 'mean'
    }).reset_index()
    
    # Count points per bin
    counts = data.groupby(['time_bin', 'margin_bin']).size().reset_index(name='count')
    aggregated = aggregated.merge(counts, on=['time_bin', 'margin_bin'])

    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(aggregated['time_elapsed'], aggregated['score_diff'], 
                         s=aggregated['count']*2, c=aggregated['wp_leverage'],
                         alpha=0.6, edgecolors='black', linewidth=0.5)
    plt.title('In-Game Jumpball Leverage (Aggregated by Density)')
    plt.xlabel('Time Elapsed (seconds)')
    plt.ylabel('Score Differential')
    
    # Add quarter boundary lines
    for t in [0, 720, 1440, 2160, 2880]:
        plt.axvline(x=t, color='gray', linestyle=':', linewidth=0.8, alpha=0.7)
    
    cbar = plt.colorbar(scatter)
    cbar.set_label('WP Leverage')
    plt.tight_layout()
    plt.savefig("data/jumpball_leverage.png", dpi=150, bbox_inches='tight')


def chart_tipoff_leverages(df):
    """
    PNG Table with only two values: the average wp_leverage for start-of-game jumpballs and the average wp_leverage for start-of-ot jumpballs.
    """
    start_game_mask = df['jumpball_type'] == "start-of-game"
    start_ot_mask = df['jumpball_type'] == "start-of-ot"

    start_game_leverage = str(round(df[start_game_mask]['wp_leverage'].mean()*100, 2))+" %"
    start_ot_leverage = str(round(df[start_ot_mask]['wp_leverage'].mean()*100, 2))+" %"

    leverage_table = pd.DataFrame({
        'Jumpball Type': ['Start of Game', 'Start of OT'],
        'WP Leverage': [start_game_leverage, start_ot_leverage]
    })

    # Create table image
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(cellText=leverage_table.values, colLabels=leverage_table.columns, 
                     cellLoc='center', loc='center', colWidths=[0.3, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 2.5)
    
    # Style header row
    for i in range(len(leverage_table.columns)):
        table[(0, i)].set_facecolor('#2C3E50')
        table[(0, i)].set_text_props(weight='bold', color='white', size=13)
        table[(0, i)].set_height(0.16)
    
    # Style data rows with alternating colors and borders
    for i in range(1, len(leverage_table) + 1):
        for j in range(len(leverage_table.columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ECF0F1')
            else:
                table[(i, j)].set_facecolor('#FFFFFF')
            table[(i, j)].set_edgecolor('#BDC3C7')
            table[(i, j)].set_linewidth(0.25)
            table[(i, j)].set_height(0.16)
    
    # Set header border
    for i in range(len(leverage_table.columns)):
        table[(0, i)].set_edgecolor('#1A252F')
        table[(0, i)].set_linewidth(1.5)

    plt.title('Jumpball Leverage', fontsize=15, weight='bold', pad=20)
    plt.savefig("data/tipoff_leverages.png", dpi=150, bbox_inches='tight')
    print("\nTable saved to data/tipoff_leverages.png")


def main():
    df = pd.read_csv("data/filtered-jumpballs.csv")


    # plot_jumpballs_per_game_per_season(df)
    # chart_team_jumpball_player_variance(df)
    # chart_team_jumpball_winrate(df)
    # chart_positional_jumpball_winrate(df)
    # scatterplot_jumpball_leverage(df)
    chart_tipoff_leverages(df)


if __name__ == "__main__":
    main()