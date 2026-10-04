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
            "/api/combat/history": [], "/api/combat?kompakt=true": [], "/api/channels": [],
            "/api/rules": {"questCooldownMinutes": 45}, **extra}


class SnapshotTests(unittest.TestCase):
    def test_requests_and_empty_guilds(self):
        site = FakeSite(answers())
        s = collect.snapshot(site, [])
        self.assertEqual(list(s["guilds"]), ["karni"])  # a guild without members costs no request
        self.assertEqual(site.requests, 10)
        self.assertEqual(s["watch"], {})

    def test_compendium_is_read_on_request_and_a_failing_page_costs_nothing(self):
        site = FakeSite(answers(**{"/api/compendium": {"potions": []}}))
        s = collect.snapshot(site, [], compendium_day="2026-10-04")
        self.assertEqual((s["compendium"], s["compendium_day"], site.requests), ({"potions": []}, "2026-10-04", 11))
        self.assertNotIn("compendium", collect.snapshot(FakeSite(answers()), []))
        broken = collect.snapshot(FakeSite(answers(**{"/api/compendium": 503})), [], compendium_day="2026-10-04")
        self.assertNotIn("compendium", broken)

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

    def test_guild_buildings_and_bosses(self):
        s = snap({"karni": [member("a", 100)]})
        s["guilds"]["karni"]["boss"] = {"wins": 3, "losses": 1, "averageGear": 248, "bosses": [
            {"name": "Die Rattenkönigin", "highestWon": 2, "nextPriceSilver": 1500, "nextRecommendedGear": 170}]}
        s["guilds"]["karni"]["buildings"] = [
            {"key": "WERKSTATT", "label": "Werkstatt", "level": 3, "maxLevel": 5, "effect": "3 Siegel weniger",
             "nextPrice": "4545 Gold 20 Silber"},
            {"key": "WALL", "label": "Wall", "level": 5, "maxLevel": 5, "effect": "voll", "nextPrice": None}]
        g = collect.state_from(s, {})["guilds"]["karni"]
        self.assertEqual(g["buildings"], {"WERKSTATT": [3, 5, "Werkstatt", "3 Siegel weniger", 454520],
                                          "WALL": [5, 5, "Wall", "voll", None]})
        self.assertEqual(g["bosses"], {"Die Rattenkönigin": [2, 1500, 170]})
        self.assertEqual(g["boss_gear"], 248)
        self.assertEqual(collect.price_value("15 Gold"), 1500)
        self.assertEqual(collect.price_value("80 Silber"), 80)
        self.assertIsNone(collect.price_value("kostenlos"))

    def test_compendium_keeps_the_reference_data_and_carries_over_until_the_next_read(self):
        raw = {"potions": [{"kind": "HEAL", "label": "Heiltrank", "description": "d", "icon": "x.png", "use": "FIGHT"}],
               "tiers": [{"tier": 1, "material": "Holz", "templates": 90, "examples": [{}], "sources": ["Quests"]}],
               "bosses": [{"name": "Boss", "intro": "...", "lootTierMin": 4, "lootTierMax": 5, "gearTier": 3,
                           "recommendedGear": 170, "mythicGearTier": 3, "hidden": False, "unlockedBy": None,
                           "hoard": [{"name": "Helm", "slot": "Helm", "icon": "i.png"}]}],
               "fights": [{"name": "Höhle", "kind": "ADVENTURE", "kindLabel": "Abenteuer", "difficulty": 1}],
               "projects": [{"project": "WARD", "label": "Schutzzeichen", "description": "d", "nextBattle": True}]}
        s = snap({"karni": [member("a", 100)]})
        first = collect.state_from({**s, "compendium": raw, "compendium_day": "2026-10-04"}, {})
        self.assertEqual(first["compendium"]["potions"], [{"kind": "HEAL", "label": "Heiltrank", "description": "d",
                                                          "use": "FIGHT"}])
        self.assertEqual(first["compendium"]["tiers"][0], {"tier": 1, "material": "Holz", "templates": 90,
                                                          "sources": ["Quests"]})
        self.assertEqual(first["compendium"]["bosses"][0]["hoard"], [{"name": "Helm", "slot": "Helm"}])
        self.assertNotIn("mythicGearTier", first["compendium"]["bosses"][0])
        later = collect.state_from(s, first)
        self.assertEqual((later["compendium"], later["compendium_day"]), (first["compendium"], "2026-10-04"))

    def test_changed_ignores_equal_entries_and_keeps_new_ones_whole(self):
        old = {"a": {"x": 1, "y": 2}, "b": {"x": 1}}
        new = {"a": {"x": 1, "y": 3}, "b": {"x": 1}, "c": {"x": 9}}
        self.assertEqual(collect.changed(old, new), {"a": {"y": 3}, "c": {"x": 9}})


class MainTests(unittest.TestCase):
    def run_main(self, *, now, snapshot=None, args=(), data=None):
        data = data or Path(tempfile.mkdtemp())
        out = Path(tempfile.mkdtemp()) / "out"
        patches = [mock.patch.object(collect, "datetime", mock.Mock(now=lambda tz: now)),
                   mock.patch.object(collect, "Site", lambda: mock.Mock(requests=7)),
                   mock.patch.object(collect, "snapshot", snapshot or (
                       lambda site, wl, after=0, compendium_day=None: snap({"karni": [member("a", 100)]}))),
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

    def test_compendium_is_asked_for_once_a_day(self):
        asked = []

        def fake(site, wl, after=0, compendium_day=None):
            asked.append(compendium_day)
            return {**snap({"karni": [member("a", 100)]}), "compendium_day": compendium_day,
                    **({"compendium": {"potions": []}} if compendium_day else {})}

        _, data, _, _ = self.run_main(now=self.NOON, snapshot=fake)
        self.run_main(now=self.NOON, snapshot=fake, data=data)
        self.assertEqual(asked, ["2026-09-30", None])

    def test_second_run_appends_and_reads_the_state(self):
        _, data, _, _ = self.run_main(now=self.NOON)
        with mock.patch("sys.argv", ["collect.py", "--data", str(data), "--watchlist", str(data / "none.txt")]), \
                mock.patch.object(collect, "datetime", mock.Mock(now=lambda tz: self.NOON)), \
                mock.patch.object(collect, "Site", lambda: mock.Mock(requests=7)), \
                mock.patch.object(collect, "snapshot",
                                  lambda site, wl, after=0, compendium_day=None: snap({"karni": [member("a", 105)]})), \
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
        def down(site, wl, after=0, compendium_day=None):
            raise TimeoutError("timed out")

        code, data, out, printed = self.run_main(now=self.NOON, snapshot=down)
        self.assertEqual(code, 0)
        self.assertFalse((data / "state.json").exists())
        self.assertFalse(out.exists())
        self.assertIn("übersprungen", printed)


if __name__ == "__main__":
    unittest.main()
