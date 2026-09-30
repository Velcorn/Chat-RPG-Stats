# Chat-RPG Statistik

Ranglisten, Verlauf und Prognosen für das Twitch-Chat-RPG [rpg.sola.rip](https://rpg.sola.rip): Wie schnell wächst deine
Ausrüstung, wann erreichst du den nächsten Rang oder die Top 100, wie verteilen ähnlich starke Spieler ihre Werte, wo
stehst du in deiner Gilde, welche Kämpfe gewinnt man meistens.

Die Seite ist ein reines Dashboard: Sie liest öffentliche Daten, spielt nicht, meldet sich nirgends an und schreibt
nichts in den Chat. Kein offizielles Angebot des Spiels.

## Was erfasst wird

Ein Sammler läuft alle 15 Minuten von 7 bis 24 Uhr (Berliner Zeit, die Spielzeit des Spiels; nachts ändert sich nichts)
als GitHub Action und fragt die öffentlichen Schnittstellen der Seite ab, dieselben, die die Seite selbst ohne Anmeldung
zeigt:

| Daten | Quelle | Anfragen pro Lauf |
|---|---|---|
| Ausrüstungswert, Spenden und Aktivität aller Gildenmitglieder | Gildenliste und Gildenseiten | 1 + 1 pro Gilde |
| Top 100 nach Ausrüstung und nach Quests (mit ATK/DEF/SUP) | Ranglisten | 2 |
| Die letzten 20 Kämpfe aller Kanäle | Kampfarchiv | 1 |
| Fahrender Händler, Kanäle | Händler, Kanalliste | 2 |
| Spieler auf der Beobachtungsliste | Spielerseite | 1 pro Spieler |

Das sind etwa 10 Anfragen pro Lauf im Abstand von 2 Sekunden, rund 700 am Tag, egal wie viele Leute die Seite
ansehen: Besucher lesen nur die fertigen Dateien. Jede Anfrage nennt das Projekt im User-Agent. Ist die Seite nicht
erreichbar, fällt der Lauf einfach aus.

Gespeichert wird nur, was sich seit dem letzten Lauf geändert hat (bei einem Spieler nur die geänderten Werte), eine
Datei pro Tag im Zweig `data`.

## Beobachtungsliste

Kampfquoten, Markt, Verlosungen, Überleben und die eigenen Quests gibt es für Spieler auf der Beobachtungsliste. Eintragen
(oder austragen) geht über das Issue-Formular "Auf die Beobachtungsliste"; eine Action prüft den Namen, trägt ihn ein
und schließt das Issue. Bitte nur den eigenen Namen. Die Liste ist auf 150 Spieler begrenzt, weil jeder Eintrag eine
Anfrage pro Lauf kostet.

## So rechnet die Seite

- **Rang:** In den Top 100 der Rang aus der Rangliste des Spiels. Darunter "etwa": der Platz unter allen erfassten
  Spielern (Gildenmitglieder und Top 100); wer in keiner Gilde ist, fehlt dort. Gleiche Werte teilen sich einen Platz.
  Die Rangliste des Spiels hinkt der Gildenseite ein paar Minuten nach; die Tabelle zeigt deshalb ihren eigenen Wert.
- **Tempo:** Zuwachs an Ausrüstungswert pro Tag, gemittelt über die letzten 7 Tage (oder seit Beginn der Aufzeichnung,
  frühestens nach 12 Stunden).
- **Nächster Rang:** Punkte bis über den nächsthöheren Wert, und wie lange das bei deinem Tempo dauert (ohne dass der
  andere weiter wächst).
- **Top 100:** Punkte bis über den Wert von Platz 100. Die Dauer rechnet mit deinem Tempo abzüglich des Tempos an der
  Grenze (Mittel der Plätze 90 bis 100), denn die Grenze steigt mit.
- **Vergleich mit ähnlichen Spielern:** Mittel von ATK/DEF/SUP der Spieler mit bekannter Verteilung (Top 100 und
  Beobachtungsliste), deren Wert höchstens 5 % (mindestens 10 Punkte) von deinem abweicht; sind das weniger als 8, die
  8 nächsten.
- **Aufsteiger:** größter Zuwachs in 24 Stunden bzw. 7 Tagen.
- **Kämpfe:** Siegquote pro Kampfart der letzten 30 Tage, Bosse nach Name und Stufe, sonst nach Art und Schwierigkeit.
- **Fahrender Händler:** Besuche, die bei einem Lauf gerade liefen (ein Besuch dauert 5 Minuten, also längst nicht alle).

## Entwicklung

Python 3.13 ohne Laufzeit-Abhängigkeiten, verwaltet mit [uv](https://docs.astral.sh/uv/). Die Seite ist eine einzelne
HTML-Datei ohne Build-Schritt.

```
uv run python collect.py --data data --force    # ein Lauf, auch außerhalb der Spielzeit
uv run python build.py --data data --out _site   # die Dateien für die Seite
uv run python -m http.server -d _site            # ansehen unter http://localhost:8000
uv run python -m unittest discover tests
uv run ruff check
```

Auf GitHub: Unter Settings -> Pages als Quelle "GitHub Actions" wählen. Die Action "Sammeln und veröffentlichen" läuft
dann nach Zeitplan; von Hand gestartet sammelt sie auch außerhalb der Spielzeit.

## Wenn der Betreiber des Spiels das nicht möchte

Dann wird der Sammler sofort abgestellt. Ein Issue oder eine Nachricht genügt.
