"""Collector edges: requests, the run itself (skips, files), the watchlist's data and the User-Agent."""
import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest import mock

from test_pipeline import member, snap

import collect


class FakeSite:
    """Answers by path; a path mapped to an int raises that HTTP status."""

    def __init__(self, answers):
        self.answers, self.paths, self.requests = answers, [], 0

    def get(self, path):
        self.paths.append(path)
        self.requests += 1
        answer = self.answers[path]
        if isinstance(answer, int):
            raise urllib.error.HTTPError(collect.BASE + path, answer, "x", {}, io.BytesIO())
        return answer


def answers(**extra):
    board = [{"login": "a", "gearScore": 100, "quests": 3, "silver": 500, "achievements": 7}]
    return {"/api/guilds": [{"login": "karni", "members": 2}, {"login": "leer", "members": 0}],
            "/api/guilds/karni": {"guild": {"name": "Karni"}, "members": [member("a", 100)]},
            **{f"/api/leaderboard?by={b}&limit=100": board for b in collect.BOARD_FIELDS},
            "/api/combat/history": [], "/api/trader": {"visiting": False}, "/api/combat?kompakt=true": [],
            "/api/channels": [], **extra}


class SnapshotTests(unittest.TestCase):
    def test_requests_and_empty_guilds(self):
        site = FakeSite(answers())
        s = collect.snapshot(site, [])
        self.assertEqual(list(s["guilds"]), ["karni"])  # a guild without members costs no request
        self.assertEqual(site.requests, 10)
        self.assertEqual(s["watch"], {})

    def test_watchlist_costs_one_request_each_and_skips_unknown_players(self):
        site = FakeSite(answers(**{"/api/players/sola": {"displayName": "Sola"}, "/api/players/weg": 404}))
        s = collect.snapshot(site, ["sola", "weg"])
        self.assertEqual(list(s["watch"]), ["sola"])
        self.assertEqual(site.requests, 12)

    def test_other_http_errors_are_raised(self):
        with self.assertRaises(urllib.error.HTTPError):
            collect.snapshot(FakeSite(answers(**{"/api/players/sola": 500})), ["sola"])

    def test_only_get_requests_with_an_honest_user_agent(self):
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout):
            seen["method"], seen["agent"], seen["url"] = req.get_method(), req.get_header("User-agent"), req.full_url
            return Resp(b'{"ok": true}')

        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep") as sleep:
            site = collect.Site(pause=2)
            self.assertEqual(site.get("/api/rules"), {"ok": True})
            site.get("/api/rules")
        self.assertEqual(seen["method"], "GET")
        self.assertIn("Chat-RPG-Stats", seen["agent"])
        self.assertIn("github.com/", seen["agent"])
        sleep.assert_called_once_with(2)  # a pause between requests, none before the first

    def test_user_agent_names_the_repo_it_runs_in(self):
        with mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": "someone/fork"}):
            self.assertIn("github.com/someone/fork", collect.user_agent())


class StateTests(unittest.TestCase):
    def test_watch_data_and_players_only_known_from_the_watchlist(self):
        watch = {"sola": {"displayName": "Sola", "attack": 5, "defense": 6, "support": 7, "silver": 42,
                          "survivalPercent": 80, "life": 3, "achievementsUnlocked": 2, "stats": {"fights": 4},
                          "guild": {"login": "karni"}}}
        s = snap({"karni": [member("a", 100)]}, watch=watch)
        prev = {"players": {"sola": {"gear": 50, "name": "Sola", "guild": None}}}
        state = collect.state_from(s, prev)
        self.assertEqual(state["watch"]["sola"], {"survival": 80, "life": 3, "ach": 2, "stats": {"fights": 4},
                                                  "slots": {}})
        self.assertEqual(state["details"]["sola"]["atk"], 5)
        self.assertEqual(state["players"]["sola"]["gear"], 50)  # the last known gear stays
        self.assertEqual(state["players"]["sola"]["guild"], "karni")

    def test_every_ranking_keeps_the_value_it_ranks_by(self):
        s = snap({"karni": [member("a", 100)]}, board=[("a", 100, 1, 2, 3)])
        state = collect.state_from(s, {})
        self.assertEqual({b: state["boards"][b] for b in ("gear", "gold", "errungenschaften", "quests")},
                         {"gear": [["a", 100]], "gold": [["a", 100]], "errungenschaften": [["a", 5]],
                          "quests": [["a", 10]]})

    def test_board_player_without_a_guild(self):
        s = snap({"karni": [member("a", 100)]}, board=[("solo", 80, 1, 2, 3)])
        state = collect.state_from(s, {})
        self.assertEqual(state["players"]["solo"]["guild"], None)
        self.assertEqual(state["players"]["solo"]["gear"], 80)
        self.assertEqual(state["boards"]["gear"], [["solo", 80]])

    def test_running_fights_only(self):
        s = snap({"karni": [member("a", 100)]})
        s["encounters"] = [{"id": 1, "channel": "sola", "kind": "BOSS", "name": "Drache", "bossLevel": 2,
                            "phase": "FIGHT", "phaseLabel": "Kampf läuft", "fighterCount": 40},
                           {"id": 2, "channel": "karni", "kind": "RAID", "phase": "VICTORY", "difficulty": 3}]
        live = collect.state_from(s, {})["live_fights"]
        self.assertEqual([(f["channel"], f["level"], f["phase"], f["fighters"]) for f in live],
                         [("sola", 2, "Kampf läuft", 40)])

    def test_trader_only_named_while_visiting(self):
        s = snap({"karni": [member("a", 100)]})
        s["trader"] = {"visiting": True, "channel": "sola", "lastVisit": "2026-09-30T10:00:00Z"}
        self.assertEqual(collect.state_from(s, {})["trader"], {"channel": "sola", "last": "2026-09-30T10:00:00Z"})
        s["trader"]["visiting"] = False
        self.assertIsNone(collect.state_from(s, {})["trader"]["channel"])

    def test_changed_ignores_equal_entries_and_keeps_new_ones_whole(self):
        old = {"a": {"x": 1, "y": 2}, "b": {"x": 1}}
        new = {"a": {"x": 1, "y": 3}, "b": {"x": 1}, "c": {"x": 9}}
        self.assertEqual(collect.changed(old, new), {"a": {"y": 3}, "c": {"x": 9}})


class MainTests(unittest.TestCase):
    def run_main(self, *, now, snapshot=None, args=()):
        data = Path(tempfile.mkdtemp())
        out = Path(tempfile.mkdtemp()) / "out"
        patches = [mock.patch.object(collect, "datetime", mock.Mock(now=lambda tz: now)),
                   mock.patch.object(collect, "Site", lambda: mock.Mock(requests=7)),
                   mock.patch.object(collect, "snapshot", snapshot or (lambda site, wl: snap(
                       {"karni": [member("a", 100)]}))),
                   mock.patch("sys.argv", ["collect.py", "--data", str(data), "--watchlist", str(data / "none.txt"),
                                           *args]),
                   mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(out)})]
        for p in patches:
            p.start()
        try:
            with redirect_stdout(io.StringIO()) as printed:
                code = collect.main()
        finally:
            mock.patch.stopall()
        return code, data, out, printed.getvalue()

    NOON = datetime(2026, 9, 30, 12, 0, tzinfo=collect.BERLIN)
    NIGHT = datetime(2026, 9, 30, 3, 0, tzinfo=collect.BERLIN)

    def test_run_writes_the_day_file_state_and_output(self):
        code, data, out, _ = self.run_main(now=self.NOON)
        self.assertEqual(code, 0)
        lines = (data / "days" / "2026-09-30.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["t"], int(self.NOON.timestamp()))
        self.assertEqual(json.loads((data / "state.json").read_text())["players"]["a"]["gear"], 100)
        self.assertEqual(out.read_text(), "collected=true\n")
        self.assertFalse((data / "state.json.tmp").exists())

    def test_second_run_appends_and_reads_the_state(self):
        _, data, _, _ = self.run_main(now=self.NOON)
        with mock.patch("sys.argv", ["collect.py", "--data", str(data), "--watchlist", str(data / "none.txt")]), \
                mock.patch.object(collect, "datetime", mock.Mock(now=lambda tz: self.NOON)), \
                mock.patch.object(collect, "Site", lambda: mock.Mock(requests=7)), \
                mock.patch.object(collect, "snapshot", lambda site, wl: snap({"karni": [member("a", 105)]})), \
                redirect_stdout(io.StringIO()):
            collect.main()
        lines = (data / "days" / "2026-09-30.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(lines[1])["players"], {"a": {"gear": 105}})

    def test_nothing_happens_outside_the_play_window(self):
        code, data, out, printed = self.run_main(now=self.NIGHT)
        self.assertEqual(code, 0)
        self.assertFalse((data / "days").exists())
        self.assertFalse(out.exists())  # no "collected", so no build and no deploy
        self.assertIn("Außerhalb der Spielzeit", printed)

    def test_force_collects_at_night(self):
        _, data, out, _ = self.run_main(now=self.NIGHT, args=["--force"])
        self.assertTrue((data / "state.json").exists())
        self.assertTrue(out.exists())

    def test_site_down_skips_the_run_without_failing(self):
        def down(site, wl):
            raise TimeoutError("timed out")

        code, data, out, printed = self.run_main(now=self.NOON, snapshot=down)
        self.assertEqual(code, 0)
        self.assertFalse((data / "state.json").exists())
        self.assertFalse(out.exists())
        self.assertIn("übersprungen", printed)


if __name__ == "__main__":
    unittest.main()
