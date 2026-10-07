# Chat-RPG Statistik

[![CI](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/ci.yml)
[![coverage](https://raw.githubusercontent.com/Velcorn/Chat-RPG-Stats/badges/coverage.svg)](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/ci.yml)
[![collect](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/collect.yml/badge.svg)](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/collect.yml)
[![license: MIT](https://img.shields.io/github/license/Velcorn/Chat-RPG-Stats)](LICENSE)

Ranglisten, Verlauf und Prognosen für das Twitch-Chat-RPG [rpg.sola.rip](https://rpg.sola.rip): Wie schnell wächst
deine Kampfkraft, wann erreichst du den nächsten Rang oder die Top 100, wie verteilen ähnlich starke Spieler ihre
Werte, wo stehst du in deiner Gilde, welche Kämpfe gewinnt man meistens. Die Seite hat vier Bereiche mit
Unterseiten: Ranglisten (Kampfkraft, Silber, Errungenschaften, Quests, Aufsteiger), Gilden (Vergleich mit den ersten Siegen über die Bosse und eine Seite pro Gilde),
Kämpfe (Kampfarten, Abenteuer, Überleben, Kampfkraft, Wann und wo, Gilden, letzte Kämpfe) und Spiel (Wirtschaft, Regeln, Änderungen, Kompendium), dazu eine Seite pro Spieler
mit Teilen-Knopf. Die Startseite zeigt Kennzahlen, die Spielersuche, die Top 5, die Aufsteiger, die Gilden und die Streamer mit Live-Status, Chat-Modus, Link zum Stream und Gildenstand.

**Zur Seite: <https://velcorn.github.io/Chat-RPG-Stats/>**

> **Hinweis:** Dieses Projekt ist (fast) komplett vibe-coded, also größtenteils von einer KI geschrieben und nur
> stichprobenartig von Hand geprüft. Die Zahlen sind Schätzungen; Benutzung auf eigene Gefahr.

Die Seite ist ein reines Dashboard: Sie liest öffentliche Daten, spielt nicht, meldet sich nirgends an und schreibt
nichts in den Chat. Kein offizielles Angebot des Spiels.

## Was erfasst wird

Ein Sammler läuft etwa alle 15 Minuten von 7 bis 24 Uhr (Berliner Zeit, die Spielzeit des Spiels; nachts ändert sich nichts)
als GitHub Action und fragt die öffentlichen Schnittstellen der Seite ab, dieselben, die sie selbst ohne Anmeldung
zeigt:

| Daten | Quelle | Anfragen pro Lauf |
|---|---|---|
| Kampfkraft, Spenden und Aktivität aller Gildenmitglieder | Gildenliste und Gildenseiten | 1 + 1 pro Gilde |
| Top 100 nach Kampfkraft (mit ATK/DEF/SUP), Silber, Errungenschaften und Quests | Ranglisten | 4 |
| Die letzten 20 Kämpfe aller Kanäle | Kampfarchiv | 1 |
| Gefallene, Rollen und Schaden jedes neuen Kampfes (nur Summen) | Kampfbericht | 1 pro neuem Kampf, etwa 3 pro Lauf |
| Durchschnittliche Kampfkraft und Empfehlung des zuletzt angezeigten Kampfes | laufender Kampf | 1 |
| Kanäle | Kanalliste, Live-Status, Chat-Modus | 1 |
| Regeln des Spiels (für den Änderungsverlauf) | Regeln | 1 |
| Nachschlagewerk: Stufen, Bosse, Kämpfe, Schmiede und Lager | Kompendium | 1 pro Tag |
| Erste Siege der Gilden über jeden Boss | Erstkills | 1 pro Tag |
| Änderungsprotokoll des Spiels | Skript der Changelog-Seite | 3 pro Tag |
| Spieler auf der Beobachtungsliste | Spielerseite | 1 pro Spieler |

Ein Lauf macht also etwa 16 Anfragen und eine pro neuem Kampf, im Abstand von 2 Sekunden. Bei 4 Läufen pro Stunde und
17 Stunden Spielzeit sind das rund 1.200 Anfragen am Tag, egal wie viele Leute die Seite ansehen: Besucher lesen nur fertige Dateien. Die Seite nennt diese Zahl
im Fuß (gemessen am letzten Lauf, mal 68 Läufe am Tag). Jede Anfrage nennt
das Projekt im User-Agent. Ist die Seite nicht erreichbar, fällt der Lauf aus. Gespeichert wird nur, was sich geändert hat.

Wie gerechnet wird (Rang, Tempo, Prognose, Vergleich) und wie die Daten liegen: [docs/funktionsweise.md](docs/funktionsweise.md).

## Beobachtungsliste

Ausrüstung je Platz, Siegquoten, Schadensminderung, Markt und Verlosungen gibt es für Spieler auf der Beobachtungsliste. Die Streamer der Kanäle stehen standardmäßig auf der Liste. Eintragen oder austragen
geht über das Issue-Formular ["Auf die Beobachtungsliste"](https://github.com/Velcorn/Chat-RPG-Stats/issues/new?template=watchlist.yml);
eine Action prüft den Namen, trägt ihn ein und schließt das Issue. Bitte nur den eigenen Namen. Die Liste ist auf 150
Spieler begrenzt, weil jeder Eintrag eine Anfrage pro Lauf kostet.

## Wünsche und Fehler

Ideen, Wünsche oder Fehler bitte als [Issue](https://github.com/Velcorn/Chat-RPG-Stats/issues/new) melden.

## Entwicklung

Python 3.13 ohne Laufzeit-Abhängigkeiten, verwaltet mit [uv](https://docs.astral.sh/uv/). Die Seite ist eine einzelne
HTML-Datei ohne Build-Schritt.

```
uv run python src/collect.py --data data --force    # ein Lauf, auch außerhalb der Spielzeit
uv run python src/build.py --data data --out _site   # die Dateien für die Seite
uv run python -m http.server -d _site            # ansehen unter http://localhost:8000
PYTHONPATH=src uv run python -m unittest discover tests
uv run ruff check
uv run prek install                              # Git-Hooks: ruff, Tests, Dateihygiene, einfache Satzzeichen
```

Eigene Kopie (Fork): unter Settings -> Pages als Quelle "GitHub Actions" wählen, die Action "collect"
einmal von Hand starten. Danach läuft sie nach Zeitplan.

Die Action `CI` prüft jeden Push und jeden Pull Request (dieselben Hooks wie lokal, dazu die Testabdeckung, aus der das
Badge oben entsteht). Neue Fassungen der Actions und Abhängigkeiten schlägt Dependabot vor.

## Wenn der Betreiber des Spiels das nicht möchte

Dann wird der Sammler sofort abgestellt. Ein Issue oder eine Nachricht genügt.

## Lizenz

[MIT](LICENSE)
