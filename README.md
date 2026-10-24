# Chat-RPG Statistik

[![CI](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/ci.yml)
[![coverage](https://raw.githubusercontent.com/Velcorn/Chat-RPG-Stats/badges/coverage.svg)](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/ci.yml)
[![collect](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/collect.yml/badge.svg)](https://github.com/Velcorn/Chat-RPG-Stats/actions/workflows/collect.yml)
[![license: MIT](https://img.shields.io/github/license/Velcorn/Chat-RPG-Stats)](LICENSE)

Ranglisten, Verlauf und Prognosen für das Twitch-Chat-RPG [rpg.sola.rip](https://rpg.sola.rip): Wie schnell wächst
dein Ausrüstungswert, wann erreichst du den nächsten Rang oder die Top 100, wie verteilen ähnlich starke Spieler ihre
Werte, wo stehst du in deiner Gilde und welche Kämpfe gewinnt man meistens. Die Seite hat vier Bereiche mit
Unterseiten: Ranglisten (Ausrüstungswert, Kampfkraft, Aufsteiger), Gilden (Vergleich mit den ersten Siegen über die Bosse und eine Seite pro Gilde),
Kämpfe (Übersicht, Kampfkraft, letzte Kämpfe) und Spiel (Regeln mit Changelog, Ausrüstung mit Höchstwerten, Formen und Spezialitems, Verbessern), dazu eine Seite pro Spieler
mit Teilen-Knopf. Die Startseite zeigt Kennzahlen, den Termin des letzten Bosses mit Countdown, die Spielersuche, die Top 5, die Gilden und die Streamer mit Live-Status, Kämpfen, Link zum Stream und Gildenstand. Die Saisonauswahl oben rechts öffnet den laufenden Saisonbericht (Podium, Weg an die Spitze, Rekorde, Zahlen, Gildenfinale) und später unveränderliche Archive früherer Saisons mit Abschlusskarten, Rangreise und Vergleich.

**Zur Seite: <https://velcorn.github.io/Chat-RPG-Stats/>**

> **Hinweis:** Dieses Projekt ist (fast) komplett vibe-coded, also größtenteils von einer KI geschrieben und nur
> stichprobenartig von Hand geprüft. Die Zahlen sind Schätzungen; Benutzung auf eigene Gefahr.

Die Seite ist ein reines Dashboard: Sie liest öffentliche Daten, spielt nicht, meldet sich nirgends an und schreibt
nichts in den Chat. Kein offizielles Angebot des Spiels.

## Was erfasst wird

Ein Sammler läuft etwa alle 5 Minuten, rund um die Uhr, von 1 bis 9 Uhr nur alle 15 Minuten (die Spielzeit des Spiels ändert sich ab und zu, nachts ändert sich meist nichts)
als GitHub Action und fragt die öffentlichen Schnittstellen der Seite ab, dieselben, die sie selbst ohne Anmeldung
zeigt:

| Daten | Quelle | Anfragen pro Lauf |
|---|---|---|
| Kampfkraft, Spenden und Aktivität aller Gildenmitglieder | Gildenliste und Gildenseiten | 1 + 1 pro Gilde (auch ohne Mitglieder, solange sie eine Kasse hat: ihre Bosssiege zählen mit) |
| Ausrüstungswert (Angriff + Verteidigung + Unterstützung) der aktiven Mitglieder außerhalb der Top 100, jeder etwa einmal am Tag | Spielerseite | rund 55 |
| Top 100 nach Ausrüstungswert (mit ATK/DEF/SUP) | Rangliste | 1 |
| Die letzten 20 Kämpfe aller Kanäle | Kampfarchiv | 1 |
| Gefallene, Rollen, Schaden, Heilung und Verstärkung jedes neuen Kampfes (nur Summen) | Kampfbericht | 1 pro neuem Kampf, etwa 3 pro Lauf |
| Durchschnittliche Kampfkraft und Empfehlung des zuletzt angezeigten Kampfes | laufender Kampf | 1 |
| Kanäle | Kanalliste, Live-Status | 1 |
| Regeln des Spiels (für den Änderungsverlauf) | Regeln | 1 |
| Erste Siege der Gilden über jeden Boss | Erstkills | 1 pro Tag |
| Spieler auf der Beobachtungsliste | Spielerseite | 1 pro Spieler |
| Top 100 der Rangliste (ohne Liste) | Spielerseite | 100 einmal am Tag im ersten Lauf, sonst nur, wessen Ausrüstungswert sich seit dem letzten Profil geändert hat (etwa 6 je Lauf) |

Ein Lauf macht also etwa 75 Anfragen (rund 16 für Ranglisten, Gilden, Kämpfe und Kanäle, die zuerst auf die Seite kommen, den Rest für Profile danach) und eine pro neuem Kampf, im Abstand von 2 Sekunden. Bei 12 Läufen pro Stunde (von 1 bis 9 Uhr 4)
(224 am Tag) kommt über den Tag eine entsprechend große Zahl zusammen, egal wie viele Leute die Seite ansehen: Besucher lesen nur fertige Dateien. Die Seite nennt diese Zahl
im Fuß (gemessen am letzten Lauf, mal 224 Läufe am Tag). Jede Anfrage nennt
das Projekt im User-Agent. Ist die Seite nicht erreichbar, fällt der Lauf aus. Gespeichert wird nur, was sich geändert hat.

Wie gerechnet wird (Rang, Tempo, Prognose, Vergleich) und wie die Daten liegen: [docs/funktionsweise.md](docs/funktionsweise.md).

## Beobachtungsliste

Ausrüstung, Siegquoten und Schadensminderung gibt es für die Top 100 (am Morgen und nach jeder Änderung der Ausrüstung aktualisiert) und für Spieler auf der Beobachtungsliste (bei jedem Lauf). Die Streamer der Kanäle stehen standardmäßig auf der Liste. Eintragen oder austragen
geht über das Issue-Formular ["Auf die Beobachtungsliste"](https://github.com/Velcorn/Chat-RPG-Stats/issues/new?template=watchlist.yml);
eine Action prüft den Namen, trägt ihn ein und schließt das Issue. Bitte nur den eigenen Namen. Die Liste ist auf 150
Spieler begrenzt, weil jeder Eintrag eine Anfrage pro Lauf kostet.

## Wünsche und Fehler

Ideen, Wünsche oder Fehler bitte als [Issue](https://github.com/Velcorn/Chat-RPG-Stats/issues/new) melden.

## Entwicklung

Python 3.13 ohne Laufzeit-Abhängigkeiten, verwaltet mit [uv](https://docs.astral.sh/uv/). Die Seite ist eine einzelne
HTML-Datei ohne Build-Schritt.

```
uv run python src/collect.py --data data    # ein Lauf
uv run python src/build.py --data data --out _site   # die Dateien für die Seite
PYTHONPATH=src uv run python src/archive.py --data data --id beta-2026 --label "Beta 2026"  # Saisonende
uv run python -m http.server -d _site            # ansehen unter http://localhost:8000
PYTHONPATH=src uv run python -m unittest discover tests
uv run ruff check
uv run prek install                              # Git-Hooks: ruff, Tests, Dateihygiene, einfache Satzzeichen
```

Eigene Kopie (Fork): unter Settings -> Pages als Quelle "GitHub Actions" wählen, die Action "collect"
einmal von Hand starten. Danach läuft sie nach Zeitplan.

Die Action `CI` prüft jeden Push und jeden Pull Request (dieselben Hooks wie lokal, dazu die Testabdeckung, aus der das
Badge oben entsteht). Neue Fassungen der Actions und Abhängigkeiten werden als Änderungsvorschläge geprüft.

## Wenn der Betreiber des Spiels das nicht möchte

Dann wird der Sammler sofort abgestellt. Ein Issue oder eine Nachricht genügt.

## Lizenz

[MIT](LICENSE)

Versionsregel: CalVer JJJJ.MM.TT, genau eine Version pro Kalendertag ohne Suffix. Die erste Änderung eines Tages setzt die Version in `pyproject.toml`, führt `uv lock` aus und beginnt den Tagesabschnitt in `CHANGELOG.md`. Weitere Änderungen desselben Tages behalten die Version und ergänzen denselben Eintrag. Keine Git-Tags. Ältere Angaben wie "seit 0.45.0" sind historische SemVer-Nummern und bleiben erhalten.
