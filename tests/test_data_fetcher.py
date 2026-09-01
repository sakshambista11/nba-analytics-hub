import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

import pandas as pd

import data_fetcher


class FakeEndpoint:
    def __init__(self, frames):
        self.frames = frames

    def get_data_frames(self):
        return self.frames


class SeasonTests(unittest.TestCase):
    def test_rollover_boundary(self):
        self.assertEqual(data_fetcher.get_current_season(date(2026, 6, 30)), "2025-26")
        self.assertEqual(data_fetcher.get_current_season(date(2026, 7, 1)), "2026-27")
        self.assertEqual(data_fetcher.get_current_season(date(2027, 1, 1)), "2026-27")

    def test_aware_datetime_uses_central_date(self):
        instant = datetime(2026, 7, 1, 2, tzinfo=timezone.utc)
        self.assertEqual(data_fetcher.get_current_season(instant), "2025-26")

    def test_previous_season(self):
        self.assertEqual(data_fetcher.get_previous_season("2026-27"), "2025-26")

    def test_analytics_use_previous_season_until_team_completes_a_game(self):
        with patch.object(data_fetcher, "get_team_game_logs", return_value=pd.DataFrame()):
            self.assertEqual(
                data_fetcher.get_analytics_season(1610612737, "2026-27"),
                "2025-26",
            )

        completed_game = pd.DataFrame({"GAME_ID": ["0022600001"]})
        with patch.object(
            data_fetcher, "get_team_game_logs", return_value=completed_game
        ):
            self.assertEqual(
                data_fetcher.get_analytics_season(1610612737, "2026-27"),
                "2026-27",
            )


class ScheduleTests(unittest.TestCase):
    def tearDown(self):
        data_fetcher.get_season_schedule.clear()

    def test_schedule_request_uses_season_and_normalizes_dates(self):
        raw_schedule = pd.DataFrame(
            {
                "gameDateTimeUTC": ["2026-10-05T01:00:00Z", "2026-11-01T01:00:00Z"],
                "gameLabel": ["Preseason", ""],
                "gameStatus": [1, 1],
                "homeTeam_teamId": [1610612742, 1610612742],
                "awayTeam_teamId": [1610612745, 1610612745],
            }
        )
        requested = []

        def build_endpoint(**kwargs):
            requested.append(kwargs)
            return FakeEndpoint([raw_schedule])

        with patch.object(data_fetcher, "ScheduleLeagueV2", side_effect=build_endpoint):
            schedule = data_fetcher.get_season_schedule("2026-27")

        self.assertEqual(requested, [{"season": "2026-27"}])
        self.assertEqual(len(schedule), 1)
        self.assertEqual(str(schedule["Date"].dt.tz), "America/Chicago")
        self.assertEqual(schedule["Date"].iloc[0].day, 31)

    def test_finds_next_back_to_back_by_local_game_date(self):
        schedule = pd.DataFrame(
            {
                "Date": pd.to_datetime(
                    ["2026-11-01T01:00:00Z", "2026-11-02T01:00:00Z"], utc=True
                ).tz_convert(data_fetcher.CENTRAL_TIMEZONE),
                "homeTeam_teamId": [1, 3],
                "awayTeam_teamId": [2, 1],
            }
        )
        games, status = data_fetcher._find_next_back_to_back(
            schedule, 1, as_of=date(2026, 10, 30)
        )
        self.assertEqual(status, "found")
        self.assertEqual(len(games), 2)

    def test_schedule_states(self):
        columns = ["Date", "homeTeam_teamId", "awayTeam_teamId"]
        games, status = data_fetcher._find_next_back_to_back(
            pd.DataFrame(columns=columns), 1, as_of=date(2026, 10, 1)
        )
        self.assertTrue(games.empty)
        self.assertEqual(status, "schedule_unavailable")

        schedule = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2026-10-20T19:00:00-05:00"]),
                "homeTeam_teamId": [1],
                "awayTeam_teamId": [2],
            }
        )
        _, status = data_fetcher._find_next_back_to_back(
            schedule, 1, as_of=date(2026, 10, 21)
        )
        self.assertEqual(status, "season_complete")

        _, status = data_fetcher._find_next_back_to_back(
            schedule, 1, as_of=date(2026, 10, 1)
        )
        self.assertEqual(status, "no_back_to_back")

    def test_completed_game_is_not_used_in_next_back_to_back(self):
        schedule = pd.DataFrame(
            {
                "Date": pd.to_datetime(
                    [
                        "2026-10-23T23:00:00Z",
                        "2026-10-25T00:00:00Z",
                        "2026-11-01T00:00:00Z",
                        "2026-11-02T00:00:00Z",
                    ],
                    utc=True,
                ).tz_convert(data_fetcher.CENTRAL_TIMEZONE),
                "gameStatus": [3, 1, 1, 1],
                "homeTeam_teamId": [1, 1, 1, 4],
                "awayTeam_teamId": [2, 3, 4, 1],
            }
        )
        games, status = data_fetcher._find_next_back_to_back(
            schedule, 1, as_of=datetime(2026, 10, 23, 20)
        )
        self.assertEqual(status, "found")
        self.assertEqual(games["Date"].dt.strftime("%m/%d").tolist(), ["10/31", "11/01"])


class EmptyResponseTests(unittest.TestCase):
    def tearDown(self):
        for function in (
            data_fetcher.ovr_rating,
            data_fetcher.get_team_shot_data,
            data_fetcher.league_standings_data,
            data_fetcher.get_lineup,
            data_fetcher.get_team_game_logs,
            data_fetcher.get_recent_scores,
            data_fetcher.get_player_stats,
        ):
            function.clear()

    def test_all_fetchers_return_stable_empty_results(self):
        empty = pd.DataFrame()
        cases = (
            ("LeagueDashTeamStats", [empty], lambda: data_fetcher.ovr_rating(1, "2026-27")),
            ("ShotChartDetail", [empty], lambda: data_fetcher.get_team_shot_data(1, "2026-27")),
            ("LeagueStandings", [empty], lambda: data_fetcher.league_standings_data(1, "2026-27")),
            ("TeamDashLineups", [empty, empty], lambda: data_fetcher.get_lineup(1, "2026-27")),
            ("TeamGameLogs", [empty], lambda: data_fetcher.get_recent_scores(1, "2026-27")),
            ("TeamPlayerDashboard", [empty, empty], lambda: data_fetcher.get_player_stats(1, "2026-27")),
        )

        for endpoint_name, frames, call_fetcher in cases:
            with self.subTest(endpoint=endpoint_name):
                with patch.object(data_fetcher, endpoint_name, return_value=FakeEndpoint(frames)):
                    result = call_fetcher()
                if isinstance(result, tuple):
                    self.assertTrue(all(frame.empty for frame in result))
                else:
                    self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()
