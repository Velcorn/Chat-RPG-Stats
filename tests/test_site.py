import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "node not installed")
class SiteTests(unittest.TestCase):
    def test_the_page_script_parses(self):
        html = (Path(__file__).parent.parent / "site" / "index.html").read_text("utf-8")
        script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
        with tempfile.TemporaryDirectory() as tmp:
            js = Path(tmp) / "page.js"
            js.write_text(script, "utf-8")
            result = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_key_card_uses_the_final_boss_date_without_a_key_forecast(self):
        html = (Path(__file__).parent.parent / "site" / "index.html").read_text("utf-8")
        key_card = re.search(r"function keyCard\(s\) \{(.*?)\n\}", html, re.S).group(1)
        self.assertIn('`Letzter Boss: ${label}`', key_card)
        self.assertIn('"heute" : "vorbei"', key_card)
        for obsolete in ("s.keys.finish", "net_rate", ".eta", "Prognose sammelt", "letzter Schlüssel"):
            self.assertNotIn(obsolete, key_card)
