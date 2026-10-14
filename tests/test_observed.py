import json
import unittest

from observed import SEED, base_of, observed


def slot(name, tier, stats, socket=None, two=0, level=0, focus=None, loot=0):
    return ["Label", name, tier, *stats, 100, 0, socket, two, level, focus, loot]


class ObservedTests(unittest.TestCase):
    def test_seed_sums_match_the_tier(self):
        table = json.loads(SEED.read_text("utf-8"))
        for tier, kinds in table.items():
            for kind, forms in kinds.items():
                for form, stats in forms.items():
                    per = 3 * int(tier) if kind == "ring" else (2 if kind == "w2" else 1) * (5 * int(tier) + 3)
                    self.assertEqual(sum(stats), per, (tier, kind, form))

    def test_clean_pieces(self):
        self.assertEqual(base_of("SHIELD", slot("altairischer Turmschild", 13, [3, 65, 0])),
                         ("13", "shield", "Turmschild", [3, 65, 0]))
        self.assertEqual(base_of("WEAPON", slot("x Zweihänder des Kriegsherrn", 14, [124, 22, 0], two=1)),
                         ("14", "w2", "des Kriegsherrn", [124, 22, 0]))
        self.assertEqual(base_of("RING", slot("Ring der Wacht", 10, [10, 10, 10]))[1:3], ("ring", "der Wacht"))
        self.assertEqual(base_of("SHIELD", slot("Klinge des Ritters", 10, [45, 8, 0]))[1], "w1")

    def test_stone_and_upgrade_are_taken_out(self):
        v = slot("Brust des Pilgers +2", 13, [0, 24 + 4, 44 + 3], socket="Verteidigung +4", level=2, focus="SUPPORT")
        self.assertEqual(base_of("CHEST", v), ("13", "armor", "des Pilgers", [0, 24, 44]))

    def test_unclear_pieces_are_skipped(self):
        self.assertIsNone(base_of("CHEST", ["Brust"]))
        self.assertIsNone(base_of("CHEST", slot("Brust des Pilgers", 13, [0, 24, 44], loot=1)))
        self.assertIsNone(base_of("CHEST", slot("Brust des Pilgers", 13, [0, 24, 50])))      # points without an upgrade
        self.assertIsNone(base_of("CHEST", slot("Brust des Pilgers", 13, [0, 24, 47], level=1)))  # no focus
        self.assertIsNone(base_of("CHEST", slot("Brust des Pilgers", 13, [0, 24, 47], level=1, focus="ATTACK")))
        self.assertIsNone(base_of("CHEST", slot("Brust Plattenpanzer", 13, [0, 24, 44])))  # no form name

    def test_profiles_add_to_the_table(self):
        shield = slot("altairischer Turmschild", 15, [4, 74, 0])
        state = {"watch": {"a": {"slots": {"SHIELD": shield, "HEAD": ["Helm"]}}, "b": {}}}
        table = observed(state)
        self.assertEqual(table["15"]["shield"]["Turmschild"], [4, 74, 0])
        self.assertEqual(table["13"]["shield"]["Turmschild"], [3, 65, 0])
        self.assertEqual(observed({}), json.loads(SEED.read_text("utf-8")))
