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
    



def main():
    df = pd.read_csv("data/filtered-jumpballs.csv")


    # plot_jumpballs_per_game_per_season(df)
    # chart_team_jumpball_player_variance(df)
    chart_team_jumpball_winrate(df)


if __name__ == "__main__":
    main()