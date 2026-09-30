"""The watchlist issue form: add, remove, refuse anything that isn't a plain existing Twitch login."""
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
