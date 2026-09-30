# Chat-RPG Statistik

[![CI](https://github.com/Velcorn/chat-rpg-stats/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Velcorn/chat-rpg-stats/actions/workflows/ci.yml)
[![Abdeckung](https://raw.githubusercontent.com/Velcorn/chat-rpg-stats/badges/coverage.svg)](https://github.com/Velcorn/chat-rpg-stats/actions/workflows/ci.yml)
[![Sammler](https://github.com/Velcorn/chat-rpg-stats/actions/workflows/collect.yml/badge.svg)](https://github.com/Velcorn/chat-rpg-stats/actions/workflows/collect.yml)
[![Lizenz: MIT](https://img.shields.io/github/license/Velcorn/chat-rpg-stats)](LICENSE)

Ranglisten, Verlauf und Prognosen für das Twitch-Chat-RPG [rpg.sola.rip](https://rpg.sola.rip): Wie schnell wächst
deine Ausrüstung, wann erreichst du den nächsten Rang oder die Top 100, wie verteilen ähnlich starke Spieler ihre
Werte, wo stehst du in deiner Gilde, welche Kämpfe gewinnt man meistens. Die Seite hat drei Bereiche mit
Unterseiten: Ranglisten (Ausrüstung, Silber, Errungenschaften, Quests, Aufsteiger), Gilden (eine Seite pro Gilde) und
Kämpfe (Kampfarten, letzte Kämpfe, fahrender Händler), dazu eine Seite pro Spieler.

**Zur Seite: <https://velcorn.github.io/chat-rpg-stats/>**

> **Hinweis:** Dieses Projekt ist (fast) komplett vibe-coded, also größtenteils von einer KI geschrieben und nur
> stichprobenartig von Hand geprüft. Die Zahlen sind Schätzungen; Benutzung auf eigene Gefahr.

Die Seite ist ein reines Dashboard: Sie liest öffentliche Daten, spielt nicht, meldet sich nirgends an und schreibt
nichts in den Chat. Kein offizielles Angebot des Spiels.

## Was erfasst wird

Ein Sammler läuft alle 15 Minuten von 7 bis 24 Uhr (Berliner Zeit, die Spielzeit des Spiels; nachts ändert sich nichts)
als GitHub Action und fragt die öffentlichen Schnittstellen der Seite ab, dieselben, die sie selbst ohne Anmeldung
zeigt:

| Daten | Quelle | Anfragen pro Lauf |
|---|---|---|
| Ausrüstungswert, Spenden und Aktivität aller Gildenmitglieder | Gildenliste und Gildenseiten | 1 + 1 pro Gilde |
| Top 100 nach Ausrüstung (mit ATK/DEF/SUP), Silber, Errungenschaften und Quests | Ranglisten | 4 |
| Die letzten 20 Kämpfe aller Kanäle | Kampfarchiv | 1 |
| Fahrender Händler, Kanäle | Händler, Kanalliste | 2 |
| Spieler auf der Beobachtungsliste | Spielerseite | 1 pro Spieler |

Das sind etwa 12 Anfragen pro Lauf im Abstand von 2 Sekunden, rund 800 am Tag, egal wie viele Leute die Seite ansehen:
Besucher lesen nur fertige Dateien. Jede Anfrage nennt das Projekt im User-Agent. Ist die Seite nicht erreichbar, fällt
der Lauf aus. Gespeichert wird nur, was sich geändert hat.

Wie gerechnet wird (Rang, Tempo, Prognose, Vergleich) und wie die Daten liegen: [docs/funktionsweise.md](docs/funktionsweise.md).

## Beobachtungsliste

Ausrüstung je Platz, Kampfquoten im Vergleich, Überleben, Markt und Verlosungen gibt es für Spieler auf der Beobachtungsliste. Eintragen oder austragen
geht über das Issue-Formular ["Auf die Beobachtungsliste"](https://github.com/Velcorn/chat-rpg-stats/issues/new?template=watchlist.yml);
eine Action prüft den Namen, trägt ihn ein und schließt das Issue. Bitte nur den eigenen Namen. Die Liste ist auf 150
Spieler begrenzt, weil jeder Eintrag eine Anfrage pro Lauf kostet.

## Wünsche und Fehler

Ideen, Wünsche oder Fehler bitte als [Issue](https://github.com/Velcorn/chat-rpg-stats/issues/new) melden.

## Entwicklung

Python 3.13 ohne Laufzeit-Abhängigkeiten, verwaltet mit [uv](https://docs.astral.sh/uv/). Die Seite ist eine einzelne
HTML-Datei ohne Build-Schritt.

```
uv run python collect.py --data data --force    # ein Lauf, auch außerhalb der Spielzeit
uv run python build.py --data data --out _site   # die Dateien für die Seite
uv run python -m http.server -d _site            # ansehen unter http://localhost:8000
uv run python -m unittest discover tests
uv run ruff check
uv run prek install                              # Git-Hooks: ruff, Tests, Dateihygiene, einfache Satzzeichen
```

Eigene Kopie (Fork): unter Settings -> Pages als Quelle "GitHub Actions" wählen, die Action "Sammeln und
veröffentlichen" einmal von Hand starten. Danach läuft sie nach Zeitplan.

Die Action `CI` prüft jeden Push und jeden Pull Request (dieselben Hooks wie lokal, dazu die Testabdeckung, aus der das
Badge oben entsteht). Neue Fassungen der Actions und Abhängigkeiten schlägt Dependabot vor.

## Wenn der Betreiber des Spiels das nicht möchte

Dann wird der Sammler sofort abgestellt. Ein Issue oder eine Nachricht genügt.

## Lizenz

[MIT](LICENSE)
