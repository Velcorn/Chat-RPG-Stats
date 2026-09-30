"""Collector and build on made-up snapshots: changes only, history replay, pace, forecasts, guild standing."""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import build
import collect

DAY = 86400


def member(login, gear, donated=0, active=True):
    return {"login": login, "displayName": login.capitalize(), "gearScore": gear, "donatedSilver": donated,
            "active": active}


def snap(members: dict, board=None, fights=(), watch=None, treasury=1000) -> dict:
    """members: guild -> [member, ...]; board: [(login, gear, atk, def, sup), ...]."""
    guilds = {g: {"guild": {"name": g.upper(), "treasurySilver": treasury, "members": len(ms),
                            "activeMembers": sum(1 for m in ms if m["active"]),
                            "gearScore": sum(m["gearScore"] for m in ms), "raidLevel": 2},
                  "boss": {"wins": 3, "losses": 1}, "members": ms} for g, ms in members.items()}
    rows = [{"login": lo, "displayName": lo, "gearScore": g, "attack": a, "defense": d, "support": s, "silver": 100,
             "quests": 10, "achievements": 5} for lo, g, a, d, s in board or []]
    return {"guilds": guilds, "boards": {"gear": rows, "quests": rows}, "fights": list(fights),
            "trader": {"visiting": False, "lastVisit": None}, "channels": [{"login": "sola", "live": True,
                                                                          "enabled": True}],
            "watch": watch or {}}


class Pipeline:
    """Runs collect's state/record steps on snapshots, like the Action would, into a temp data folder."""

    def __init__(self):
        self.data = Path(tempfile.mkdtemp())
        (self.data / "days").mkdir()
        self.prev: dict = {}

    def run(self, s: dict, t: int) -> dict:
        cur = collect.state_from(s, self.prev)
        rec = collect.record(s, self.prev, cur, t)
        day = datetime.fromtimestamp(t).strftime("%Y-%m-%d")
        with (self.data / "days" / f"{day}.jsonl").open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        (self.data / "state.json").write_text(json.dumps(cur))
        self.prev = cur
        return rec

    def build(self, now: int) -> tuple[dict, Path]:
        out = Path(tempfile.mkdtemp())
        return build.build(self.data, out, now), out / "data"


T0 = 1_790_000_000


class CollectTests(unittest.TestCase):
    def test_second_run_stores_only_changes(self):
        pipe = Pipeline()
        first = pipe.run(snap({"karni": [member("a", 100), member("b", 90)]}), T0)
        self.assertEqual(set(first["players"]), {"a", "b"})
        again = pipe.run(snap({"karni": [member("a", 100), member("b", 95)]}), T0 + 900)
        self.assertEqual(again["players"], {"b": {"name": "B", "gear": 95, "donated": 0, "active": True,
                                                  "guild": "karni"}})
        self.assertNotIn("channels", again)  # unchanged

    def test_player_leaving_every_guild_keeps_the_last_gear(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100), member("b", 90)]}), T0)
        rec = pipe.run(snap({"karni": [member("a", 100)]}), T0 + 900)
        self.assertEqual(rec["players"]["b"]["guild"], None)
        self.assertEqual(rec["players"]["b"]["gear"], 90)

    def test_fights_and_quests_are_new_ones_only(self):
        pipe = Pipeline()
        fight = {"id": 5, "kind": "RAID", "difficulty": 2, "outcome": "VICTORY", "fighters": 30}
        quest = {"at": "2026-09-30T10:00:00Z", "channel": "sola", "failed": False, "line": "erhält 2 Gold 17 Silber"}
        watch = {"a": {"displayName": "a", "attack": 1, "defense": 2, "support": 3, "questHistory": [quest]}}
        first = pipe.run(snap({"karni": [member("a", 100)]}, fights=[fight], watch=watch), T0)
        self.assertEqual([f["id"] for f in first["fights"]], [5])
        self.assertEqual(len(first["quests"]["a"]), 1)
        again = pipe.run(snap({"karni": [member("a", 100)]}, fights=[fight], watch=watch), T0 + 900)
        self.assertNotIn("fights", again)
        self.assertNotIn("quests", again)

    def test_play_window(self):
        self.assertTrue(collect.in_play_window(datetime(2026, 9, 30, 7, 0)))
        self.assertTrue(collect.in_play_window(datetime(2026, 9, 30, 23, 59)))
        self.assertFalse(collect.in_play_window(datetime(2026, 9, 30, 6, 59)))

    def test_watchlist_file(self):
        path = Path(tempfile.mkdtemp()) / "watchlist.txt"
        path.write_text("# Kommentar\nVelcorn\n\nsola  # mit Kommentar\nvelcorn\n")
        self.assertEqual(collect.read_watchlist(path), ["sola", "velcorn"])


class BuildTests(unittest.TestCase):
    def setUp(self):
        # A week of history: "fast" gains 10 a day, "slow" 2 a day, "top" sits at the top-100 border.
        self.pipe = Pipeline()
        for d in range(8):
            ms = [member("fast", 100 + 10 * d, donated=50 * d), member("slow", 150 + 2 * d, donated=1000),
                  member("top", 200 + d)]
            board = [("top", 200 + d, 90, 60, 50), ("slow", 150 + 2 * d, 50, 80, 20)]
            self.pipe.run(snap({"karni": ms}, board=board,
                               fights=[{"id": d + 1, "kind": "BOSS", "name": "Drache", "bossLevel": 2,
                                        "outcome": "VICTORY" if d % 2 else "DEFEAT", "fighters": 20,
                                        "endedAt": "2026-09-30T10:00:00Z"}]),
                          T0 + d * DAY)
        self.now = T0 + 7 * DAY
        self.summary, self.out = self.pipe.build(self.now)

    def test_pace_and_changes(self):
        fast = json.loads((self.out / "p" / "fast.json").read_text())
        self.assertEqual((fast["gear"], fast["day"], fast["week"], fast["pace"]), (170, 10, 70, 10.0))
        self.assertEqual(self.summary["risers"]["day"][0]["login"], "fast")

    def test_forecast(self):
        fast = json.loads((self.out / "p" / "fast.json").read_text())
        f = fast["forecast"]
        self.assertEqual((f["rank"], f["exact"]), (2, False))  # behind top (207), ahead of slow (164)
        self.assertEqual(f["next_gap"], 207 - 170 + 1)
        self.assertEqual(f["next_days"], 3.8)

    def test_guild_standing_and_series(self):
        fast = json.loads((self.out / "p" / "fast.json").read_text())
        self.assertEqual((fast["guild"]["donation_rank"], fast["guild"]["donation_gap"]), (2, 1000 - 350 + 1))
        self.assertEqual(len(fast["series"]["gear"]), 8)
        top = json.loads((self.out / "p" / "top.json").read_text())
        self.assertEqual((top["board_rank"], top["forecast"]["exact"]), (1, True))

    def test_peers_need_a_known_split(self):
        fast = json.loads((self.out / "p" / "fast.json").read_text())
        self.assertEqual(fast["peers"]["n"], 2)  # only the two board players have a split
        self.assertIsNone(fast["split"]["atk"])

    def test_fight_groups(self):
        groups = self.summary["fights"]["groups"]
        self.assertEqual([(g["name"], g["level"], g["n"], g["wins"]) for g in groups], [("Drache", 2, 8, 4)])

    def test_players_index_is_sorted_by_gear(self):
        index = json.loads((self.out / "players.json").read_text())
        self.assertEqual([r[0] for r in index], ["top", "fast", "slow"])


class HelperTests(unittest.TestCase):
    def test_value_at_and_pace(self):
        series = [[0, 10], [DAY, 20]]
        self.assertIsNone(build.value_at(series, -1))
        self.assertEqual(build.value_at(series, DAY - 1), 10)
        self.assertEqual(build.pace(series, 2 * DAY), 5.0)
        self.assertIsNone(build.pace([[0, 10]], 3600))  # under 12 h of data

    def test_quest_silver(self):
        self.assertEqual(build.quest_silver("X erhält 2 Gold 17 Silber. Nächste"), 217)
        self.assertEqual(build.quest_silver("X erhält 90 Silber."), 90)
        self.assertEqual(build.quest_silver("X scheitert."), 0)


if __name__ == "__main__":
    unittest.main()
