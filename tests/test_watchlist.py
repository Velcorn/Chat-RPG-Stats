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
