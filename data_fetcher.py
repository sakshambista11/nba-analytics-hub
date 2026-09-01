import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from nba_api.stats.endpoints import (
    LeagueDashTeamStats,
    LeagueStandings,
    ScheduleLeagueV2,
    ShotChartDetail,
    TeamDashLineups,
    TeamGameLogs,
    TeamPlayerDashboard,
)


CENTRAL_TIMEZONE = ZoneInfo("America/Chicago")
SCHEDULE_CACHE_TTL_SECONDS = 24 * 60 * 60
STATS_CACHE_TTL_SECONDS = 60 * 60
logger = logging.getLogger(__name__)


def get_current_season(as_of=None):
    """Return the NBA season label active on a given Central Time date."""
    if as_of is None:
        current_date = datetime.now(CENTRAL_TIMEZONE).date()
    elif isinstance(as_of, datetime):
        if as_of.tzinfo is not None:
            as_of = as_of.astimezone(CENTRAL_TIMEZONE)
        current_date = as_of.date()
    elif isinstance(as_of, date):
        current_date = as_of
    else:
        raise TypeError("as_of must be a date, datetime, or None")

    start_year = current_date.year if current_date.month >= 7 else current_date.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def get_previous_season(season):
    """Return the NBA season immediately preceding a 'YYYY-YY' label."""
    start_year = int(season.split("-")[0]) - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _select_columns(dataframe, columns):
    """Return a frame with a stable schema, including for empty API results."""
    if dataframe is None:
        return pd.DataFrame(columns=columns)
    return dataframe.reindex(columns=columns)


@st.cache_data(ttl=SCHEDULE_CACHE_TTL_SECONDS, show_spinner=False)
def get_season_schedule(season):
    """Fetch and normalize the official schedule for one NBA season."""
    schedule = ScheduleLeagueV2(season=season)
    schedule_df = schedule.get_data_frames()[0]
    schedule_df = _select_columns(
        schedule_df,
        [
            "gameDateTimeUTC",
            "gameLabel",
            "gameStatus",
            "homeTeam_teamId",
            "awayTeam_teamId",
        ],
    )
    schedule_df = schedule_df[schedule_df["gameLabel"] != "Preseason"].copy()
    schedule_df["Date"] = pd.to_datetime(
        schedule_df["gameDateTimeUTC"], errors="coerce", utc=True
    ).dt.tz_convert(CENTRAL_TIMEZONE)
    schedule_df["homeTeam_teamId"] = pd.to_numeric(
        schedule_df["homeTeam_teamId"], errors="coerce"
    )
    schedule_df["awayTeam_teamId"] = pd.to_numeric(
        schedule_df["awayTeam_teamId"], errors="coerce"
    )
    schedule_df["gameStatus"] = pd.to_numeric(
        schedule_df["gameStatus"], errors="coerce"
    )
    return schedule_df.dropna(subset=["Date"])


def _find_next_back_to_back(schedule_df, team_id, as_of=None):
    """Find a team's next back-to-back in an already normalized schedule."""
    if schedule_df.empty:
        return pd.DataFrame(columns=schedule_df.columns), "schedule_unavailable"

    team_games = schedule_df[
        (schedule_df["homeTeam_teamId"] == team_id)
        | (schedule_df["awayTeam_teamId"] == team_id)
    ].copy()
    if team_games.empty:
        return team_games, "schedule_unavailable"

    if as_of is None:
        current_time = pd.Timestamp.now(tz=CENTRAL_TIMEZONE)
    else:
        current_time = pd.Timestamp(as_of)
        if current_time.tzinfo is None:
            current_time = current_time.tz_localize(CENTRAL_TIMEZONE)
        else:
            current_time = current_time.tz_convert(CENTRAL_TIMEZONE)

    if "gameStatus" in team_games.columns:
        game_status = pd.to_numeric(team_games["gameStatus"], errors="coerce")
    else:
        game_status = pd.Series(pd.NA, index=team_games.index, dtype="Int64")
    not_completed = game_status.ne(3).fillna(True)
    in_progress = game_status.eq(2).fillna(False)
    upcoming_mask = not_completed & (
        (team_games["Date"] >= current_time) | in_progress
    )
    upcoming = team_games[upcoming_mask].sort_values("Date").reset_index(drop=True)
    if upcoming.empty:
        return upcoming, "season_complete"

    game_dates = upcoming["Date"].dt.date
    for index in range(len(upcoming) - 1):
        if (game_dates.iloc[index + 1] - game_dates.iloc[index]).days == 1:
            return upcoming.iloc[[index, index + 1]].reset_index(drop=True), "found"

    return upcoming.iloc[0:0], "no_back_to_back"


def get_next_back_to_back(team_id, season):
    """Return the next back-to-back games and a display status."""
    try:
        schedule_df = get_season_schedule(season)
    except Exception as exc:  # Keep schedule outages isolated from the dashboard.
        logger.warning("Unable to load the %s NBA schedule: %s", season, exc)
        return pd.DataFrame(), "schedule_unavailable"
    return _find_next_back_to_back(schedule_df, team_id)


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS, show_spinner=False)
def get_team_game_logs(team_id, season):
    """Fetch a team's completed regular-season game logs."""
    return TeamGameLogs(
        season_nullable=season,
        team_id_nullable=team_id,
        measure_type_player_game_logs_nullable="Base",
    ).get_data_frames()[0]


def get_analytics_season(team_id, schedule_season):
    """Use the new season once a team has completed a regular-season game."""
    try:
        current_logs = get_team_game_logs(team_id, schedule_season)
    except Exception as exc:
        logger.warning(
            "Unable to determine analytics season for team %s: %s",
            team_id,
            exc,
        )
        return get_previous_season(schedule_season)
    if current_logs.empty:
        return get_previous_season(schedule_season)
    return schedule_season


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS)
def ovr_rating(team_id, season):
    """Fetch offensive, defensive, and net rating for a team."""
    stats = LeagueDashTeamStats(
        team_id_nullable=team_id,
        season=season,
        measure_type_detailed_defense="Advanced",
    ).get_data_frames()[0]
    return _select_columns(stats, ["OFF_RATING", "DEF_RATING", "NET_RATING"])


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS)
def get_team_shot_data(team_id, season):
    """Fetch all field goal attempts for a team and split by outcome."""
    shots = ShotChartDetail(
        team_id=team_id,
        player_id=0,
        context_measure_simple="FGA",
        season_nullable=season,
    ).get_data_frames()[0]
    shots = _select_columns(shots, ["SHOT_MADE_FLAG", "LOC_X", "LOC_Y"])
    return shots[shots["SHOT_MADE_FLAG"] == 1], shots[shots["SHOT_MADE_FLAG"] == 0]


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS)
def league_standings_data(team_id, season):
    """Fetch a team's current record and playoff seeding."""
    standings = LeagueStandings(season=season).get_data_frames()[0]
    if standings.empty or "TeamID" not in standings.columns:
        return pd.DataFrame(columns=["Record", "PlayoffRank"])
    team_stats = standings[standings["TeamID"] == team_id]
    return _select_columns(team_stats, ["Record", "PlayoffRank"])


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS)
def get_lineup(team_id, season):
    """Fetch the top five-player lineups for a team."""
    lineup = TeamDashLineups(
        team_id=team_id,
        group_quantity=5,
        season=season,
    ).get_data_frames()[1]
    if lineup.empty:
        return pd.DataFrame(columns=["Plus Minus", "Line up", "MIN"])
    lineup = _select_columns(lineup, ["PLUS_MINUS", "GROUP_NAME", "MIN"])
    lineup = lineup.sort_values(by="PLUS_MINUS", ascending=False).reset_index(drop=True)
    lineup["Plus Minus"] = pd.to_numeric(lineup["PLUS_MINUS"], errors="coerce").astype("Int64")
    lineup["Line up"] = lineup["GROUP_NAME"]
    return lineup[["Plus Minus", "Line up", "MIN"]]


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS)
def get_recent_scores(team_id, season):
    """Fetch the last ten game scores for a team in chronological order."""
    games = get_team_game_logs(team_id, season).copy()
    if games.empty:
        return pd.DataFrame(columns=["PTS", "oppscore", "GAME_DATE", "WL"])
    games = _select_columns(games, ["PTS", "PLUS_MINUS", "GAME_DATE", "WL"])
    games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"], errors="coerce").dt.strftime("%m/%d")
    games["oppscore"] = games["PTS"] - games["PLUS_MINUS"]
    return games[["PTS", "oppscore", "GAME_DATE", "WL"]].head(10).iloc[::-1]


@st.cache_data(ttl=STATS_CACHE_TTL_SECONDS)
def get_player_stats(team_id, season):
    """Fetch per-game stats for every player on a team's roster."""
    players = TeamPlayerDashboard(
        season=season,
        team_id=team_id,
        per_mode_detailed="PerGame",
    ).get_data_frames()[1]
    output_columns = ["Player", "PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "TOV"]
    if players.empty:
        return pd.DataFrame(columns=output_columns)
    players = _select_columns(
        players,
        ["PLAYER_NAME", "PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "TOV"],
    )
    players["Player"] = players["PLAYER_NAME"]
    return players[output_columns]
