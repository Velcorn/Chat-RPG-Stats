"""The watchlist issue form: add, remove, refuse anything that isn't a plain existing Twitch login."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import watchlist


def body(action, login):
    return f"### Was soll passieren?\n\n{action}\n\n### Twitch-Name\n\n{login}\n"


class WatchlistTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "watchlist.txt"
        self.path.write_text("# Kommentar\nvelcorn\n")

    def test_add_and_remove(self):
        changed, summary, _ = watchlist.apply(body("Hinzufügen", "@Sola"), self.path, exists=lambda _: True)
        self.assertEqual((changed, summary), (True, "add sola"))
        self.assertIn("sola\n", self.path.read_text())
        changed, _, msg = watchlist.apply(body("Hinzufügen", "sola"), self.path, exists=lambda _: True)
        self.assertFalse(changed)
        self.assertIn("schon", msg)
        changed, summary, _ = watchlist.apply(body("Entfernen", "velcorn"), self.path)
        self.assertEqual((changed, summary), (True, "remove velcorn"))
        self.assertEqual(self.path.read_text(), "# Kommentar\nsola\n")

    def test_refusals(self):
        for login in ("a b", "x", "name; rm -rf /", "<script>"):
            changed, _, _ = watchlist.apply(body("Hinzufügen", login), self.path, exists=lambda _: True)
            self.assertFalse(changed, login)
        changed, _, msg = watchlist.apply(body("Hinzufügen", "gibtsnicht"), self.path, exists=lambda _: False)
        self.assertFalse(changed)
        self.assertIn("gibt es im Spiel nicht", msg)

    def test_full_list_and_missing_entries(self):
        self.path.write_text("".join(f"spieler{i:03d}\n" for i in range(watchlist.MAX)))
        changed, _, msg = watchlist.apply(body("Hinzufügen", "neuer"), self.path, exists=lambda _: True)
        self.assertFalse(changed)
        self.assertIn("voll", msg)
        changed, _, msg = watchlist.apply(body("Entfernen", "keiner"), self.path)
        self.assertFalse(changed)
        self.assertIn("nicht auf der Liste", msg)

    def test_form_fields_and_an_empty_body(self):
        self.assertEqual(watchlist.field(body("Entfernen", "sola"), "Was soll passieren?"), "Entfernen")
        self.assertEqual(watchlist.field("", "Twitch-Name"), "")
        changed, _, _ = watchlist.apply("", self.path)
        self.assertFalse(changed)

    def test_player_exists_asks_the_site_and_survives_an_outage(self):
        with mock.patch.object(watchlist.collect, "Site") as site:
            site.return_value.get.return_value = {"login": "sola"}
            self.assertTrue(watchlist.player_exists("sola"))
            site.return_value.get.side_effect = TimeoutError("timed out")
            self.assertFalse(watchlist.player_exists("sola"))

    def test_main_prints_the_action_outputs(self):
        with mock.patch.dict(os.environ, {"BODY": body("Hinzufügen", "x")}), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(watchlist.main(), 0)
        self.assertIn("changed=false", out.getvalue())
        self.assertIn("message=Das sieht nicht nach einem Twitch-Namen aus", out.getvalue())


if __name__ == "__main__":
    unittest.main()


class AutoPartTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "watchlist.txt"
        self.path.write_text("# Kommentar\nsola\nvelcorn\n")

    def test_sync_adds_the_top_100_below_the_marker_and_follows_changes(self):
        self.assertTrue(watchlist.sync(["a", "sola", "b"], self.path))
        text = self.path.read_text()
        self.assertEqual(text, f"# Kommentar\nsola\nvelcorn\n{watchlist.collect.AUTO_MARK}\na\nb\n")  # sola is above
        self.assertFalse(watchlist.sync(["a", "sola", "b"], self.path))  # nothing changed, nothing written
        self.assertTrue(watchlist.sync(["b", "c"], self.path))  # a left the top 100, c came in
        self.assertTrue(self.path.read_text().endswith(f"{watchlist.collect.AUTO_MARK}\nb\nc\n"))
        # the top part is not read in every run
        self.assertEqual(watchlist.collect.read_watchlist(self.path), ["sola", "velcorn"])

    def test_hand_entries_survive_a_sync_and_the_form_edits_above_the_marker(self):
        watchlist.sync(["a", "b"], self.path)
        changed, _, _ = watchlist.apply(body("Hinzufügen", "neuer"), self.path, exists=lambda _: True)
        self.assertTrue(changed)
        lines = self.path.read_text().splitlines()
        self.assertLess(lines.index("neuer"), lines.index(watchlist.collect.AUTO_MARK))
        watchlist.sync(["ccc"], self.path)
        self.assertIn("neuer", self.path.read_text().splitlines())
        changed, _, msg = watchlist.apply(body("Entfernen", "ccc"), self.path)
        self.assertFalse(changed)
        self.assertIn("Top 100", msg)
        changed, _, _ = watchlist.apply(body("Entfernen", "velcorn"), self.path)
        self.assertTrue(changed)
        self.assertIn(watchlist.collect.AUTO_MARK, self.path.read_text())

    def test_cli_sync_reads_the_board_from_the_state(self):
        state = self.path.parent / "state.json"
        state.write_text('{"boards": {"gear": [["Fluriio", 557], ["Sola", 1]]}}')
        with mock.patch("sys.argv", ["watchlist.py", "--sync", str(state)]), \
                mock.patch.object(watchlist, "LIST", self.path), redirect_stdout(io.StringIO()) as out:
            watchlist.main()
        self.assertEqual(out.getvalue().strip(), "changed=true")
