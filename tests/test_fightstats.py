"""Fight statistics: the digests the collector keeps and the sums the build makes of them."""
import unittest
from datetime import UTC, datetime

import collect
import fightstats

MINUS = chr(0x2212)  # the game writes a real minus sign
NOW = datetime(2026, 10, 2, 22, 0, tzinfo=UTC).timestamp()


def fighter(role, alive, gold):
    return {"role": role, "alive": alive, "gold": gold, "login": "geheim"}


def detail(**extra):
    return {"fighters": [fighter("TANK", True, "+2 Gold 10 Silber"),
                         fighter("FIGHTER", False, f"{MINUS}3 Gold 36 Silber"),
                         fighter("FIGHTER", True, "+4 Gold 90 Silber"), fighter("SUPPORT", False, f"{MINUS}1 Gold")],
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
        self.assertNotIn("geheim", str(d))

    def test_live_digest_takes_the_engine_numbers(self):
        d = collect.live_digest({"averageGear": 196, "averagePower": 222, "recommendedGear": 0, "minGear": 0,
                                 "battle": {"secondsFought": 50, "enraged": False, "tanksStanding": 3,
                                            "tanksTotal": 4, "groupStrength": 10, "groupStrengthMax": 12}})
        self.assertEqual((d["gear"], d["power"], d["secs"], d["tanks"]), (196, 222, 50, [3, 4]))

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

    def test_rules_and_chat_mode_are_kept_as_changes(self):
        snap = {"fights": [], "guilds": {}, "boards": {}, "watch": {}, "rules": {"a": 1, "playWindowOpenNow": True},
                "channels": [{"login": "sola", "enabled": True, "live": True, "chatMode": "SLOW"}]}
        cur = collect.state_from(snap, {})
        self.assertEqual(cur["rules"], {"a": 1})
        self.assertEqual(cur["chat"], {"sola": "SLOW"})
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
        self.assertEqual(s["roles"][1]["death"], round(100 * (1 + 2 + 1) / 6, 1))
        self.assertEqual(s["total"]["dmg"], 100)

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


if __name__ == "__main__":
    unittest.main()
