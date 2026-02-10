import pandas as pd
import streamlit as st
from nba_api.stats.endpoints import TeamGameLogs
from nba_api.stats.endpoints import ShotChartDetail
from nba_api.stats.endpoints import LeagueStandings
from nba_api.stats.endpoints import TeamDashLineups
from nba_api.stats.endpoints import TeamPlayerDashboard
from nba_api.stats.endpoints import LeagueDashTeamStats
from nba_api.stats.static import teams

@st.cache_data
def ovr_rating(team_id):
    standings = LeagueDashTeamStats( team_id_nullable=team_id, season='2025-26', measure_type_detailed_defense="Advanced")
    standings_df=standings.get_data_frames()[0]
    return standings_df[['OFF_RATING',"DEF_RATING","NET_RATING"]]

@st.cache_data
#Calculates rolling net efficiency from advanced stats endpoint
def get_rolling_efficiency(team_id, season='2025-26', window=5):
    log = TeamGameLogs(team_id_nullable=team_id, season_nullable=season, measure_type_player_game_logs_nullable="Advanced")
    df = log.get_data_frames()[0]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    df = df.sort_values('GAME_DATE')
    df['ROLLING_NET_RTG'] = df['NET_RATING'].rolling(window=window).mean()
    return df[['GAME_DATE', 'NET_RATING', 'ROLLING_NET_RTG']]

@st.cache_data
def get_team_shot_data(team_id):
    gameshots = ShotChartDetail(team_id=team_id, player_id=0,context_measure_simple='FGA',season_nullable='2025-26')
    gameshots_df = gameshots.get_data_frames()[0]
    missed = gameshots_df[gameshots_df["SHOT_MADE_FLAG"] == 0]
    made = gameshots_df[gameshots_df["SHOT_MADE_FLAG"] == 1]
    return made, missed

@st.cache_data
def league_standings_data(team_id):
    standings = LeagueStandings(season='2025-26')
    standings_df=standings.get_data_frames()[0]
    team_stats = standings_df[standings_df['TeamID'] == team_id] 
    return team_stats[['Record', 'PlayoffRank']]


@st.cache_data
def get_lineup (team_id):
    lineup = TeamDashLineups(team_id=team_id, group_quantity=5, season='2025-26')
    lineup_df = lineup.get_data_frames()[1]
    lineup_df = lineup_df.sort_values(by='PLUS_MINUS', ascending=False)
    return lineup_df[["PLUS_MINUS", "GROUP_NAME", 'MIN']]

@st.cache_data
def get_recent_scores(team_id):
    games = TeamGameLogs(season_nullable="2025-26", team_id_nullable=team_id, measure_type_player_game_logs_nullable='Base')
    games_df = games.get_data_frames()[0]
    games_df["GAME_DATE"] = pd.to_datetime(games_df["GAME_DATE"])
    games_df["GAME_DATE"] = games_df["GAME_DATE"].dt.strftime("%m/%d")
    games_df["oppscore"] = games_df['PTS'] - games_df["PLUS_MINUS"]
    return games_df[['PTS','oppscore','GAME_DATE','WL']].head(10).iloc[::-1]

@st.cache_data
def get_player_stats(team_id):
    playerstats = TeamPlayerDashboard(season="2025-26", team_id=team_id)
    playerstats_df = playerstats.get_data_frames()[1]
    return playerstats_df[['PTS','REB','AST','STL','BLK','FG_PCT','FG3_PCT','TOV',"PLAYER_NAME"]]

@st.cache_data
def get_rank():
    ranking = LeagueStandings(season="2025-26")
    overall = ranking.get_data_frames()[0]
    west=overall[overall["Conference"] == "West"]
    east=overall[overall["Conference"] == "East"]
    return overall, west, east

@st.cache_data
def get_advanced_player_stats(team_id):
    stats = TeamPlayerDashboard(season="2025-26", team_id=team_id, measure_type_detailed_defense='Advanced')
    stats_df = stats.get_data_frames()[1]
    return stats_df[['PLAYER_NAME','GP','USG_PCT','TS_PCT']]


