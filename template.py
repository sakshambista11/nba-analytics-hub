import streamlit as st
from data_fetcher import league_standings_data, ovr_rating, get_recent_scores, get_team_shot_data
import plotly.graph_objects as go

def draw_court(fig):
    # Court dimensions (in feet, scaled by 10 for NBA API units)
    # Hoop is at (0,0) usually, but visual needs to match data coordinates
    
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


def render_dashboard(team_id, team_name, primary_color, secondary_color):
    
    # Get standings data
    standings = league_standings_data(team_id)
    rating = ovr_rating(team_id)
    record = standings['Record'].values[0]
    rank = standings['PlayoffRank'].values[0]
    netrating = rating["NET_RATING"]
    recent_games = get_recent_scores(team_id)
    made, miss = get_team_shot_data(team_id)
    madeX = made["LOC_X"]
    madeY = made["LOC_Y"]
    missX = miss["LOC_X"]
    missY = miss["LOC_Y"]
    
    
        # Header row: Title on the left, overview "card" on the right
    title_col, card_col = st.columns([2.2, 1.4], vertical_alignment="center")

    with title_col:
        # Smaller, more resume-friendly title
        st.markdown("#### NBA Analytics Hub")

        # BIG team name (this becomes the “hero” text)
        st.markdown(f"# {team_name}")


    with card_col:
        with st.container(border=True):
            st.markdown("**Team Overview**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Record", record)
            m2.metric("Rank", f"#{rank}")
            m3.metric("Net Rating", netrating)

    # Main Dashboard - 3 Column Layout
    left_col, center_col, right_col = st.columns([3, 2, 1.2])

    with left_col:
        
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
            barmode = 'group',                # Side-by-side bars
            xaxis_title = 'Date',
            yaxis_title = 'Points',
            height = 420,                     # Chart height in pixels
            showlegend = True
        )

        st.plotly_chart(fig, use_container_width=True)
    
    with center_col:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x = madeX,
                y = madeY,
                mode="markers",
                name="Made",
                marker = dict(color=primary_color,opacity=0.5, line = dict(color = "white", width = 0.5))
            )
        )

        fig.add_trace(
            go.Scatter(
                x = missX,
                y = missY,
                mode="markers",
                name="Miss",
                marker=dict(symbol='star',color=secondary_color,opacity=0.5)
            )
        )
        draw_court(fig)

        st.plotly_chart(fig, use_container_width=True)

        
    
    with right_col:
        pass