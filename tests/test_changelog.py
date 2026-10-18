"""The site changelog supports the historical grouping styles."""
import unittest
from pathlib import Path

from build import parse_changelog, project_version


class ChangelogTests(unittest.TestCase):
    def test_headings_and_newest_first(self):
        entries = parse_changelog('''## 2026.10.17 (17.10.2026)
### Neu
- First
### Behoben
- Second
## 2026.10.18 (18.10.2026)
### Verbessert
- Third
''')
        self.assertEqual([e['version'] for e in entries], ['2026.10.18', '2026.10.17'])
        self.assertEqual(entries[1]['groups'], [
            {'title': 'Neu', 'items': ['First']}, {'title': 'Behoben', 'items': ['Second']}])
        self.assertEqual(entries[0]['date'], '18.10.2026')

    def test_bold_labels(self):
        entries = parse_changelog('''## 2026.10.18 (18.10.2026)
**Neu**
- First
**Verbessert**
- Second
  continued
''')
        self.assertEqual(entries[0]['groups'], [
            {'title': 'Neu', 'items': ['First']}, {'title': 'Verbessert', 'items': ['Second continued']}])

    def test_without_groups(self):
        entries = parse_changelog('## 2026.10.18 (18.10.2026)\n- Plain item\n')
        self.assertEqual(entries[0]['groups'], [{'title': '', 'items': ['Plain item']}])

    def test_repository_entries_have_unique_days_and_current_version(self):
        text = (Path(__file__).resolve().parent.parent / 'CHANGELOG.md').read_text('utf-8')
        entries = parse_changelog(text)
        self.assertEqual(entries[0]['version'], project_version())
        self.assertEqual(len(entries), len({e['date'] for e in entries}))
        item_count = sum(len(g['items']) for e in entries for g in e['groups'])
        self.assertEqual(item_count, sum(line.startswith('- ') for line in text.splitlines()))
