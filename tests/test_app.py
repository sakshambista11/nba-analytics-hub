import unittest
from contextlib import ExitStack
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

import data_fetcher
import template


ATLANTA_TEAM_ID = 1610612737


class SplitSeasonAppTests(unittest.TestCase):
    def run_dashboard(self, analytics_season):
        lineup = pd.DataFrame(
            {"Plus Minus": [12], "Line up": ["A - B - C - D - E"], "MIN": [100]}
        )
        players = pd.DataFrame(
            {
                "Player": ["Test Player"],
                "PTS": [20],
                "REB": [5],
                "AST": [6],
                "STL": [1],
                "BLK": [1],
                "FG_PCT": [0.5],
                "FG3_PCT": [0.4],
                "TOV": [2],
            }
        )
        standings = pd.DataFrame({"Record": ["40-42"], "PlayoffRank": [10]})
        rating = pd.DataFrame(
            {"OFF_RATING": [112.0], "DEF_RATING": [113.2], "NET_RATING": [-1.2]}
        )
        games = pd.DataFrame(
            {"PTS": [110], "oppscore": [105], "GAME_DATE": ["04/13"], "WL": ["W"]}
        )
        made_shots = pd.DataFrame(
            {"SHOT_MADE_FLAG": [1], "LOC_X": [0], "LOC_Y": [10]}
        )
        missed_shots = pd.DataFrame(columns=["SHOT_MADE_FLAG", "LOC_X", "LOC_Y"])
        back_to_back = pd.DataFrame(
            {
                "Date": pd.to_datetime(
                    ["2026-10-23T23:00:00Z", "2026-10-25T00:00:00Z"], utc=True
                ).tz_convert(data_fetcher.CENTRAL_TIMEZONE)
            }
        )

        with ExitStack() as stack:
            mocks = {
                "current": stack.enter_context(
                    patch.object(data_fetcher, "get_current_season", return_value="2026-27")
                ),
                "analytics": stack.enter_context(
                    patch.object(
                        data_fetcher,
                        "get_analytics_season",
                        return_value=analytics_season,
                    )
                ),
                "back_to_back": stack.enter_context(
                    patch.object(
                        template,
                        "get_next_back_to_back",
                        return_value=(back_to_back, "found"),
                    )
                ),
                "players": stack.enter_context(
                    patch.object(template, "get_player_stats", return_value=players)
                ),
                "standings": stack.enter_context(
                    patch.object(template, "league_standings_data", return_value=standings)
                ),
                "lineup": stack.enter_context(
                    patch.object(template, "get_lineup", return_value=lineup)
                ),
                "rating": stack.enter_context(
                    patch.object(template, "ovr_rating", return_value=rating)
                ),
                "games": stack.enter_context(
                    patch.object(template, "get_recent_scores", return_value=games)
                ),
                "shots": stack.enter_context(
                    patch.object(
                        template,
                        "get_team_shot_data",
                        return_value=(made_shots, missed_shots),
                    )
                ),
            }
            app = AppTest.from_file("app.py").run(timeout=10)
            calls = {name: mocked.call_args for name, mocked in mocks.items()}

        return app, calls

    def test_offseason_uses_current_schedule_and_previous_analytics(self):
        app, calls = self.run_dashboard("2025-26")

        self.assertEqual(len(app.exception), 0)
        captions = [caption.value for caption in app.caption]
        self.assertIn("Schedule: 2026-27", captions)
        self.assertIn("Analytics: 2025-26 (last season)", captions)
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric],
            [
                ("Record", "40-42"),
                ("Rank", "#10"),
                ("Next Back to Back", "10/23 — 10/24"),
                ("Net Rating", "-1.2"),
            ],
        )
        self.assertEqual(calls["back_to_back"].args, (ATLANTA_TEAM_ID, "2026-27"))
        for name in ("players", "standings", "lineup", "rating", "games", "shots"):
            self.assertEqual(calls[name].args, (ATLANTA_TEAM_ID, "2025-26"))

    def test_analytics_switch_after_first_completed_game(self):
        app, calls = self.run_dashboard("2026-27")

        self.assertEqual(len(app.exception), 0)
        captions = [caption.value for caption in app.caption]
        self.assertIn("Schedule: 2026-27", captions)
        self.assertIn("Analytics: 2026-27", captions)
        self.assertNotIn("Analytics: 2026-27 (last season)", captions)
        for name in ("players", "standings", "lineup", "rating", "games", "shots"):
            self.assertEqual(calls[name].args, (ATLANTA_TEAM_ID, "2026-27"))


if __name__ == "__main__":
    unittest.main()
