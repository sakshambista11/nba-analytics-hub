# NBA Analytics Hub 🏀

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?logo=streamlit)](https://nba-analytics-app.streamlit.app/)

A real-time NBA team analytics dashboard that goes beyond the box score — visualizing shot quality, lineup efficiency, and schedule fatigue for all 30 teams, pulled live from the NBA Stats API.

## Project Overview
Built on a **Single-Template Architecture**: one master layout programmatically generates 30 unique, team-branded dashboards. Selecting a team re-fetches live data and re-renders every chart — standings, shot charts, lineup plus/minus, and scoring trends — with that team's colors applied throughout.

## Features
- **Dynamic Shot Charts** — Made/missed field goal attempts mapped onto a custom-drawn NBA half-court using Plotly Graph Objects
- **Advanced Efficiency Metrics** — Offensive, defensive, and net rating pulled from `LeagueDashTeamStats`
- **Schedule Intelligence** — Automatically detects the next back-to-back game pair for any team
- **Lineup Analysis** — Top 5-man lineups ranked by plus/minus via `TeamDashLineups`
- **Player Explorer** — Per-game stats (PTS/REB/AST/STL/BLK/FG%) for every player on the roster
- **Live Standings** — Current record and playoff seed updated each session

## Tech Stack
| Layer | Tool |
|---|---|
| Language | Python 3.13.1 |
| Framework | Streamlit |
| Data Source | `nba_api` (NBA Stats endpoints) |
| Visualization | Plotly Graph Objects |
| Data Processing | Pandas |

## How to Run
> Note: The NBA Stats API can be slow on first load — expect 5–10 seconds per team selection.

```bash
git clone https://github.com/sakshambista11/nba-analytics-hub.git
cd nba-analytics-hub
pip install -r requirements.txt
streamlit run app.py
```

> ⚠️ Run `streamlit run app.py` from the project root directory.

## Roadmap
- [ ] Rolling net efficiency trend chart (data pipeline already built)
- [ ] Conference standings split view
- [ ] Advanced player efficiency metrics (USG%, TS%)

---
*Saksham Bista — University of Texas at Austin, Statistics & Data Sciences, Class of 2029*