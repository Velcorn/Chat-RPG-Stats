"""Fight statistics: the digests the collector keeps and the sums the build makes of them."""
import itertools
import json
import statistics
import time
import unittest
from datetime import UTC, datetime

import collect
import fightstats

MINUS = chr(0x2212)  # the game writes a real minus sign
NOW = datetime(2026, 10, 2, 22, 0, tzinfo=UTC).timestamp()


def fighter(role, alive, gold, **numbers):
    return {"role": role, "alive": alive, "gold": gold, "login": "geheim", **numbers}


def detail(**extra):
    return {"fighters": [fighter("TANK", True, "+2 Gold 10 Silber", damage=50, damageTaken=60),
                         fighter("FIGHTER", False, f"{MINUS}3 Gold 36 Silber", damage=150, damageTaken=10),
                         fighter("FIGHTER", True, "+4 Gold 90 Silber", damage=190, damageTaken=6),
                         fighter("SUPPORT", False, f"{MINUS}1 Gold", damage=10, damageTaken=4, healing=20, boosted=8)],
            "crowd": {"tally": {"damage": 400, "taken": 80, "healing": 20, "boosted": 8}},
            "round": 7, "maxRounds": 39, "hp": 0, "maxHp": 1000, **extra}


def fight(i, outcome="VICTORY", kind="ADVENTURE", hour=20, **extra):
    return {"id": i, "channel": "sola", "kind": kind, "name": "Koboldmarkt", "difficulty": 2, "bossLevel": 0,
            "outcome": outcome, "fighters": 4, "endedAt": f"2026-10-02T{hour:02d}:10:00Z", **extra}


class DigestTests(unittest.TestCase):
    def test_silver_value_reads_the_games_amounts(self):
        self.assertEqual(collect.silver_value("+4 Gold 65 Silber"), 465)
        self.assertEqual(collect.silver_value(f"{MINUS}3 Gold 36 Silber"), -336)
        self.assertEqual(collect.silver_value("+50 Silber"), 50)
        self.assertIsNone(collect.silver_value("nichts"))
        self.assertIsNone(collect.silver_value(None))

    def test_detail_digest_keeps_sums_and_no_names(self):
        d = collect.detail_digest(detail())
        self.assertEqual(d["roles"], [1, 2, 1])
        self.assertEqual(d["dead"], [0, 1, 1])
        self.assertEqual((d["dmg"], d["taken"], d["heal"], d["boost"]), (400, 80, 20, 8))
        self.assertEqual(d["pay"], [round((210 + 490) / 2), round((-336 - 100) / 2)])
        self.assertEqual(d["rsum"], [[50, 60, 0, 0], [340, 16, 0, 0], [10, 4, 20, 8]])
        self.assertNotIn("geheim", str(d))

    def test_live_digest_takes_the_engine_numbers(self):
        d = collect.live_digest({"averageGear": 196, "averagePower": 222, "recommendedGear": 0, "minGear": 0,
                                 "battle": {"secondsFought": 50, "enraged": False, "tanksStanding": 3,
                                            "tanksTotal": 4, "groupStrength": 10, "groupStrengthMax": 12}})
        self.assertEqual((d["gear"], d["power"], d["secs"], d["tanks"]), (196, 222, 50, [3, 4]))
        d = collect.live_digest({"groupGear": 512, "groupGearFinal": True, "battle": {}})
        self.assertEqual((d["gg"], d["ggf"]), (512, True))

    def test_record_keeps_details_of_new_fights_once(self):
        snap = {"fights": [{"id": 5, "kind": "BOSS"}], "details": {5: detail()}, "guilds": {}, "boards": {},
                "watch": {}, "channels": [],
                "live": [{"archiveId": 5, "phase": "VICTORY", "endedAt": "x", "averagePower": 300, "battle": {}}]}
        cur = collect.state_from(snap, {})
        rec = collect.record(snap, {}, cur, 1)
        self.assertEqual(rec["fightx"][5]["power"], 300)
        self.assertEqual(rec["fightx"][5]["dead"], [0, 1, 1])
        self.assertEqual((cur["detail_last"], cur["live_seen"]), (5, [5]))
        again = collect.record({**snap, "details": {}}, cur, collect.state_from({**snap, "details": {}}, cur), 2)
        self.assertNotIn("fightx", again)

    def test_record_counts_fighters_by_their_known_stats(self):
        fighters = [{"login": "A", "role": "TANK", "alive": False, "damageTaken": 30},
                    {"login": "fremd", "role": "TANK", "alive": True, "damageTaken": 99}]  # unknown stats: left out
        snap = {"fights": [{"id": 5, "kind": "BOSS"}], "details": {5: {"fighters": fighters}}, "guilds": {},
                "boards": {}, "watch": {}, "channels": []}
        cur = {**collect.state_from(snap, {}), "details": {"a": {"atk": 10, "def": 254, "sup": 3}}}
        self.assertEqual(collect.record(snap, {}, cur, 1)["fightx"][5]["sx"], {"TANK": {"def": {"250": [1, 1, 30]}}})

    def test_rules_are_kept_as_changes(self):
        snap = {"fights": [], "guilds": {}, "boards": {}, "watch": {}, "rules": {"a": 1, "playWindowOpenNow": True},
                "channels": [{"login": "sola", "enabled": True, "live": True, "chatMode": "SLOW"}]}
        cur = collect.state_from(snap, {})
        self.assertEqual(cur["rules"], {"a": 1})
        self.assertNotIn("chat", cur)  # the chat mode is no longer kept (0.25.0)
        later = collect.state_from({**snap, "rules": {"a": 2}}, cur)
        self.assertEqual(collect.record(snap, cur, later, 2)["rules"], {"a": 2})


class StatsTests(unittest.TestCase):
    def setUp(self):
        self.fights = [fight(1), fight(2, "DEFEAT", hour=21), fight(3, kind="BOSS", hour=21), fight(4, hour=8)]
        d = collect.detail_digest(detail())
        self.extra = {1: d, 2: {**d, "dead": [1, 2, 1], "hp": 400, "power": 200, "rec": 250, "gear": 150},
                      3: {**d, "power": 320, "rec": 250, "gear": 200}}

    def stats(self):
        return fightstats.fight_stats(self.fights, self.extra, NOW)

    def test_death_share_counts_every_fighter_of_the_fights_with_details(self):
        s = self.stats()
        self.assertEqual(s["detail"], 3)
        self.assertEqual(s["total"]["death"], round(100 * (2 + 4 + 2) / 12, 1))
        self.assertEqual(s["total"]["death_win"], 50.0)
        self.assertEqual(s["total"]["death_loss"], 100.0)

    def test_roles_and_per_fighter_numbers(self):
        s = self.stats()
        self.assertEqual([r["role"] for r in s["roles"]], ["TANK", "FIGHTER", "SUPPORT"])
        self.assertEqual(s["roles"][1]["share"], 50.0)
        self.assertEqual(s["roles"][1]["death"], 50.0)  # won fights only: the lost fight 2 would make it 66.7
        self.assertEqual(s["total"]["dmg"], 100)

    def test_what_each_role_did_per_head(self):
        s = self.stats()
        self.assertEqual([(r["dmg"], r["taken"], r["heal"], r["boost"]) for r in s["roles"]],
                         [(50, 60, 0, 0), (170, 8, 0, 0), (10, 4, 20, 8)])
        self.assertEqual(s["total"]["boost"], 2)

    def test_fights_without_a_tally_do_not_pull_the_averages_down(self):
        self.extra[4] = collect.detail_digest(detail(crowd={"tally": {"damage": 0, "taken": 0, "healing": 0,
                                                                      "boosted": 0}}))
        s = self.stats()
        self.assertEqual((s["detail"], s["total"]["dmg"], s["total"]["boost"]), (4, 100, 2))

    def test_fallen_per_fight_and_for_the_power_list(self):
        self.assertEqual(fightstats.fallen(self.extra[2]), {"dead": 4, "death": 100.0})
        self.assertEqual(fightstats.fallen(self.extra[1]), {"dead": 2, "death": 50.0})
        self.assertEqual(fightstats.fallen(None), {})
        recent = {r["id"]: r for r in self.stats()["power"]["recent"]}
        self.assertEqual(recent[2]["death"], 100.0)

    def test_fights_without_details_still_count_for_time_and_channel(self):
        s = self.stats()
        self.assertEqual((s["hours"][10]["n"], s["hours"][22]["n"], s["hours"][23]["n"]), (1, 1, 2))  # Berlin time
        self.assertEqual(s["channels"][0]["n"], 4)
        self.assertEqual(s["daily"][-1]["n"], 4)

    def test_power_against_the_recommendation(self):
        p = self.stats()["power"]
        self.assertEqual((p["n"], p["avg"], p["rec"]), (2, 260, 250))
        self.assertEqual([m["n"] for m in p["margins"]], [0, 1, 0, 1])  # 200 / 250 = 0.8, 320 / 250 = 1.28
        self.assertEqual((p["margins"][1]["wins"], p["margins"][3]["wins"]), (0, 1))

    def test_boss_life_left_in_defeats(self):
        row = next(r for r in self.stats()["types"] if r["kind"] == "ADVENTURE")
        self.assertEqual(row["boss_left"], 40.0)

    def test_old_fights_leave_the_window(self):
        old = fight(9, endedAt="2026-08-01T10:00:00Z")
        self.assertEqual(fightstats.fight_stats([old], {}, NOW)["fights"], 0)

    def test_no_details_means_no_death_numbers(self):
        s = fightstats.fight_stats([fight(1)], {}, NOW)
        self.assertEqual((s["detail"], s["roles"], s["total"]["detail"]), (0, [], 0))
        self.assertNotIn("death", s["total"])


class WhoseTests(unittest.TestCase):
    def test_digest_keeps_the_guild_the_summoner_and_the_treasury_change(self):
        d = collect.detail_digest(detail(guildName="Karni", summonedBy="sola", guildOnly=True,
                                         treasuryChange=f"{MINUS}12 Gold 50 Silber"))
        self.assertEqual((d["gn"], d["by"], d["gc"], d["go"]), ("Karni", "sola", -1250, True))
        plain = collect.detail_digest(detail(guildName=None, treasuryChange="was anderes", guildOnly=False))
        self.assertFalse({"gn", "by", "gc", "go"} & set(plain))
        self.assertEqual(fightstats.whose(d), {"gn": "Karni", "by": "sola", "gc": -1250})
        self.assertEqual(fightstats.whose(None), {})

    def test_guild_fights_count_raids_and_summoned_bosses_per_guild(self):
        fights = [fight(1, kind="RAID"), fight(2, "DEFEAT", kind="RAID"), fight(3, "DEFEAT", kind="RAID"),
                  fight(4, kind="BOSS"), fight(5, "DEFEAT", kind="BOSS"), fight(6, kind="BOSS"),
                  fight(7, kind="RAID"), {**fight(8, kind="RAID"), "endedAt": "2026-08-01T10:00:00Z"}]
        extra = {1: {"gn": "Karni", "gc": 300}, 2: {"gn": "Karni", "gc": -1000}, 3: {"gn": "Karni"},
                 4: {"gn": "Karni", "by": "sola"}, 5: {"gn": "Karni", "by": "sola"}, 6: {"gn": "Karni"},
                 7: {"gn": "Anders"}, 8: {"gn": "Karni", "gc": -9}}
        rows = fightstats.guild_fights(fights, extra, NOW)
        self.assertEqual(rows[0], {"guild": "Karni", "raids": 3, "raid_wins": 1, "raid_known": 2, "lost": 1000,
                                   "won": 300, "bosses": 2, "boss_wins": 1})
        self.assertEqual((rows[1]["guild"], rows[1]["raids"], rows[1]["raid_known"]), ("Anders", 1, 0))
        self.assertEqual(fightstats.guild_fights(fights, {}, NOW), [])


class WinOddsTests(unittest.TestCase):
    def test_the_curve_rises_through_the_fights_and_crosses_half_between_them(self):
        now = fightstats.iso_ts("2026-10-11T12:00:00Z")
        fights, extra = [], {}
        for i, (power, won) in enumerate([(70, 0), (75, 0), (80, 0), (85, 1), (90, 0), (95, 1), (100, 1), (110, 1)]):
            fights.append({"id": i, "kind": "BOSS", "name": "Drache", "outcome": "VICTORY" if won else "DEFEAT",
                           "endedAt": "2026-10-11T10:00:00Z"})
            extra[i] = {"power": power, "rec": 100}
        fights.append({"id": 99, "kind": "BOSS", "name": "alt", "outcome": "DEFEAT", "endedAt": "2026-09-01T10:00:00Z"})
        extra[99] = {"power": 50, "rec": 100}  # older than 30 days
        odds = fightstats.win_odds(fights, extra, now)
        self.assertEqual((odds["n"], odds["points"][0]), (8, [0.7, 0, "Drache"]))
        fit = odds["fit"]
        self.assertLess(fit[0][1], 20)
        self.assertGreater(fit[-1][1], 80)
        self.assertTrue(all(a[1] <= b[1] for a, b in itertools.pairwise(fit)))
        self.assertTrue(0.8 < odds["mid"] < 0.95)

    def test_the_game_group_gear_replaces_the_kampfkraft_once_enough_fights_have_it(self):
        now = fightstats.iso_ts("2026-10-11T12:00:00Z")
        fights, extra = [], {}
        for i in range(12):
            fights.append({"id": i, "kind": "BOSS", "name": "Drache", "outcome": "VICTORY" if i >= 5 else "DEFEAT",
                           "endedAt": "2026-10-11T10:00:00Z"})
            extra[i] = {"power": 70 + 3 * i, "gear": 60, "rec": 100, "gg": 90 + 3 * i if i != 4 else None}
        odds = fightstats.win_odds(fights, extra, now)
        self.assertEqual((odds["basis"], odds["n"], odds["points"][0]), ("gg", 11, [0.9, 0, "Drache"]))  # 4 has none
        stats = fightstats.fight_stats(fights, extra, now)
        self.assertEqual(stats["power"]["basis"], "gg")
        self.assertEqual(sum(m["n"] for m in stats["power"]["margins"]), 11)
        few = {i: {**d, "gg": d["gg"] if i < 5 else None} for i, d in extra.items()}  # under GG_MIN: the Kampfkraft
        self.assertEqual((fightstats.win_odds(fights, few, now)["basis"], fightstats.win_odds(fights, few, now)["n"]),
                         ("power", 12))

    def test_a_boss_made_stronger_leaves_its_old_fights_out_of_the_power_numbers(self):
        now = fightstats.iso_ts("2026-10-11T12:00:00Z")
        fights, extra = [], {}
        for i, (name, rec) in enumerate([("Alt", 365), ("Alt", 365), ("Neu", 470), ("Neu", 470), ("Neu", 400)]):
            fights.append({"id": i, "kind": "BOSS", "name": name, "outcome": "VICTORY", "fighters": 10,
                           "endedAt": "2026-10-11T10:00:00Z"})
            extra[i] = {"power": 400, "gear": 300, "rec": rec}
        fights.append({"id": 9, "kind": "ADVENTURE", "name": "Moor", "outcome": "VICTORY", "fighters": 10,
                       "endedAt": "2026-10-11T10:00:00Z"})
        extra[9] = {"power": 300, "gear": 250, "rec": None}
        boss_rec = {"Neu": 470, "Alt": 600, "Ohne": 0}
        odds = fightstats.win_odds(fights, extra, now, boss_rec=boss_rec)
        self.assertEqual(odds["n"], 2)  # the two 470 ones; "Alt" is 600 now, the 400 one is an old "Neu"
        stats = fightstats.fight_stats(fights, extra, now, boss_rec=boss_rec)
        self.assertEqual(stats["power"]["n"], 3)  # the two 470 ones and the adventure
        rows = {r["name"]: r for r in stats["types"]}
        self.assertEqual((rows["Neu"]["rec"], rows["Alt"]["power"], rows["Moor"]["power"]), (470, None, 300))
        self.assertEqual(fightstats.win_odds(fights, extra, now)["n"], 5)  # without the compendium: all of them

    def test_few_fights_or_one_outcome_give_no_curve(self):
        now = fightstats.iso_ts("2026-10-11T12:00:00Z")
        fights = [{"id": i, "kind": "BOSS", "name": "D", "outcome": "VICTORY", "endedAt": "2026-10-11T10:00:00Z"}
                  for i in range(9)]
        extra = {i: {"power": 90 + i, "rec": 100} for i in range(9)}
        self.assertEqual(fightstats.win_odds(fights, extra, now)["fit"], [])
        self.assertEqual(fightstats.win_odds(fights[:3], extra, now)["n"], 3)

    def test_the_fit_stops_on_a_flat_problem(self):
        self.assertEqual(fightstats.logistic_fit([1.0, 1.0], [0, 1], ridge=0), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()


class WindowAndOrderTests(unittest.TestCase):
    def test_old_fights_leave_the_window(self):
        old = fight(1, hour=10, endedAt="2026-06-01T10:00:00Z")
        new = fight(2, "DEFEAT")
        types = fightstats.fight_stats([old, new], {}, NOW)["types"]
        self.assertEqual([(t["n"], t["wins"]) for t in types], [(1, 0)])
        self.assertIsNone(fightstats.iso_ts(None))

    def test_types_are_ordered_by_win_rate_then_number_of_fights(self):
        win, lose = "VICTORY", "DEFEAT"

        def f(i, kind, difficulty, outcome):
            return {**fight(i, outcome, kind), "difficulty": difficulty, "name": f"Abenteuer {difficulty}"}
        fights = [f(1, "ADVENTURE", 1, win), f(2, "ADVENTURE", 1, lose),
                  f(3, "RAID", 1, win), f(4, "RAID", 1, win), f(5, "RAID", 1, lose), f(6, "RAID", 1, lose),
                  f(7, "ADVENTURE", 2, win), f(8, "RAID", 2, win),
                  f(9, "ADVENTURE", 3, win), f(10, "ADVENTURE", 3, win), f(11, "ADVENTURE", 3, win)]
        types = fightstats.fight_stats(fights, {}, NOW)["types"]
        self.assertEqual([(t["kind"], t["n"], t["wins"]) for t in types],
                         [("ADVENTURE", 3, 3), ("ADVENTURE", 1, 1), ("RAID", 1, 1), ("RAID", 4, 2),
                          ("ADVENTURE", 2, 1)])

    def test_a_game_version_is_cut_out_by_time(self):
        before = fight(1, hour=10, endedAt="2026-10-03T10:00:00Z")
        after = fight(2, endedAt="2026-10-03T21:00:00Z")
        undated = {**fight(3), "endedAt": None}
        args = ([before, after, undated], {}, NOW + 86400)
        self.assertEqual(fightstats.fight_stats(*args)["fights"], 3)
        self.assertEqual(fightstats.fight_stats(*args, lo=fightstats.UPDATE)["fights"], 1)
        self.assertEqual(fightstats.fight_stats(*args, hi=fightstats.UPDATE)["fights"], 1)


class StatCurveTests(unittest.TestCase):
    """Fighters counted by role and stat, without names (0.27.0)."""

    def test_the_digest_counts_by_role_and_stat_and_keeps_no_name(self):
        d = {"fighters": [{"login": "Anna1", "role": "TANK", "alive": True, "damageTaken": 100},
                          {"login": "berta", "role": "TANK", "alive": False, "damageTaken": 140},
                          {"login": "hau", "role": "FIGHTER", "alive": True, "damage": 900},
                          {"login": "fremd", "role": "SUPPORT", "alive": True, "boosted": 50}]}
        stats = {"anna1": {"atk": 10, "def": 204, "sup": 5}, "berta": {"atk": 10, "def": 209, "sup": 5},
                 "hau": {"atk": 151, "def": 80, "sup": 0}}
        sx = collect.stat_digest(d, stats)
        self.assertEqual(sx["TANK"], {"def": {"200": [2, 1, 240]}})
        self.assertEqual(sx["FIGHTER"], {"atk": {"150": [1, 0, 900]}, "def": {"80": [1, 0, 0]}})
        self.assertNotIn("SUPPORT", sx)  # unknown stats: left out
        self.assertFalse({"anna1", "berta", "hau"} & set(str(sx).lower().replace("'", " ").split()))
        self.assertIsNone(collect.stat_digest({"fighters": []}, stats))

    def test_player_stats_prefer_the_gear_of_a_kept_profile(self):
        state = {"details": {"a": {"atk": 1, "def": 2, "sup": 3}, "b": {"atk": 4, "def": 5, "sup": 6}},
                 "watch": {"a": {"slots": {"HELMET": ["Helm", "h", 9, 10, 20, 30], "BOOTS": ["Stiefel"]}}}}
        self.assertEqual(collect.player_stats(state), {"a": {"atk": 10, "def": 20, "sup": 30},
                                                       "b": {"atk": 4, "def": 5, "sup": 6}})

    def test_curves_add_up_won_boss_fights_per_boss(self):
        sx = {"TANK": {"def": {"200": [3, 1, 300], "210": [1, 1, 150]}}}
        fights = [{**fight(1, kind="BOSS", name="Loserqueue"), "endedAt": "2026-10-05T10:00:00Z"},
                  {**fight(2, "DEFEAT", kind="BOSS", name="Loserqueue"), "endedAt": "2026-10-05T11:00:00Z"},
                  {**fight(3, kind="BOSS", name="Loserqueue"), "endedAt": "2026-10-05T12:00:00Z"}]
        extra = {1: {"sx": sx}, 2: {"sx": sx}, 3: {"sx": sx}}
        curves = fightstats.stat_curves(fights, extra, NOW, step=20)
        self.assertEqual(len(curves), 1)
        self.assertEqual(curves[0]["fights"], 2)  # the lost one doesn't count
        self.assertEqual(curves[0]["roles"]["TANK"]["def"], [[200, 8, 50.0, 112]])

    def test_curves_list_the_strongest_boss_first(self):
        sx = {"TANK": {"def": {"200": [3, 1, 300]}}}
        names = ["Loserqueue", "Ostmauer", "Finanzamt", "Neuer"]
        fights = [{**fight(i, kind="BOSS", name=n), "endedAt": "2026-10-05T10:00:00Z"} for i, n in enumerate(names, 1)]
        fights += [{**fight(9, kind="BOSS", name="Finanzamt"), "endedAt": "2026-10-05T11:00:00Z"}]
        extra = {f["id"]: {"sx": sx} for f in fights}
        rec = {"Loserqueue": 400, "Ostmauer": 600, "Finanzamt": 270}
        order = [c["boss"] for c in fightstats.stat_curves(fights, extra, NOW, boss_rec=rec)]
        self.assertEqual(order, ["Ostmauer", "Loserqueue", "Finanzamt", "Neuer"])  # unknown boss last


class PayoutTests(unittest.TestCase):
    def rows(self):
        fights = [{**fight(1, kind="BOSS"), "name": "Boss A"},
                  {**fight(2, kind="BOSS"), "name": "Boss A"},
                  fight(3), fight(4, "DEFEAT"), fight(5, kind="RAID"),
                  {**fight(6), "endedAt": "2026-08-01T10:00:00Z"}]
        extra = {1: {"pay": [900, 500]}, 2: {"pay": [910, None]}, 3: {"pay": [500, 100]},
                 4: {"pay": [-100, -300]}, 5: {"pay": [None, None]}, 6: {"pay": [999, 1]}}
        return fightstats.payout_rows(fights, extra, since=NOW - 86400 * 20)

    def test_rows_keep_the_fights_with_a_payout_after_the_cut(self):
        self.assertEqual([r["id"] for r in self.rows()], [1, 2, 3, 4])  # no payout (raid) or too old: left out

    def test_spread_per_type_has_std_variance_and_the_outcome_means(self):
        types = {t["name"]: t for t in fightstats.payout(self.rows())}
        boss = types["Boss A"]
        self.assertEqual((boss["n"], boss["alive"]["mean"], boss["alive"]["std"], boss["alive"]["var"]),
                         (2, 905, 7.1, 50))
        self.assertEqual((boss["alive"]["min"], boss["alive"]["med"], boss["alive"]["max"]), (900, 905, 910))
        self.assertEqual(boss["fallen"]["n"], 1)  # the fight without fallen fighters adds none
        story = types["Koboldmarkt"]
        self.assertEqual((story["win"], story["loss"], story["alive"]["mean"]), (500, -100, 200))

    def test_a_single_fight_has_no_spread(self):
        s = fightstats.spread([300])
        self.assertEqual((s["std"], s["var"]), (0.0, 0))

    def test_csv_has_one_line_per_fight(self):
        lines = fightstats.payout_csv(self.rows()).splitlines()
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].startswith("fight_id,ended_at,kind"))
        self.assertIn("910,", lines[2] + ",")


class PayGroupTests(unittest.TestCase):
    def test_the_digest_keeps_the_spread_of_every_fighter_without_names(self):
        d = collect.detail_digest(detail())
        a = d["pg"]["a"]  # 210 and 490 stood, -336 and -100 fell
        self.assertEqual((a["n"], a["s"], a["lo"], a["hi"], a["q"]), (2, 700, 210, 490, 210 ** 2 + 490 ** 2))
        self.assertEqual(a["h"], {"200": 1, "450": 1})
        self.assertEqual(d["pg"]["d"]["lo"], -336)
        self.assertNotIn("geheim", str(d))

    def test_pooled_spread_is_over_the_fighters_not_the_fights(self):
        values = [[100, 300], [200, 400, 600]]
        groups = [collect.pay_group(v) for v in values]
        p = fightstats.pooled(groups)
        flat = [100, 300, 200, 400, 600]
        self.assertEqual((p["n"], p["fights"], p["mean"], p["min"], p["max"]), (5, 2, 320, 100, 600))
        self.assertAlmostEqual(p["std"], round(statistics.stdev(flat), 1))
        self.assertEqual((p["q1"], p["med"], p["q3"]), (200, 300, 400))  # bucket lower edges of 50 silver
        self.assertIsNone(fightstats.pooled([None]))


class LootTests(unittest.TestCase):
    def fighters(self):
        def f(**kw):
            return {"login": "geheim", "lootEligible": True, **kw}
        return [f(lootItems=[{"name": "Helm", "tier": 13, "guaranteed": False}]), f(),
                f(lootItems=[{"name": "Stab", "tier": 14, "guaranteed": False},
                             {"name": "Schicksal", "tier": 14, "guaranteed": True}]),
                f(lootEligible=False), f(lootItems=[{"name": "Ring", "tier": 13, "guaranteed": False}])]

    def test_digest_counts_drops_per_tier_without_names(self):
        d = collect.loot_digest(self.fighters())
        self.assertEqual(d, {"el": 4, "dr": {"13": 2, "14": 1}, "gu": 1, "wn": 3})
        self.assertNotIn("geheim", str(d))
        self.assertIn("lt", collect.detail_digest(detail()))

    def rows(self):
        fights = [{**fight(1, kind="BOSS"), "name": "Boss A"}, {**fight(2, kind="BOSS"), "name": "Boss A"},
                  fight(3, kind="RAID"), fight(4)]
        extra = {1: {"lt": {"el": 100, "dr": {"13": 4}, "gu": 0, "wn": 4}},
                 2: {"lt": {"el": 300, "dr": {"13": 6, "14": 2}, "gu": 1, "wn": 8}},
                 3: {"lt": {"el": 10, "dr": {}, "gu": 0, "wn": 0}}, 4: {}}
        return fightstats.loot_rows(fights, extra)

    def test_rows_need_a_digest_and_raids_drop_out_of_the_summary(self):
        self.assertEqual([r["id"] for r in self.rows()], [1, 2, 3])
        self.assertEqual([t["name"] for t in fightstats.loot(self.rows())], ["Boss A"])

    def test_rate_per_100_fighters_and_tiers(self):
        boss = fightstats.loot(self.rows())[0]
        self.assertEqual((boss["n"], boss["eligible"], boss["items"], boss["per100"]), (2, 400, 12, 3.0))
        self.assertEqual((boss["tiers"], boss["guaranteed"], boss["winners"]), ([(13, 10), (14, 2)], 1, 12))
        self.assertEqual((boss["per_fight"]["mean"], boss["per_fight"]["min"], boss["per_fight"]["max"]), (6, 4, 8))

    def test_csv_has_one_line_per_fight(self):
        lines = fightstats.loot_csv(self.rows()).splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[2].endswith("13:6;14:2"))


class BackfillTests(unittest.TestCase):
    def test_a_backfill_record_adds_digests_without_counting_as_a_run(self):
        import backfill
        import build
        t = int(NOW)
        fights = [{**fight(1, kind="BOSS"), "name": "Boss A", "endedAt": "2026-10-02T20:10:00Z"},
                  {**fight(2, kind="RAID"), "endedAt": "2026-10-02T20:20:00Z"},
                  {**fight(3), "endedAt": "2026-08-01T10:00:00Z"}]
        records = [{"t": t, "fights": fights, "fightx": {"1": {"pay": [900, 500]}}},
                   {"t": t + 60, "part": "backfill", "req": 3,
                    "fightx": {"1": {"lt": {"el": 5, "dr": {}, "gu": 0, "wn": 0}}}}]
        h = build.History(iter(records))
        self.assertEqual((h.runs, h.last), (1, t))
        self.assertEqual(sorted(h.fightx[1]), ["lt", "pay"])
        self.assertEqual(backfill.missing(h, NOW), [])  # fight 1 has its digest, the raid and the old fight don't count
        h2 = build.History(iter(records[:1]))
        self.assertEqual([f["id"] for f in backfill.missing(h2, NOW)], [1])


class CoverageGapTests(unittest.TestCase):
    def test_spread_of_nothing_is_none(self):
        self.assertIsNone(fightstats.spread([]))

    def test_a_type_without_a_survivor_count_is_left_out(self):
        row = {"kind": "BOSS", "name": "X", "level": 1, "alive": None, "outcome": "VICTORY"}
        self.assertEqual(fightstats.payout([row]), [])

    def test_backfill_reads_the_missing_reports_and_skips_a_gone_one(self):
        import io
        import tempfile
        import urllib.error
        from contextlib import redirect_stdout
        from pathlib import Path
        from unittest import mock

        import backfill
        import collect
        now = time.time()
        stamp = datetime.fromtimestamp(now - 3600, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        fights = [{**fight(1, kind="BOSS"), "endedAt": stamp}, {**fight(2, kind="BOSS"), "endedAt": stamp}]

        class FakeSite:
            requests = 2

            def get(self, path):
                if path.endswith("/2"):
                    raise urllib.error.HTTPError(path, 404, "gone", None, io.BytesIO())
                return {}

        with tempfile.TemporaryDirectory() as tmp:
            days = Path(tmp) / "days"
            days.mkdir()
            (days / "2026-10-27.jsonl").write_text(json.dumps({"t": int(now), "fights": fights}) + "\n")
            digest = {"pg": {"n": 1}, "lt": {"el": 1}}
            argv = ["backfill", "--data", tmp]
            with mock.patch("sys.argv", [*argv, "--dry"]), redirect_stdout(io.StringIO()):
                self.assertEqual(backfill.main(), 0)
            with (mock.patch("sys.argv", argv), mock.patch.object(collect, "Site", FakeSite),
                  mock.patch.object(collect, "detail_digest", return_value=digest), redirect_stdout(io.StringIO())):
                self.assertEqual(backfill.main(), 0)
            out = list(days.glob("*-backfill.jsonl"))
            self.assertEqual(len(out), 1)
            self.assertEqual(list(json.loads(out[0].read_text())["fightx"]), ["1"])
            (days / "2026-10-27.jsonl").write_text("")
            with mock.patch("sys.argv", argv), redirect_stdout(io.StringIO()):
                self.assertEqual(backfill.main(), 0)

    def test_top_story_pads_the_series_with_the_score_before_the_window(self):
        from types import SimpleNamespace

        import finale

        def history(top_score):
            return SimpleNamespace(leader=[[100, "a"], [200, "b"]], last=300, top_score=top_score,
                                   gs={"a": [[100, 12]], "b": [[200, 12]]}, board_last=[["a", 12]])

        self.assertIsNone(finale.top_story(history([[50, 10]]), {}, since=400))
        self.assertIsNone(finale.top_story(history([]), {}, since=150))
        top = finale.top_story(history([[50, 10], [250, 12]]), {}, since=150)
        self.assertEqual(top["series"][0], [150, 10])
