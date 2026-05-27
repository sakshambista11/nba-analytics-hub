import pandas as pd
import streamlit as st
from nba_api.stats.endpoints import TeamGameLogs, LeagueStandings, TeamPlayerDashboard

CURRENT_SEASON = "2025-26"

@st.cache_data
#Calculates rolling net efficiency from advanced stats endpoint
def get_rolling_efficiency(team_id, season='2025-26', window=5):
    """
    Calculates rolling net efficiency from advanced game logs.

    Args:
        team_id (int): NBA Stats team ID.
        season (str): Season string in 'YYYY-YY' format. Defaults to '2025-26'.
        window (int): Rolling average window size. Defaults to 5.

    Returns:
        pd.DataFrame: Columns ['GAME_DATE', 'NET_RATING', 'ROLLING_NET_RTG'],
                      sorted chronologically.
    """
    log = TeamGameLogs(team_id_nullable=team_id, season_nullable=season, measure_type_player_game_logs_nullable="Advanced")
    df = log.get_data_frames()[0]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    df = df.sort_values('GAME_DATE')
    df['ROLLING_NET_RTG'] = df['NET_RATING'].rolling(window=window).mean()
    return df[['GAME_DATE', 'NET_RATING', 'ROLLING_NET_RTG']]


@st.cache_data
def get_rank():
    """
    Fetches current league standings split by conference.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            (overall_standings, west_standings, east_standings).
    """
    ranking = LeagueStandings(season="2025-26")
    overall = ranking.get_data_frames()[0]
    west=overall[overall["Conference"] == "West"]
    east=overall[overall["Conference"] == "East"]
    return overall, west, east

@st.cache_data
def get_advanced_player_stats(team_id):
    """
    Fetches advanced efficiency metrics for all players on a team.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        pd.DataFrame: Columns ['PLAYER_NAME', 'GP', 'USG_PCT', 'TS_PCT'].
    """
    stats = TeamPlayerDashboard(season="2025-26", team_id=team_id, measure_type_detailed_defense='Advanced')
    stats_df = stats.get_data_frames()[1]
    return stats_df[['PLAYER_NAME','GP','USG_PCT','TS_PCT']]