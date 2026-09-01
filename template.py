import streamlit as st
from data_fetcher import league_standings_data, ovr_rating, get_recent_scores, get_team_shot_data, get_lineup, get_player_stats, get_next_back_to_back
import plotly.graph_objects as go

def draw_court(fig):
    """
    Draws NBA half-court lines and markings onto a Plotly figure.

    Args:
        fig (go.Figure): Plotly figure to draw the court on.
        Court coordinates match the NBA Stats API LOC_X / LOC_Y scale.
    """
    
    court_shapes = [
        # 1. Outer Court Boundary (Half Court)
        dict(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2)),
        
        # 2. The Paint (Key) - Outer Box
        dict(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2)),
        
        # 3. The Paint (Key) - Inner Box (The Restricted Area mostly)
        dict(type="rect", x0=-60, y0=-47.5, x1=60, y1=142.5, line=dict(color="white", width=2)),

        # 4. Backboard
        dict(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line=dict(color="white", width=2)),

        # 5. Hoop (Circle)
        dict(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line=dict(color="orange", width=2)),
        
        # 6. Restricted Area Arc
        dict(type="path",
             path="M -40,-7.5 C -40,50 40,50 40,-7.5",
             line=dict(color="white", width=2)),
             
        # 7. Free Throw Circle (Top Half)
        dict(type="path",
             path="M -60,142.5 C -60,200 60,200 60,142.5",
             line=dict(color="white", width=2)),
             
        # 8. Free Throw Circle (Bottom Half - Dashed)
        dict(type="path",
             path="M -60,142.5 C -60,85 60,85 60,142.5",
             line=dict(color="white", width=2, dash='dot')),

        # 9. Corner 3-Point Lines (Straight parts)
        dict(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line=dict(color="white", width=2)),
        dict(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line=dict(color="white", width=2)),

        # 10. 3-Point Arc (Curved part)
        dict(type="path",
             path="M -220,92.5 C -220,300 220,300 220,92.5",
             line=dict(color="white", width=2)),
             
        # 11. Center Court Circle (Bottom part visible in half court)
        dict(type="path",
             path="M -60,422.5 C -60,360 60,360 60,422.5",
             line=dict(color="white", width=2)),
    ]
    
    fig.update_layout(shapes=court_shapes)
    
    # Fix the aspect ratio so the court doesn't look stretched
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)


def render_dashboard(
    team_id,
    team_name,
    primary_color,
    secondary_color,
    schedule_season,
    analytics_season,
):
    """
    Renders the full team dashboard including standings, shot chart,
    recent scores, lineup analysis, and player stats.

    Args:
        team_id (int): NBA Stats team ID.
        team_name (str): Full team name (e.g., 'Dallas Mavericks').
        primary_color (str): Team primary hex color for chart theming.
        secondary_color (str): Team secondary hex color for chart theming.
        schedule_season (str): Season used for upcoming games.
        analytics_season (str): Season used for team and player statistics.
    """
    
    back_to_back, back_to_back_status = get_next_back_to_back(
        team_id, schedule_season
    )
    playerstat = get_player_stats(team_id, analytics_season)
    standings = league_standings_data(team_id, analytics_season)
    lineup = get_lineup(team_id, analytics_season)
    rating = ovr_rating(team_id, analytics_season)
    record = standings["Record"].iloc[0] if not standings.empty else "—"
    rank = standings["PlayoffRank"].iloc[0] if not standings.empty else None
    rank_label = f"#{rank}" if rank is not None else "—"
    if back_to_back_status == "found":
        firstdate = back_to_back["Date"].dt.strftime("%m/%d").values[0]
        seconddate = back_to_back["Date"].dt.strftime("%m/%d").values[1]
        back_to_back_date = f'{firstdate} — {seconddate}'
    elif back_to_back_status == "season_complete":
        back_to_back_date = "Season complete"
    elif back_to_back_status == "no_back_to_back":
        back_to_back_date = "None remaining"
    else:
        back_to_back_date = "Schedule unavailable"
    netrating = rating["NET_RATING"].iloc[0] if not rating.empty else "—"
    recent_games = get_recent_scores(team_id, analytics_season)
    made, miss = get_team_shot_data(team_id, analytics_season)
    
    
    #Title/header
    title_col, lineup_col, card_col = st.columns([1, 2, 1.7], vertical_alignment="center")

    with title_col:

        st.markdown("#### NBA Analytics Hub")

        st.markdown(f"# {team_name}")

    with lineup_col:
        if lineup.empty:
            st.info("Lineup data will appear after the season begins.")
        else:
            st.table(lineup[["Plus Minus", "Line up"]].head(3), border="horizontal")

    with card_col:
        with st.container(border=True):
            st.markdown("**Team Overview**")
            record_col, rank_col = st.columns(2)
            b2b_col, rating_col = st.columns(2)
            record_col.metric("Record", record)
            rank_col.metric("Rank", rank_label)
            b2b_col.metric("Next Back to Back", back_to_back_date)
            rating_col.metric("Net Rating", netrating)

    # Main Dashboard - 3 Column Layout
    left_col, center_col = st.columns([1, 1])

    with left_col:
        st.markdown("**Last 10 Games**",text_alignment="center")
        if recent_games.empty:
            st.info("Game results will appear after the season begins.")
        else:
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x = recent_games['GAME_DATE'],
                y = recent_games['PTS'],
                name = 'Team Score',
                marker_color = primary_color
            ))

            fig.add_trace(go.Bar(
                x = recent_games['GAME_DATE'],
                y = recent_games['oppscore'],
                name ='Opponent Score',
                marker_color = '#888888'
            ))

            fig.update_layout(
                barmode = 'group',
                xaxis_title = 'Date',
                yaxis_title = 'Points',
                height = 420,
                showlegend = True
            )

            st.plotly_chart(fig, width="stretch")
    
    with center_col:
        st.markdown("**Shot Map**", text_alignment="center")
        if made.empty and miss.empty:
            st.info("Shot data will appear after the season begins.")
        else:
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x = made["LOC_X"],
                    y = made["LOC_Y"],
                    mode="markers",
                    name="Made",
                    marker = dict(color=primary_color,opacity=0.5, line = dict(color = "white", width = 0.5))
                )
            )

            fig.add_trace(
                go.Scatter(
                    x = miss["LOC_X"],
                    y = miss["LOC_Y"],
                    mode="markers",
                    name="Miss",
                    marker=dict(symbol='star',color=secondary_color,opacity=0.5)
                )
            )
            draw_court(fig)

            st.plotly_chart(fig, width="stretch")

    player_col, _right_col = st.columns([1,1])

    with player_col:
        if playerstat.empty:
            st.markdown("**Player Explorer**")
            st.info("Player statistics will appear after the season begins.")
        else:
            option = st.selectbox(
                "**Player Explorer**",
                playerstat["Player"].tolist()
            )

            st.table(playerstat.loc[playerstat["Player"] == option],border="horizontal")
