import unittest

from timelapse import BIN, STEP, timelapse


class FakeHistory:
    def __init__(self, gs, guild, first, last):
        self.gs, self.guild, self.first, self.last = gs, guild, first, last


class TimelapseTests(unittest.TestCase):
    def setUp(self):
        self.first = 10 * STEP
        self.last = self.first + 5 * STEP
        names = [f"p{i}" for i in range(20)]
        # everyone grows by 10 per frame; the second half of the players is only known from frame 2 on
        self.gs = {n: [[self.first + (0 if i < 10 else 2 * STEP) + k * STEP, 100 + i + 10 * k] for k in range(4)]
                   for i, n in enumerate(names)}
        self.guild = {n: [[self.first, "a" if i % 2 else "b"]] for i, n in enumerate(names)}
        self.players = {n: {"active": True} for n in names}
        self.h = FakeHistory(self.gs, self.guild, self.first, self.last)

    def test_frames_start_where_enough_players_are_known(self):
        lapse = timelapse(self.h, self.players, [[self.first, 300]])
        self.assertEqual(lapse["frames"][-1], self.last)
        self.assertGreaterEqual(lapse["frames"][0], self.first + 2 * STEP)  # before: only half of them known
        self.assertEqual([g["name"] for g in lapse["groups"]], ["Alle", "a", "b"])

    def test_percentiles_and_shares(self):
        lapse = timelapse(self.h, self.players, [[self.first, 300]])
        alle = lapse["groups"][0]
        self.assertEqual(len(alle["pct"][-1]), 101)
        self.assertLessEqual(alle["pct"][-1][0], alle["pct"][-1][100])
        for row in alle["hist"]:
            self.assertAlmostEqual(sum(row), 100, delta=0.5)
        self.assertEqual(lapse["bin"], BIN)
        self.assertEqual(lapse["border"][0], 300)

    def test_too_little_history_gives_none(self):
        h = FakeHistory({"p": [[5, 1]]}, {"p": [[5, "a"]]}, 5, 5)
        self.assertIsNone(timelapse(h, {"p": {"active": True}}, []))
        self.assertIsNone(timelapse(h, {}, []))


class TopLapseTests(unittest.TestCase):
    def test_rows_follow_the_board_with_one_index_per_player(self):
        from timelapse import top_lapse
        h = FakeHistory({}, {}, 0, 0)
        h.board_at = {7200: [["a", 10], ["b", 9]], 14400: [["b", 11], ["a", 10], ["c", 5]]}
        out = top_lapse(h, {"a": {"name": "Anna"}, "b": {}})
        self.assertEqual(out["frames"], [7200, 14400])
        self.assertEqual(out["names"], ["Anna", "b", "c"])
        self.assertEqual(out["rows"], [[[0, 10], [1, 9]], [[1, 11], [0, 10], [2, 5]]])
        h.board_at = {7200: [["a", 1]]}
        self.assertIsNone(top_lapse(h, {}))
