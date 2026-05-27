from nba_api.stats.library.http import NBAStatsHTTP
from pathlib import Path

CURRENT_SEASON = "2025-26"

NBAStatsHTTP.headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
}
import pandas as pd
from datetime import date
import streamlit as st
from nba_api.stats.endpoints import TeamGameLogs
from nba_api.stats.endpoints import ShotChartDetail
from nba_api.stats.endpoints import LeagueStandings
from nba_api.stats.endpoints import TeamDashLineups
from nba_api.stats.endpoints import TeamPlayerDashboard
from nba_api.stats.endpoints import LeagueDashTeamStats


@st.cache_data
def get_next_back_to_back(team):
    """
    Finds the next back-to-back game pair for a given team.

    Args:
        team (str): Full team name (e.g., 'Dallas Mavericks').

    Returns:
        pd.DataFrame: Two-row DataFrame with the back-to-back games,
                      or None if no upcoming back-to-backs exist.
    """
    schedule_df = pd.read_csv(Path(__file__).parent / "nbaschedule.csv")
    schedule_df["Date"] = pd.to_datetime(schedule_df["Date"], format="%d/%m/%Y %H:%M").dt.tz_localize('UTC').dt.tz_convert('America/Chicago')
    team_games = schedule_df[(schedule_df["Home Team"] == team) | (schedule_df["Away Team"] == team)].copy()
    today = pd.Timestamp(date.today(), tz='America/Chicago')
    upcoming = team_games[team_games["Date"] >= today].sort_values("Date").reset_index(drop=True)
    if upcoming.empty:
        st.warning(f"No upcoming games found for '{team}'.")
        return None
    upcoming["_game_date"] = upcoming["Date"].dt.date
    for i in range(len(upcoming) - 1):
        day_a = upcoming.loc[i, "_game_date"]
        day_b = upcoming.loc[i + 1, "_game_date"]
        if (day_b - day_a).days == 1:
            return upcoming.loc[[i, i + 1]].drop(columns="_game_date").reset_index(drop=True)
    st.warning(f"No upcoming back-to-backs found for '{team}'.")
    return None



@st.cache_data
def ovr_rating(team_id):
    """
    Fetches offensive, defensive, and net rating for a team.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        pd.DataFrame: Single-row DataFrame with OFF_RATING, DEF_RATING, NET_RATING.
    """
    standings = LeagueDashTeamStats( team_id_nullable=team_id, season=CURRENT_SEASON, measure_type_detailed_defense="Advanced")
    standings_df=standings.get_data_frames()[0]
    return standings_df[['OFF_RATING',"DEF_RATING","NET_RATING"]]



@st.cache_data
def get_team_shot_data(team_id):
    """
    Fetches all field goal attempts for a team and splits by outcome.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (made_shots, missed_shots),
        each with full ShotChartDetail columns including LOC_X and LOC_Y.
    """
    gameshots = ShotChartDetail(team_id=team_id, player_id=0,context_measure_simple='FGA',season_nullable=CURRENT_SEASON)
    gameshots_df = gameshots.get_data_frames()[0]
    missed = gameshots_df[gameshots_df["SHOT_MADE_FLAG"] == 0]
    made = gameshots_df[gameshots_df["SHOT_MADE_FLAG"] == 1]
    return made, missed

@st.cache_data
def league_standings_data(team_id):
    """
    Fetches a team's current record and playoff seeding.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        pd.DataFrame: Single-row DataFrame with 'Record' and 'PlayoffRank'.
    """
    standings = LeagueStandings(season=CURRENT_SEASON)
    standings_df=standings.get_data_frames()[0]
    team_stats = standings_df[standings_df['TeamID'] == team_id] 
    return team_stats[['Record', 'PlayoffRank']]


@st.cache_data
def get_lineup(team_id):
    """
    Fetches the top 5-man lineups for a team, sorted by plus/minus.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        pd.DataFrame: Columns ['Plus Minus', 'Line up', 'MIN'],
                      sorted descending by plus/minus.
    """
    lineup = TeamDashLineups(team_id=team_id, group_quantity=5, season=CURRENT_SEASON)
    lineup_df = lineup.get_data_frames()[1]
    lineup_df = lineup_df.sort_values(by='PLUS_MINUS', ascending=False).reset_index()
    lineup_df["Plus Minus"] = lineup_df['PLUS_MINUS'].astype(int)
    lineup_df["Line up"] = lineup_df['GROUP_NAME']
    return lineup_df[["Plus Minus", "Line up", 'MIN']]


@st.cache_data
def get_recent_scores(team_id):
    """
    Fetches the last 10 game scores for a team in chronological order.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        pd.DataFrame: Columns ['PTS', 'oppscore', 'GAME_DATE', 'WL'],
                      oldest to newest (reversed for charting).
    """
    games = TeamGameLogs(season_nullable=CURRENT_SEASON, team_id_nullable=team_id, measure_type_player_game_logs_nullable='Base')
    games_df = games.get_data_frames()[0]
    games_df["GAME_DATE"] = pd.to_datetime(games_df["GAME_DATE"])
    games_df["GAME_DATE"] = games_df["GAME_DATE"].dt.strftime("%m/%d")
    games_df["oppscore"] = games_df['PTS'] - games_df["PLUS_MINUS"]
    return games_df[['PTS','oppscore','GAME_DATE','WL']].head(10).iloc[::-1]

@st.cache_data
def get_player_stats(team_id):
    """
    Fetches per-game stats for all players on a team's roster.

    Args:
        team_id (int): NBA Stats team ID.

    Returns:
        pd.DataFrame: Columns ['Player', 'PTS', 'REB', 'AST', 'STL',
                      'BLK', 'FG_PCT', 'FG3_PCT', 'TOV'].
    """
    playerstats = TeamPlayerDashboard(season=CURRENT_SEASON, team_id=team_id, per_mode_detailed="PerGame")
    playerstats_df = playerstats.get_data_frames()[1]
    playerstats_df["Player"] = playerstats_df["PLAYER_NAME"]
    return playerstats_df[["Player",'PTS','REB','AST','STL','BLK','FG_PCT','FG3_PCT','TOV']]




