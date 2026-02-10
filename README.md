# NBA Analytics Hub 🏀

**Status:** 🚧 Work in Progress (Active Development)

A Python-based interactive dashboard designed to visualize real-time NBA team performance, shot charts, and advanced efficiency metrics using the NBA API.

## Project Overview
This tool allows users to analyze NBA teams beyond basic box scores. Built on a **Single-Template Architecture**, the app uses one master layout to programmatically generate 30 unique, team-branded dashboards. By leveraging the `nba_api`, it fetches live season data to generate spatial visualizations of shot locations and track team efficiency over time.

## Key Features (Implemented)
* **Dynamic Shot Charts:** Visualizes made/missed shots mapped onto a custom-drawn plotting of an NBA court using Plotly.
* **Advanced Metrics:** Calculates and displays Rolling Net Efficiency and Team Ratings using data from `LeagueDashTeamStats`.
* **Live Data Integration:** Fetches real-time game logs and standings directly from NBA stats endpoints.
* **Interactive UI:** Built with Streamlit for seamless team selection and data filtering.

## Roadmap (Upcoming Features)
* **Player Explorer Module:** Developing a deep-dive interactive element to analyze individual player usage vs. efficiency.
* **Advanced Trend Toggles:** Implementing UI toggles to switch between raw scoring trends and rolling net rating views.
* **Context Logic:** Adding logic to identify and flag "Back-to-Back" schedule disadvantages for upcoming games.

## Tech Stack
* **Language:** Python 3.x
* **Framework:** Streamlit
* **Data Source:** NBA API (`nba_api`)
* **Visualization:** Plotly Graph Objects
* **Data Manipulation:** Pandas

## How to Run
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`

---
*Created by [Saksham Bista] - University of Texas at Austin, Class of 2029*