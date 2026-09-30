# Funktionsweise

Wie Daten hereinkommen, wie sie gespeichert werden und wie die Seite rechnet. Was das Projekt ist und wie du es
benutzt, steht in der [README](../README.md).

## Ablauf

```
Zeitplan (alle 15 Min., 7-24 Uhr) -> collect.py -> Zweig "data" -> build.py -> GitHub Pages
```

1. **Sammeln** (`collect.py`): fragt die öffentlichen Schnittstellen ab (Tabelle in der README), bildet daraus den
   aktuellen Stand und schreibt nur die Änderungen zum letzten Lauf.
2. **Speichern:** im Zweig `data`, eine Datei `days/JJJJ-MM-TT.jsonl` pro Tag (eine Zeile pro Lauf) und `state.json`
   mit dem letzten Stand. Von einem bekannten Spieler oder einer Gilde werden nur die geänderten Werte gespeichert.
   Ein Lauf ist dadurch rund 10 KB groß, ein Tag etwa 0,7 MB.
3. **Bauen** (`build.py`): spielt alle Tagesdateien ab und schreibt `summary.json` (Ranglisten, Gilden, Kämpfe),
   `players.json` (Suchindex) und eine Datei `p/<name>.json` pro Spieler.
4. **Veröffentlichen:** die Action lädt die Dateien samt `site/index.html` auf GitHub Pages. Besucher lesen nur diese
   fertigen Dateien; ihre Zahl ändert nichts an den Anfragen ans Spiel.

Läuft der Sammler außerhalb der Spielzeit (Zeitplan deckt 4 bis 22 Uhr UTC ab, also Sommer- und Winterzeit), tut er
nichts. Ist die Seite nicht erreichbar, fällt der Lauf aus; die nächste Zeitplan-Ausführung versucht es wieder.
Von Hand gestartet (`workflow_dispatch`) sammelt er immer.

Änderungen an `site/` oder `build.py` lösen nur Bauen und Veröffentlichen aus, ohne neue Anfragen.

## Beobachtungsliste

Das Issue-Formular legt ein Issue mit dem Label `beobachtungsliste` an. Die Action `Beobachtungsliste` liest den
Issue-Text (untrusted: nur ein gültiger Twitch-Name, `^[a-z0-9_]{3,25}$`, und nur wenn es den Spieler im Spiel gibt),
ändert `watchlist.txt`, antwortet und schließt das Issue. Höchstens 150 Einträge, weil jeder eine Anfrage pro Lauf
kostet. Für diese Spieler kommen Überleben, Leben, Erfolge, Statistiken und die Quest-Historie dazu.

## Aufbau der Seite

Drei Bereiche mit einer zweiten Tab-Zeile, damit keine Seite überladen ist (Adresse `#/<Bereich>/<Unterseite>`):

- **Ranglisten** (`#/rangliste/...`): `ausruestung` (Standard, mit Kennzahlen), `silber`, `errungenschaften`, `quests`,
  `aufsteiger`. Die vier Ranglisten sind die des Spiels (Parameter `by=gear|gold|errungenschaften|quests`, je Top 100).
- **Gilden** (`#/gilden/<Gilde>`): eine Unterseite pro Gilde.
- **Kämpfe** (`#/kaempfe/...`): `arten`, `letzte`, `haendler`.
- **Spieler** (`#/spieler/<Name>`): eine Seite pro Spieler, erreichbar über die Suche.

## So rechnet die Seite

- **Rang:** In den Top 100 der Rang aus der Rangliste des Spiels. Darunter "etwa": der Platz unter allen erfassten
  Spielern (Gildenmitglieder und Top 100); wer in keiner Gilde ist, fehlt dort. Gleiche Werte teilen sich einen Platz.
  Die Rangliste des Spiels hinkt der Gildenseite ein paar Minuten nach; die Tabelle zeigt deshalb ihren eigenen Wert.
- **Tempo:** Zuwachs an Ausrüstungswert pro Tag, gemittelt über die letzten 7 Tage (oder seit Beginn der Aufzeichnung,
  frühestens nach 12 Stunden).
- **Nächster Rang:** Punkte bis über den nächsthöheren Wert, und wie lange das bei deinem Tempo dauert (ohne dass der
  andere weiter wächst).
- **Top 100:** Punkte bis über den Wert von Platz 100. Die Dauer rechnet mit deinem Tempo abzüglich des Tempos an der
  Grenze (Median der Plätze 90 bis 100), denn die Grenze steigt mit.
- **Vergleich mit ähnlichen Spielern:** Mittel von ATK/DEF/SUP der Spieler mit bekannter Verteilung (Top 100 und
  Beobachtungsliste), deren Wert höchstens 5 % (mindestens 10 Punkte) von deinem abweicht; sind das weniger als 8, die
  8 nächsten.
- **Gilde:** Platz bei Spenden und Ausrüstung innerhalb der Gilde, Abstand zur nächsten Spende, Anteil am
  Gildenwert.
- **Ranglisten Silber, Errungenschaften, Quests:** Rang und Wert wie in der Rangliste des Spiels; "24 h" ist die
  Änderung dieses Werts seit gestern (beim Silber kann sie auch negativ sein, wenn jemand etwas ausgibt).
- **Aufsteiger:** größter Zuwachs in 24 Stunden bzw. 7 Tagen.
- **Kämpfe:** Siegquote pro Kampfart der letzten 30 Tage, Bosse nach Name und Stufe, sonst nach Art und Schwierigkeit.
  Das Kampfarchiv des Spiels hält nur die letzten 20 Kämpfe, deshalb sammelt der Sammler sie fortlaufend.
- **Fahrender Händler:** Besuche, die bei einem Lauf gerade liefen (ein Besuch dauert 5 Minuten, also längst nicht alle).

Alle Werte sind Schätzungen aus dem, was seit Beginn der Aufzeichnung gesammelt wurde. Am Anfang und bei neuen
Spielern fehlen Tempo und Prognose.
