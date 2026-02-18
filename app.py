import streamlit as st
from team_config import team
from template import render_dashboard

st.set_page_config(page_title="NBA 360° Analytics Hub", layout="wide")

# Sidebar - Team Selection
st.sidebar.header("Select Team")

# Create a list of team names for the dropdown
team_names = [team[abbrev]['name'] for abbrev in team.keys()]

# Let user select a team
selected_team_name = st.sidebar.selectbox(
    "Choose a team:",
    team_names
)

selected_team_id = next(team[abbrev]['id'] for abbrev in team if team[abbrev]['name']==selected_team_name)
selected_team_primary = next(team[abbrev]["primary"] for abbrev in team if team[abbrev]['name']==selected_team_name)
selected_team_secondary = next(team[abbrev]["secondary"] for abbrev in team if team[abbrev]['name']==selected_team_name)

render_dashboard(selected_team_id, selected_team_name, selected_team_primary, selected_team_secondary)