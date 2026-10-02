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
   Ein Lauf ist dadurch rund 25 KB groß, ein Tag etwa 1,6 MB (die Summen je Kampf kommen dazu).
3. **Bauen** (`build.py`): spielt alle Tagesdateien ab und schreibt `summary.json` (Ranglisten, Gilden, Kämpfe, `stats` aus `fightstats.py`, `channel_stats`, `rules`, `economy`),
   `players.json` (Suchindex) und eine Datei `p/<name>.json` pro Spieler.
4. **Veröffentlichen:** die Action lädt die Dateien samt `site/index.html` auf GitHub Pages. Besucher lesen nur diese
   fertigen Dateien; ihre Zahl ändert nichts an den Anfragen ans Spiel.

Läuft der Sammler außerhalb der Spielzeit (Zeitplan deckt 4 bis 22 Uhr UTC ab, also Sommer- und Winterzeit), tut er
nichts. Ist die Seite nicht erreichbar, fällt der Lauf aus; die nächste Zeitplan-Ausführung versucht es wieder.
Von Hand gestartet (`workflow_dispatch`) sammelt er immer.

GitHubs eigener Zeitplan löst bei kleinen Repos unzuverlässig aus (am 30.09.2026 nur einmal am Tag). Darum startet zusätzlich
ein systemd-Timer (`deploy/chat-rpg-stats-collect.timer`, Einrichtung im Kopf der Service-Datei) die Action alle 15 Minuten
von 7 bis 24 Uhr per `gh workflow run`. Der Zeitplan auf GitHub bleibt als Rückfall.

Änderungen an `site/` oder `build.py` lösen nur Bauen und Veröffentlichen aus, ohne neue Anfragen.

## Beobachtungsliste

Das Issue-Formular legt ein Issue mit dem Label `beobachtungsliste` an. Die Action `Beobachtungsliste` liest den
Issue-Text (untrusted: nur ein gültiger Twitch-Name, `^[a-z0-9_]{3,25}$`, und nur wenn es den Spieler im Spiel gibt),
ändert `watchlist.txt`, antwortet und schließt das Issue. Höchstens 150 Einträge, weil jeder eine Anfrage pro Lauf
kostet. Für diese Spieler kommen Schadensminderung, Leben, Erfolge, Statistiken und die Ausrüstung je Platz dazu. Einzelne Quests
und Kämpfe eines Spielers werden nicht gespeichert, nur Werte und ihre Änderungen.

## Aufbau der Seite

Eine Startseite und vier Bereiche mit einer zweiten Tab-Zeile, damit keine Seite überladen ist (Adresse `#/<Bereich>/<Unterseite>`):

- **Start** (`#/start`, Standard): eine Karte je Streamer (Kanal der Liste `channels`): Live-Status aus `/api/channels`, Chat-Modus (`chatMode`: normal, langsam = nur jedes zehnte !quest im Chat wird beantwortet, still = gar keins), Live-Anteil (Anteil der Läufe, in denen der Kanal live war, seit Beginn der Daten), Kämpfe der letzten 30 Tage in diesem Kanal mit Siegquote, Teilnehmern und Gefallenen, Link zum Twitch-Kanal, Gildenname, Mitglieder, Kasse, durchschnittliche Kampfkraft der aktiven Mitglieder (die Karten sind nach dem Durchschnitt sortiert, Live zuerst) mit Link zur Gildenseite und zur Spielerseite des Streamers. Dazu die zehn letzten Kämpfe und die Spielersuche. Laufende Kämpfe zeigt die Startseite nicht, denn bei einem Abruf alle 15 Minuten wären sie fast immer schon vorbei. Zuschauerzahl und Titel des Streams gibt das Spiel nicht her, sie stehen nicht da.

- **Ranglisten** (`#/rangliste/...`): `kampfkraft` (Standard, mit ATK, DEF, SUP und Bonus je Spieler), `silber`, `errungenschaften`, `quests`,
  `aufsteiger`, `formel`. Die vier Ranglisten sind die des Spiels (Parameter `by=gear|gold|errungenschaften|quests`; `gear` ist seit dem 30.09.2026 die Kampfkraft, je Top 100).
- **Gilden** (`#/gilden/<Gilde>`): `vergleich` (Standard) stellt alle Gilden nebeneinander: Mitglieder, durchschnittliche Kampfkraft der Aktiven, Veränderung der Gesamt-Kampfkraft in 24 Stunden und 7 Tagen (auch je Mitglied), Kasse und ihre Veränderung in 7 Tagen, Spenden, Bossiege und -niederlagen. Dazu eine Unterseite pro Gilde, der Tab trägt den Namen des Streamers, die Überschrift den vollen Gildennamen.
- **Spiel** (`#/spiel/...`): `wirtschaft` (Silber in allen Gildenkassen und das Silber der heutigen Top 100 im Verlauf der letzten 30 Tage, Median der Top 100; der Markt ist ohne Anmeldung nicht lesbar und fehlt), `regeln` (die Regeln aus `/api/rules` mit deutschen Namen) und `aenderungen` (jede Änderung einer Regel mit Zeitpunkt, Vorher und Nachher; das Feld `playWindowOpenNow` wird nicht verglichen, es wechselt täglich). Der Sammler holt die Regeln bei jedem Lauf (eine Anfrage) und speichert sie nur bei Änderung.
- **Kämpfe** (`#/kaempfe/...`): `arten`, `ueberleben`, `kraft`, `zeit`, `letzte`.
- **Spieler** (`#/spieler/<Name>`): eine Seite pro Spieler, erreichbar über die Suche. Der Knopf "Teilen" kopiert eine kurze Zusammenfassung (Kampfkraft, Rang, Gilde, Link) in die Zwischenablage. "Vergleich" nennt den Anteil der erfassten Spieler mit niedrigerer Kampfkraft. Von oben nach unten: Kennzahlen, Verlauf der Kampfkraft und Verteilung der Werte, Gilde und Prognose, Rang und Silber, bei Spielern der Beobachtungsliste zuletzt Kämpfe, Statistik und Ausrüstung.

## So rechnet die Seite

- **Rang:** In den Top 100 der Rang aus der Rangliste des Spiels. Darunter "etwa": der Platz unter allen erfassten
  Spielern (Gildenmitglieder und Top 100); wer in keiner Gilde ist, fehlt dort. Gleiche Werte teilen sich einen Platz.
  Die Rangliste des Spiels hinkt der Gildenseite ein paar Minuten nach; die Tabelle zeigt deshalb ihren eigenen Wert.
- **Tempo:** Zuwachs an Kampfkraft pro Tag, gemittelt über die letzten 7 Tage (oder seit Beginn der Aufzeichnung,
  frühestens nach 12 Stunden).
- **Nächster Rang:** Punkte bis über den nächsthöheren Wert, und wie lange das bei deinem Tempo dauert (ohne dass der
  andere weiter wächst).
- **Top 100:** Punkte bis über den Wert von Platz 100. Die Dauer rechnet mit deinem Tempo abzüglich des Tempos an der
  Grenze (Median der Plätze 90 bis 100), denn die Grenze steigt mit.
- **Vergleich mit ähnlichen Spielern:** Mittel von ATK/DEF/SUP der Spieler mit bekannter Verteilung (Top 100 und
  Beobachtungsliste), deren Wert höchstens 5 % (mindestens 10 Punkte) von deinem abweicht; sind das weniger als 8, die
  8 nächsten.
- **Gilde:** Mitglied seit (Beitrittsdatum aus der Gildenliste), Platz bei Kampfkraft und Spenden innerhalb der Gilde,
  Anteil am Gildenwert, Abstand zur nächsten Spende und Anteil an allen Spenden der Gilde.
- **Quest-Fehlerquote (Beobachtungsliste):** gescheiterte Quests geteilt durch alle Quests (geschafft plus gescheitert),
  in Klammern hinter der Zeile "Quests".
- **Schadensminderung (Beobachtungsliste):** der Wert "Mindert Schaden" der Spielerseite im Spiel (`survivalPercent`), also
  der Anteil des eingehenden Schadens, den die Verteidigung abfängt.
- **Kampfkraft und Bonus:** Kampfkraft = ATK + DEF + SUP + Talentbonus (das Spiel nennt nur die Summe). Die Spalte "Bonus" der
  Rangliste ist Kampfkraft minus ATK, DEF und SUP. Die Seite "Bonus-Formel" hält die geschätzte Formel fest, von Hand
  aus einer Messung am eigenen Verteidiger (220 Ausrüstungszustände, 02.10.2026, nach dem Kampf-Umbau): Kampfkraft
  etwa 2,7 ATK + 0,8 DEF + 2,3 SUP - 20 (Abweichung um 15, höchstens 40; nahe dem Optimum gewölbt), Bonus etwa
  1,7 ATK - 0,2 DEF + 1,3 SUP. Dazu die Schadensminderung 100 DEF / (DEF + 80) Prozent. Eine Anpassung an den Ranglisten
  geht nicht, weil die Top 100 nach Kampfkraft ausgewählt sind (die Gewichte kämen um null heraus). Die Schätzung
  wird nicht automatisch neu angepasst; die Kennzahlen (kleinster, mittlerer, größter
  Bonus) auf der Seite kommen dagegen live aus den aktuellen Top 100.
- **Ranglisten Silber, Errungenschaften, Quests:** Rang und Wert wie in der Rangliste des Spiels; "24 h" ist die
  Änderung dieses Werts seit gestern (beim Silber kann sie auch negativ sein, wenn jemand etwas ausgibt).
- **Ausrüstung je Platz** (nur Beobachtungsliste): Stück, Stufe und ATK/DEF/SUP je Platz. Als schwächstes Stück gilt
  die niedrigste Stufe, bei Gleichstand die kleinste Summe aus ATK, DEF und SUP; leere Plätze zählen dabei nicht.
- **Siegquote** (nur Beobachtungsliste): gewonnene von den Kämpfen, an denen der Spieler teilgenommen hat, je Art
  (Abenteuer, Überfälle, Bosse), aus den Gesamtwerten seit Spielbeginn. Dazu Fallquote und Schaden pro Kampf.
- **Silber:** Silber über die Zeit (Top 100 und Beobachtungsliste).
- **Aufsteiger:** größter Zuwachs in 24 Stunden bzw. 7 Tagen.
- **Kämpfe:** Siegquote pro Kampfart der letzten 30 Tage, Bosse nach Name und Stufe, sonst nach Art und Schwierigkeit. Sortiert nach Siegquote, bei gleicher Quote nach Zahl der Kämpfe (mehr zuerst).
  Das Kampfarchiv des Spiels hält nur die letzten 20 Kämpfe, deshalb sammelt der Sammler sie fortlaufend. Die Kampfseiten nennen dazu den Beginn der Erfassung (`since` in `summary.json`, der erste Lauf); frühere Kämpfe fehlen, die Quoten gelten also nur für die Zeit danach. Derselbe Zeitpunkt steht im Seitenfuß.
  Kampfstatistik (`fightstats.py`, `summary.json` -> `stats`, letzte 30 Tage), ab 0.9.0:
  - Für jeden neuen Kampf holt der Sammler die Kampfbericht-Daten des Archivs (`/api/combat/history/{id}`, eine Anfrage je Kampf, nur einmal) und speichert daraus nur Summen: Teilnehmer und Gefallene je Rolle (Schildträger, Kämpfer, Unterstützer), Schaden, erlittener Schaden, Heilung, Runden, Leben des Bosses, mittleres Silber der Überlebenden und der Gefallenen. Namen und Einzelwerte einzelner Spieler werden nicht gespeichert. Beim ersten Lauf nach der Einführung kommen die 20 Kämpfe des Archivs nach; ältere fehlen.
  - Der laufende Kampf (`/api/combat?kompakt=true`, eine Anfrage je Lauf) nennt als Einziger Durchschnitt der Kampfkraft und der Ausrüstung, die Empfehlung und die Kampfwerte (Dauer, Wut, Gruppenstärke); das Archiv hat dort nur Nullen. Der Sammler übernimmt sie für den Kampf, den das Spiel gerade noch anzeigt, einmal je Kampf. Kämpfe, die zwischen zwei Läufen verschwinden, haben keine Kampfkraft; die Seite weist aus, für wie viele sie vorliegt.
  - **Überleben:** Anteil der Gefallenen (Gefallene durch Teilnehmer, alle Kämpfe mit Einzelheiten zusammen), getrennt nach Siegen und Niederlagen, nach Rolle, Kampfart und Kampf; dazu Schaden, Heilung, Runden und für Niederlagen das Leben, das der Boss noch hatte.
  - **Kampfkraft:** Durchschnitt der Teilnehmer gegen die Empfehlung (Bereiche unter 80 %, 80 bis 100 %, 100 bis 120 %, über 120 %, jeweils mit Siegquote), Kampfkraft der Siege gegen die der Niederlagen je Kampf.
  - **Wann und wo:** Kämpfe und Siegquote je Stunde (Berliner Zeit), je Kanal und je Tag. Braucht keine Einzelheiten.
  Links ins Spiel (öffnen in einem neuen Tab, nur feste Adressen und die Kampf-ID aus dem Archiv): der Kampfname in den Listen der letzten Kämpfe führt zu `/kampfbericht/{id}`, die Spieler- und Gildenseiten zu `/spieler/{login}` und `/gilden/{login}`, die Kampfseiten zu `/kampf`, der Seitenfuß zu Kämpfen, Bestenliste, Gilden, Markt und Kanälen. Es kommen keine zusätzlichen Anfragen dazu.

Alle Werte sind Schätzungen aus dem, was seit Beginn der Aufzeichnung gesammelt wurde. Am Anfang und bei neuen
Spielern fehlen Tempo und Prognose.
