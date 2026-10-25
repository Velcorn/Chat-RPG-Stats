"""Collector and build on made-up snapshots: changes only, history replay, pace, forecasts, guild standing."""
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest import mock

import archive as season_archive
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

    def test_summary_carries_the_project_version_for_the_page_header(self):
        text = (Path(build.__file__).resolve().parent.parent / "pyproject.toml").read_text("utf-8")
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}), T0)
        summary, data = pipe.build(T0)
        entries = json.loads((data / "changelog.json").read_text("utf-8"))
        self.assertEqual(entries[0]["version"], summary["version"])
        self.assertEqual(summary["version"], re.search(r'^version = "([^"]+)"', text, re.M)[1])
        with mock.patch.object(build.Path, "read_text", side_effect=OSError):
            self.assertIsNone(build.project_version())

    def test_summary_names_the_daily_load_on_the_game(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}), T0)
        summary, _ = pipe.build(T0)
        self.assertEqual(summary["load"], {"per_run": 15, "runs_per_day": 224})

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

    def test_channel_stats_have_the_live_share(self):
        self.assertNotIn("mode", self.summary["channel_stats"]["sola"])
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
        import build
        self.addCleanup(setattr, build, "GEAR_SINCE", build.GEAR_SINCE)
        build.GEAR_SINCE = 0  # the made-up history starts on 30.09.: before the real change of the board's measure
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

    def test_the_forecast_carries_the_gap_to_the_next_place_of_the_board(self):
        top = json.loads((self.out / "p" / "top.json").read_text())
        slow = json.loads((self.out / "p" / "slow.json").read_text())
        self.assertEqual(top["forecast"]["gap"], {"ahead": True, "tie": False, "amount": 207 - 164})
        self.assertEqual(slow["forecast"]["gap"], {"ahead": False, "tie": False, "amount": 207 - 164})

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
        # the stat bars compare within the class: "fast" (all attack) next to "top" (90/60/50), not the tank "slow"
        self.assertEqual(fast["peers"]["cls"], {"main": "atk", "n": 1, "gear": 207,
                                                "med": {"atk": 90, "def": 60, "sup": 50}})
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

    def test_the_rank_line_starts_with_plain_gear_and_skips_short_absences(self):
        from build import rank_series
        series = [[0, 64], [100, None], [200, 5], [300, None], [400, 4], [5000, None], [9000, 3]]
        self.assertEqual(rank_series(series, since=150, blip=600),
                         [[200, 5], [400, 4], [5000, None], [9000, 3]])  # 300 was a blip, 5000 a real absence
        self.assertEqual(rank_series([[200, None], [300, 7]], since=0), [[300, 7]])  # no gap at the start
        hours = [[0, 9], [3600, None], [3 * 3600, 9], [30 * 3600, None], [40 * 3600, 8]]
        self.assertEqual(rank_series(hours, since=0), [[0, 9], [3 * 3600, 9], [30 * 3600, None], [40 * 3600, 8]])

    def test_a_rank_that_drops_and_returns_at_the_next_run_is_smoothed(self):
        from build import rank_series
        series = [[0, 10], [300, 25], [600, 11], [900, 40], [5000, 12], [5300, 20], [5600, 21]]
        self.assertEqual(rank_series(series, since=0, dip_within=600),
                         [[0, 10], [600, 11], [900, 40], [5000, 12], [5300, 20], [5600, 21]])  # 25 was a dip, 40 lasted

    def test_a_gear_dip_that_comes_back_within_the_hour_is_smoothed(self):
        from build import gear_series
        series = [[0, 468], [600, 417], [900, 475], [5000, 480], [5300, 400], [20000, 478], [30000, 520]]
        self.assertEqual(gear_series(series),
                         [[0, 468], [900, 475], [5000, 480], [5300, 400], [20000, 478], [30000, 520]])  # 400 stays
        low = [[0, 468], [600, 417], [700, 420], [900, 470]]  # two runs low
        self.assertEqual(gear_series(low), [[0, 468], [900, 470]])

    def test_a_value_that_dips_and_returns_is_no_rise(self):
        from build import gain
        now = 10 * DAY
        dip = [[0, 270], [6 * DAY, 0], [9.5 * DAY, 300]]  # a profile read 0 for a while, then 300
        self.assertEqual(gain(dip, now, DAY, since=0), 30)       # above the old peak of 270, not +300
        back = [[0, 270], [6 * DAY, 0], [9 * DAY, 270]]
        self.assertEqual(gain(back, now, DAY, since=0), 0)       # just back where it was
        self.assertEqual(gain([[9 * DAY + 100, 50]], now, DAY, since=0), None)  # no value that old
        self.assertEqual(gain([[0, 100], [9.5 * DAY, 160]], now, DAY, since=0), 60)
        # a measure that changed at DAY * 4 (Kampfkraft before, plain gear after): its peaks don't count
        series = [[DAY, 500], [5 * DAY, 300], [9.5 * DAY, 340]]
        self.assertEqual(gain(series, now, DAY, since=4 * DAY), 40)
        self.assertEqual(gain(series, now, DAY, since=0), 0)
        self.assertIsNone(gain(series, now, 7 * DAY, since=4 * DAY))  # the week reaches back before the change

    def test_the_second_half_of_a_run_is_not_another_run(self):
        from build import History
        h = History([{"t": 1, "req": 10, "channels": {"sola": True}}, {"t": 2, "req": 50, "part": "profiles"},
                     {"t": 3, "req": 12, "channels": {"sola": False}}])
        self.assertEqual((h.runs, h.requests, dict(h.live_runs)), (2, 12, {"sola": [1, 2]}))
        h = History([{"t": 1, "req": 10, "channels": {"sola": True}}, {"t": 2, "req": 50, "part": "profiles"}])
        self.assertEqual((h.runs, h.requests, h.last), (1, 60, 2))  # the run's requests: both halves

    def test_players_index_is_sorted_by_gear(self):
        index = json.loads((self.out / "players.json").read_text())
        self.assertEqual([r[0] for r in index], ["top", "fast", "slow"])


class BuildEdgeTests(unittest.TestCase):
    def test_top100_border(self):
        for name in ("GEAR_SINCE", "BOARD_LAG"):  # the made-up history starts before the board showed the plain score
            self.addCleanup(setattr, build, name, getattr(build, name))
            setattr(build, name, 0)
        pipe = Pipeline()
        for d in range(3):
            board = [(f"p{i:03d}", 500 - i + 2 * d, 10, 10, 10) for i in range(100)]
            pipe.run(snap({"karni": [member(lo, g) for lo, g, *_ in board]}, board=board), T0 + d * DAY)
        summary, out = pipe.build(T0 + 2 * DAY)
        self.assertEqual(summary["top100"]["gear"], 500 - 99 + 4)
        self.assertEqual(summary["top100"]["pace"], 2.0)
        self.assertEqual(summary["top100"]["series"], [[T0 + d * DAY, 401 + 2 * d] for d in range(3)])
        roles = summary["top100"]["roles"]  # the made-up board is all 10/10/10: the first stat wins a tie, so fighters
        self.assertEqual([(r["top"], r["n"], r["fighter"]) for r in roles],
                         [(10, 10, 10), (25, 25, 25), (50, 50, 50), (100, 100, 100)])
        builds = json.loads((out / "builds.json").read_text())
        self.assertEqual((len(builds), builds[0][:3]), (100, [10, 10, 10]))  # no names, only the split and the score
        page = json.loads((out / "p" / "p050.json").read_text())
        self.assertIsNone(page["forecast"]["top100_gap"])  # already in

    def test_the_top_roles_come_from_the_main_stat_of_the_gear(self):
        pipe = Pipeline()
        board = [(f"p{i:03d}", 500 - i, *((5, 90, 5) if i % 4 == 0 else (5, 5, 90) if i % 4 == 1 else (90, 5, 5)))
                 for i in range(100)]
        pipe.run(snap({"karni": [member(lo, g) for lo, g, *_ in board]}, board=board), T0)
        summary, _ = pipe.build(T0)
        top10 = summary["top100"]["roles"][0]
        self.assertEqual((top10["tank"], top10["support"], top10["fighter"]), (3, 3, 4))  # ranks 1-10: i % 4 = 0, 1, 2

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
                "source": "TRADER", "socket": "Angriff +4", "upgrade": 4, "upgradeFocus": "DEFENSE", "bossLoot": False}
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
                         {"HELMET": ["Helm", "Helm", 6, 1, 9, 2, 73, 1, "Angriff +4", 0, 4, "DEFENSE", 0],
                          "BOOTS": ["Stiefel"]})
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
        self.assertEqual(json.loads((out / "data" / "seasons.json").read_text())["archives"], [])
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


class ArchiveTests(unittest.TestCase):
    def test_archive_freezes_generated_data_and_the_next_build_publishes_it(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}, board=[("a", 100, 80, 10, 10)]), T0)
        pipe.run(snap({"karni": [member("a", 140)]}, board=[("a", 140, 120, 10, 10)]), T0 + DAY)

        season = season_archive.archive(pipe.data, "beta-2026", "Beta 2026")

        self.assertEqual(season, {"id": "beta-2026", "label": "Beta 2026", "start": T0,
                                  "end": T0 + DAY, "archived": True})
        manifest = json.loads((pipe.data / "seasons.json").read_text())
        self.assertEqual(manifest["archives"], [season])
        archived = json.loads((pipe.data / "seasons" / "beta-2026" / "summary.json").read_text())
        self.assertEqual((archived["season"], archived["board"][0]["gear"]), (season, 140))
        self.assertFalse((pipe.data / "seasons" / "beta-2026" / "seasons").exists())

        out = Path(tempfile.mkdtemp())
        build.build(pipe.data, out, T0 + DAY)
        self.assertTrue((out / "data" / "seasons" / "beta-2026" / "p" / "a.json").exists())
        with self.assertRaises(FileExistsError):
            season_archive.archive(pipe.data, "beta-2026", "Beta 2026")
        with self.assertRaises(ValueError):
            season_archive.archive(pipe.data, "../bad", "Bad")
        with self.assertRaises(ValueError):
            season_archive.archive(pipe.data, "next", "  ")

    def test_command_line_archives_and_prints_the_season(self):
        pipe = Pipeline()
        pipe.run(snap({"karni": [member("a", 100)]}, board=[("a", 100, 80, 10, 10)]), T0)
        argv = ["archive", "--data", str(pipe.data), "--id", "beta-2026", "--label", "Beta 2026"]
        with mock.patch("sys.argv", argv), redirect_stdout(io.StringIO()) as printed:
            season_archive.main()
        self.assertEqual(printed.getvalue(), f"Beta 2026 archiviert: {T0} bis {T0}\n")

    def test_manifest_without_an_archive_list_falls_back_to_the_default(self):
        data = Path(tempfile.mkdtemp())
        (data / "seasons.json").write_text('{"archives": "x"}')
        self.assertEqual(build.season_manifest(data)["archives"], [])


GAP_ROWS = [{"silver": 900}, {"silver": 500}, {"silver": 200}, {"silver": 300}]
GAP_SCORES = [681, 681, 681, 680]


class BoardGapTests(unittest.TestCase):

    def test_a_tie_is_measured_in_silver_to_the_player_above(self):
        self.assertEqual(build.board_gap(2, GAP_SCORES, GAP_ROWS), {"ahead": False, "tie": True, "amount": 300})

    def test_the_leader_is_measured_against_the_second_place(self):
        self.assertEqual(build.board_gap(0, GAP_SCORES, GAP_ROWS), {"ahead": True, "tie": True, "amount": 400})
        gap = build.board_gap(0, [682, *GAP_SCORES[1:]], GAP_ROWS)
        self.assertEqual(gap, {"ahead": True, "tie": False, "amount": 1})

    def test_without_a_tie_the_gap_is_in_points_and_unknown_silver_gives_none(self):
        self.assertEqual(build.board_gap(3, GAP_SCORES, GAP_ROWS), {"ahead": False, "tie": False, "amount": 1})
        self.assertIsNone(build.board_gap(1, [5, 5], [{"silver": None}, {"silver": 3}]))


class HelperTests(unittest.TestCase):
    def test_value_at_and_pace(self):
        series = [[0, 10], [DAY, 20]]
        self.assertIsNone(build.value_at(series, -1))
        self.assertEqual(build.value_at(series, DAY - 1), 10)
        self.assertEqual(build.pace(series, 2 * DAY), 5.0)
        self.assertIsNone(build.pace([[0, 10]], 3600))  # under 12 h of data
        self.assertIsNone(build.pace([], 3600))

    def test_class_peers_have_a_median_and_from_four_on_a_band_of_80_percent(self):
        details = {"me": {"atk": 50, "def": 200, "sup": 10}, "fighter": {"atk": 300, "def": 50, "sup": 10},
                   **{f"t{i}": {"atk": 10 * i, "def": 200 + 10 * i, "sup": 5} for i in range(5)}}
        players = {x: {"gs": 260} for x in details}
        cls = build.class_peers("me", 260, players, details, list(details))
        self.assertEqual((cls["main"], cls["n"], cls["med"]["def"]), ("def", 5, 220))  # the fighter is left out
        self.assertEqual(cls["band"]["def"], [204, 236])
        few = build.class_peers("me", 260, players, details, ["me", "fighter", "t1"])
        self.assertEqual((few["n"], "band" in few), (1, False))
        self.assertIsNone(build.class_peers("me", 260, players, details, ["me", "fighter"]))
        self.assertEqual(build.main_stat({"atk": 5, "def": 5, "sup": 1}), "atk")  # a tie: the first

    def test_history_drops_a_player_off_the_board_and_merges_fight_digests(self):
        h = build.History([{"t": 1, "boards": {"gear": [["a", 9], ["b", 8]]}, "fightx": {"5": {"dead": [1, 0, 0]}}},
                           {"t": 2, "boards": {"gear": [["a", 9]]}, "fightx": {"5": {"power": 300}}}])
        self.assertEqual(h.rank["b"], [[1, 2], [2, None]])
        self.assertEqual(h.fightx[5], {"dead": [1, 0, 0], "power": 300})


if __name__ == "__main__":
    unittest.main()


class UpgradeTriesTests(unittest.TestCase):
    def test_the_committed_tries_are_totals_per_step(self):
        from pathlib import Path
        data = json.loads((Path(__file__).parent.parent / "src" / "upgrades.json").read_text("utf-8"))
        self.assertEqual(sorted(data["steps"]), ["1", "2", "3", "4"])
        for step in data["steps"].values():
            self.assertTrue(0 <= step["ok"] <= step["tries"])


class GuildBossTests(unittest.TestCase):
    def test_a_guild_without_members_adds_its_boss_wins_but_has_no_page(self):
        pipe = Pipeline()
        s = snap({"karni": [member("a", 100)], "solo": []})
        s["guilds"]["solo"]["boss"] = {"wins": 7, "losses": 1}
        s["guilds"]["karni"]["boss"] = {"wins": 3, "losses": 1}
        pipe.run(s, T0)
        summary, _ = pipe.build(T0 + 60)
        self.assertEqual([g["login"] for g in summary["guilds"]], ["karni"])
        self.assertEqual(summary["guild_boss"], {"guilds": 2, "wins": 10, "losses": 2})


class FinaleTests(unittest.TestCase):
    def test_the_top_story_and_the_records(self):
        import build
        self.addCleanup(setattr, build, "GEAR_SINCE", build.GEAR_SINCE)
        build.GEAR_SINCE = 0
        pipe = Pipeline()
        for step in range(6):  # every two hours: "a" leads at first, "b" from step 3 on
            a, b = 100 + step, 100 + 3 * step if step >= 3 else 99
            board = sorted([("a", a, 1, 1, 1), ("b", b, 1, 1, 1)], key=lambda r: -r[1])
            pipe.run(snap({"karni": [member("a", a, donated=10), member("b", b, donated=500)]}, board=board),
                     T0 + step * 7200)
        summary, _ = pipe.build(T0 + 6 * 7200)
        f = summary["finale"]
        self.assertEqual(f["top"]["score"], f["top"]["series"][-1][1])
        self.assertEqual(f["top"]["first"]["login"], "b")  # the first to reach the final top score
        self.assertEqual([r[0] for r in f["top"]["holders"]], ["a", "b"])
        self.assertEqual(f["top"]["ever"], 2)
        self.assertEqual(f["records"]["donors"][0][:3], ["b", "B", 500])

    def test_a_shared_top_score_belongs_to_the_first_of_the_board(self):
        import build
        self.addCleanup(setattr, build, "GEAR_SINCE", build.GEAR_SINCE)
        build.GEAR_SINCE = 0
        pipe = Pipeline()
        for step in range(3):  # the same score, "a" first (more silver)
            board = [("a", 200, 1, 1, 1), ("b", 200, 1, 1, 1)]
            pipe.run(snap({"karni": [member("a", 200), member("b", 200)]}, board=board), T0 + step * 7200)
        summary, _ = pipe.build(T0 + 3 * 7200)
        top = summary["finale"]["top"]
        self.assertEqual([r[0] for r in top["holders"]], ["a"])
        self.assertEqual(top["now"], 2)

    def test_the_time_at_the_top_runs_to_the_next_change_of_the_first_place(self):
        import build
        self.addCleanup(setattr, build, "GEAR_SINCE", build.GEAR_SINCE)
        build.GEAR_SINCE = 0
        pipe = Pipeline()
        for step, first in enumerate(["a", "a", "b", "a"]):  # every 15 minutes
            board = [(first, 200, 1, 1, 1), ("b" if first == "a" else "a", 200, 1, 1, 1)]
            pipe.run(snap({"karni": [member("a", 200), member("b", 200)]}, board=board), T0 + step * 900)
        summary, _ = pipe.build(T0 + 3 * 900)
        holders = [r[:1] + r[2:] for r in summary["finale"]["top"]["holders"]]
        self.assertEqual(holders, [["a", 0.5, 0.5], ["b", 0.25, 0.25]])


class BorderSeriesTests(unittest.TestCase):
    def test_the_border_series_skips_the_kampfkraft_era_of_the_board(self):
        pipe = Pipeline()
        for d in range(3):
            board = [(f"p{i:03d}", 500 - i + 2 * d, 10, 10, 10) for i in range(100)]
            pipe.run(snap({"karni": [member(lo, g) for lo, g, *_ in board]}, board=board), T0 + d * DAY)
        self.addCleanup(setattr, build, "GEAR_SINCE", build.GEAR_SINCE)
        build.GEAR_SINCE = T0 + DAY - build.BOARD_LAG
        summary, _ = pipe.build(T0 + 2 * DAY)
        self.assertEqual(summary["top100"]["series"], [[T0 + d * DAY, 401 + 2 * d] for d in (1, 2)])
