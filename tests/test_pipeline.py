"""Collector and build on made-up snapshots: changes only, history replay, pace, forecasts, guild standing."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest import mock

import build
import collect

DAY = 86400


def member(login, gear, donated=0, active=True):
    return {"login": login, "displayName": login.capitalize(), "gearScore": gear, "donatedSilver": donated,
            "active": active, "joinedAt": "2026-09-27T09:44:24.158Z"}


def snap(members: dict, board=None, fights=(), watch=None, treasury=1000, sweep=True) -> dict:
    """members: guild -> [member, ...]; board: [(login, gear, atk, def, sup), ...]. With `sweep` the active members
    off the board get a profile whose attack alone is their gear score (what the collector's sweep would read)."""
    guilds = {g: {"guild": {"name": g.upper(), "treasurySilver": treasury, "members": len(ms),
                            "activeMembers": sum(1 for m in ms if m["active"]),
                            "gearScore": sum(m["gearScore"] for m in ms), "raidLevel": 2},
                  "boss": {"wins": 3, "losses": 1}, "members": ms} for g, ms in members.items()}
    rows = [{"login": lo, "displayName": lo, "gearScore": g, "attack": a, "defense": d, "support": s, "silver": 100,
             "quests": 10, "achievements": 5} for lo, g, a, d, s in board or []]
    return {"guilds": guilds, "boards": {b: rows for b in collect.BOARD_FIELDS}, "fights": list(fights),
            "channels": [{"login": "sola", "live": True,
                                                                          "enabled": True}],
            "watch": watch or {},
            "sweep": {m["login"]: {"attack": m["gearScore"], "defense": 0, "support": 0, "silver": 7}
                      for ms in members.values() for m in ms
                      if sweep and m["active"] and m["login"] not in {lo for lo, *_ in board or []}
                      and m["login"] not in (watch or {})}}


class Pipeline:
    """Runs collect's state/record steps on snapshots, like the Action would, into a temp data folder."""

    def __init__(self):
        self.data = Path(tempfile.mkdtemp())
        (self.data / "days").mkdir()
        self.prev: dict = {}

    def run(self, s: dict, t: int) -> dict:
        cur = collect.state_from(s, self.prev)
        rec = collect.record(s, self.prev, cur, t)
        rec["req"] = 15
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
        self.assertEqual(again["players"], {"b": {"gear": 95, "gs": 95}})  # only the fields that changed
        self.assertEqual(again["guilds"], {"karni": {"gear": 195}})
        self.assertNotIn("channels", again)  # unchanged

    def test_summary_names_the_daily_load_on_the_game(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}), T0)
        summary, _ = pipe.build(T0)
        self.assertEqual(summary["load"], {"per_run": 15, "runs_per_day": 68})

    def test_player_leaving_every_guild_keeps_the_last_gear(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100), member("b", 90)]}), T0)
        rec = pipe.run(snap({"karni": [member("a", 100)]}), T0 + 900)
        self.assertEqual(rec["players"]["b"], {"active": None, "guild": None})
        self.assertEqual(pipe.prev["players"]["b"]["gear"], 90)

    def test_fights_are_new_ones_only_and_quests_are_not_kept(self):
        pipe = Pipeline()
        fight = {"id": 5, "kind": "RAID", "difficulty": 2, "outcome": "VICTORY", "fighters": 30}
        quest = {"at": "2026-09-30T10:00:00Z", "channel": "sola", "failed": False, "line": "erhält 2 Gold 17 Silber"}
        watch = {"a": {"displayName": "a", "attack": 1, "defense": 2, "support": 3, "questHistory": [quest]}}
        first = pipe.run(snap({"karni": [member("a", 100)]}, fights=[fight], watch=watch), T0)
        self.assertEqual([f["id"] for f in first["fights"]], [5])
        self.assertNotIn("quests", first)  # a player's quest lines are read but never stored
        again = pipe.run(snap({"karni": [member("a", 100)]}, fights=[fight], watch=watch), T0 + 900)
        self.assertNotIn("fights", again)

    def test_play_window(self):
        self.assertTrue(collect.in_play_window(datetime(2026, 9, 30, 7, 0)))
        self.assertTrue(collect.in_play_window(datetime(2026, 9, 30, 23, 59)))
        self.assertFalse(collect.in_play_window(datetime(2026, 9, 30, 6, 59)))

    def test_watchlist_file(self):
        path = Path(tempfile.mkdtemp()) / "watchlist.txt"
        path.write_text("# Kommentar\nVelcorn\n\nsola  # mit Kommentar\nvelcorn\n")
        self.assertEqual(collect.read_watchlist(path), ["sola", "velcorn"])


class CommunityTests(unittest.TestCase):
    """Rules log, channel stats, guild comparison, economy and standing (since 0.10.0)."""

    def setUp(self):
        self.pipe = Pipeline()
        day = 86_400
        for k in range(8):
            s = snap({"karni": [member("a", 100 + 10 * k), member("b", 50)]}, board=[("a", 100 + 10 * k, 1, 2, 3)],
                     treasury=1000 + 100 * k)
            s["rules"] = {"questCooldownMinutes": 60 if k < 4 else 45, "playWindowOpenNow": bool(k % 2)}
            s["channels"] = [{"login": "sola", "live": k % 2 == 0, "enabled": True, "chatMode": "SLOW"}]
            self.pipe.run(s, T0 + k * day)
        self.summary, _ = self.pipe.build(T0 + 7 * day)

    def test_rule_change_is_logged_but_the_open_flag_is_not(self):
        self.assertEqual(self.summary["rules"]["log"], [[T0 + 4 * 86_400, "questCooldownMinutes", 60, 45]])
        self.assertEqual(self.summary["rules"]["now"], {"questCooldownMinutes": 45})

    def test_channel_stats_have_mode_and_live_share(self):
        self.assertEqual(self.summary["channel_stats"]["sola"]["mode"], "SLOW")
        self.assertEqual(self.summary["channel_stats"]["sola"]["live_share"], 50.0)

    def test_guild_week_and_treasury_change(self):
        g = self.summary["guilds"][0]
        self.assertEqual((g["week"], g["treasury_week"]), (70, 700))

    def test_the_kampfkraft_board_ranks_everyone_known_by_the_guild_pages_value_and_its_change(self):
        board = self.summary["power_board"]
        self.assertEqual([(r["login"], r["rank"], r["power"], r["power_day"]) for r in board],
                         [("a", 1, 170, 10), ("b", 2, 50, 0)])

    def test_economy_series_sums_the_treasuries(self):
        self.assertEqual(self.summary["economy"]["series"][-1]["treasury"], 1700)

    def test_standing_is_the_share_of_players_below(self):
        _, data = self.pipe.build(T0 + 7 * 86_400)
        page = json.loads((data / "p" / "a.json").read_text())
        self.assertEqual(page["standing"], {"better": 50.0, "of": 2})


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
        self.assertEqual((fast["guild"]["joined"], fast["guild"]["donation_share"]),
                         ("2026-09-27T09:44:24.158Z", 25.93))
        self.assertEqual(len(fast["series"]["gear"]), 8)
        top = json.loads((self.out / "p" / "top.json").read_text())
        self.assertEqual((top["board_rank"], top["forecast"]["exact"]), (1, True))

    def test_peers_are_the_other_players_with_a_known_split(self):
        fast = json.loads((self.out / "p" / "fast.json").read_text())
        self.assertEqual(fast["peers"]["n"], 2)  # top and slow
        self.assertEqual(fast["split"]["atk"], 170)  # read from its own profile

    def test_fight_groups(self):
        groups = self.summary["stats"]["types"]
        self.assertEqual([(g["name"], g["level"], g["n"], g["wins"]) for g in groups], [("Drache", 2, 8, 4)])

    def test_guild_series_is_complete_from_partial_records(self):
        series = self.summary["guilds"][0]["series"]
        self.assertTrue(all(None not in row for row in series))
        self.assertEqual(len(series), 8)
        self.assertEqual(self.summary["guilds"][0]["avg_gear"], 180.3)  # fast 170, slow 164, top 207

    def test_the_pages_the_game_shows_itself_are_not_built(self):
        for gone in ("quests", "silver", "achievements", "compendium"):
            self.assertNotIn(gone, self.summary)

    def test_a_value_that_dips_and_returns_is_no_rise(self):
        from build import gain
        now = 10 * DAY
        dip = [[0, 270], [6 * DAY, 0], [9.5 * DAY, 300]]  # a profile read 0 for a while, then 300
        self.assertEqual(gain(dip, now, DAY), 30)       # above the old peak of 270, not +300
        back = [[0, 270], [6 * DAY, 0], [9 * DAY, 270]]
        self.assertEqual(gain(back, now, DAY), 0)       # just back where it was
        self.assertEqual(gain([[9 * DAY + 100, 50]], now, DAY), None)  # no value that old
        self.assertEqual(gain([[0, 100], [9.5 * DAY, 160]], now, DAY), 60)

    def test_players_index_is_sorted_by_gear(self):
        index = json.loads((self.out / "players.json").read_text())
        self.assertEqual([r[0] for r in index], ["top", "fast", "slow"])


class BuildEdgeTests(unittest.TestCase):
    def test_top100_border(self):
        pipe = Pipeline()
        for d in range(3):
            board = [(f"p{i:03d}", 500 - i + 2 * d, 10, 10, 10) for i in range(100)]
            pipe.run(snap({"karni": [member(lo, g) for lo, g, *_ in board]}, board=board), T0 + d * DAY)
        summary, out = pipe.build(T0 + 2 * DAY)
        self.assertEqual(summary["top100"]["gear"], 500 - 99 + 4)
        self.assertEqual(summary["top100"]["pace"], 2.0)
        page = json.loads((out / "p" / "p050.json").read_text())
        self.assertIsNone(page["forecast"]["top100_gap"])  # already in

    def test_the_gear_score_comes_from_the_profile_and_the_board_not_from_the_guild_pages_power(self):
        pipe = Pipeline()
        board = [(f"p{i:03d}", 500 - i, 10, 10, 10) for i in range(100)]
        members = [member(lo, g + 30) for lo, g, *_ in board]  # the guild pages carry gear plus talents
        members.append(member("swept", 460))  # plain 430 in its profile
        s = snap({"karni": members}, board=board)
        s["sweep"]["swept"] = {"attack": 400, "defense": 20, "support": 10}
        pipe.run(s, T0)
        summary, out = pipe.build(T0)
        self.assertEqual(summary["top100"]["gear"], 500 - 99)
        page = json.loads((out / "p" / "swept.json").read_text())
        self.assertEqual((page["gear"], page["power"], page["forecast"]["rank"]), (430, 460, 71))
        self.assertEqual(json.loads((out / "p" / "p000.json").read_text())["gear"], 500)

    def test_a_player_not_read_this_run_keeps_the_last_gear_score(self):
        pipe = Pipeline()
        s = snap({"karni": [member("a", 100)]})
        pipe.run(s, T0)
        s2 = snap({"karni": [member("a", 130)]})
        s2["sweep"] = {}
        pipe.run(s2, T0 + 900)
        self.assertEqual((pipe.prev["players"]["a"]["gs"], pipe.prev["players"]["a"]["gear"]), (100, 130))

    def test_a_player_in_no_guild(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}, board=[("solo", 40, 1, 1, 1)]), T0)
        _, out = pipe.build(T0)
        solo = json.loads((out / "p" / "solo.json").read_text())
        self.assertIsNone(solo["guild"])
        self.assertEqual((solo["forecast"]["rank"], solo["forecast"]["exact"]), (1, True))

    def test_top100_days_use_the_pace_relative_to_the_border(self):
        pipe = Pipeline()
        for d in range(3):
            board = [(f"p{i:03d}", 500 - i + d, 10, 10, 10) for i in range(100)]
            board.append(("chaser", 350 + 5 * d, 1, 1, 1))
            pipe.run(snap({"karni": [member(lo, g) for lo, g, *_ in board]}, board=board[:100]), T0 + d * DAY)
        summary, out = pipe.build(T0 + 2 * DAY)
        chaser = json.loads((out / "p" / "chaser.json").read_text())
        gap = summary["top100"]["gear"] - chaser["gear"] + 1
        self.assertEqual(chaser["forecast"]["top100_gap"], gap)
        self.assertEqual(chaser["forecast"]["top100_days"], round(gap / (5 - 1), 1))

    def test_watch_data(self):
        pipe = Pipeline()
        item = {"name": "Helm", "tier": 6, "attack": 1, "defense": 9, "support": 2, "durability": 73,
                "source": "TRADER", "socket": "Angriff +4"}
        watch = {"a": {"displayName": "A", "attack": 1, "defense": 2, "support": 3, "silver": 9, "survivalPercent": 70,
                       "life": 1, "achievementsUnlocked": 4, "questHistory": [{"at": "x", "line": "y"}],
                       "stats": {"fights": 2, "marketSilverEarned": 500, "marketSilverSpent": 200},
                       "slots": [{"slot": "HELMET", "label": "Helm", "item": item},
                                 {"slot": "BOOTS", "label": "Stiefel", "item": None}]}}
        s = snap({"karni": [member("a", 100)]}, watch=watch)
        pipe.run(s, T0)
        pipe.run(s, T0 + 900)
        _, out = pipe.build(T0 + 900)
        page = json.loads((out / "p" / "a.json").read_text())
        self.assertEqual(page["watch"]["survival"], 70)
        self.assertNotIn("quests", page["watch"])
        self.assertEqual(page["watch"]["slots"],
                         {"HELMET": ["Helm", "Helm", 6, 1, 9, 2, 73, 1, "Angriff +4"], "BOOTS": ["Stiefel"]})
        self.assertEqual(page["split"]["atk"], 1)

    def test_guild_average_counts_active_members_only(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100), member("b", 200), member("c", 900, active=False)]}), T0)
        summary, _ = pipe.build(T0 + 60)
        self.assertEqual(summary["guilds"][0]["avg_gear"], 150)

    def test_main_copies_the_page_and_writes_the_files(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}, board=[("a", 100, 1, 2, 3)]), T0)
        out = Path(tempfile.mkdtemp()) / "site"
        with mock.patch("sys.argv", ["build.py", "--data", str(pipe.data), "--out", str(out)]), \
                redirect_stdout(io.StringIO()) as printed:
            build.main()
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "data" / "p" / "a.json").exists())
        self.assertIn("1 Spieler", printed.getvalue())

    def test_rebuild_replaces_old_player_files(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}), T0)
        out = Path(tempfile.mkdtemp())
        build.build(pipe.data, out, T0)
        (out / "data" / "p" / "stale.json").write_text("{}")
        build.build(pipe.data, out, T0)
        self.assertFalse((out / "data" / "p" / "stale.json").exists())

    def test_ties_share_a_rank(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100), member("b", 100), member("c", 90)]}), T0)
        _, out = pipe.build(T0)
        ranks = {lo: json.loads((out / "p" / f"{lo}.json").read_text())["forecast"]["rank"] for lo in "abc"}
        self.assertEqual(ranks, {"a": 1, "b": 1, "c": 3})


class HelperTests(unittest.TestCase):
    def test_value_at_and_pace(self):
        series = [[0, 10], [DAY, 20]]
        self.assertIsNone(build.value_at(series, -1))
        self.assertEqual(build.value_at(series, DAY - 1), 10)
        self.assertEqual(build.pace(series, 2 * DAY), 5.0)
        self.assertIsNone(build.pace([[0, 10]], 3600))  # under 12 h of data


if __name__ == "__main__":
    unittest.main()
