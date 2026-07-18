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
    Chart the proportion of the number of jumpball events that go to top 1 player and top 3 players in a season, considering start-game and start-ot only.

    Returns: Color coded table with teams on the left, season on the top, and the proportion of jumpball events that go to top 1 player and top 3 players in a season.
    """

    #next commit
    



def main():
    df = pd.read_csv("data/filtered-jumpballs.csv")


    plot_jumpballs_per_game_per_season(df)


if __name__ == "__main__":
    main()