# Funktionsweise

Wie Daten hereinkommen, wie sie gespeichert werden und wie die Seite rechnet. Was das Projekt ist und wie du es
benutzt, steht in der [README](../README.md).

## Ablauf

```
Zeitplan (alle 15 Min., 7-24 Uhr) -> src/collect.py -> Zweig "data" -> src/build.py -> GitHub Pages
```

1. **Sammeln** (`src/collect.py`): fragt die öffentlichen Schnittstellen ab (Tabelle in der README), bildet daraus den
   aktuellen Stand und schreibt nur die Änderungen zum letzten Lauf.
2. **Speichern:** im Zweig `data`, eine Datei `days/JJJJ-MM-TT.jsonl` pro Tag (eine Zeile pro Lauf) und `state.json`
   mit dem letzten Stand. Von einem bekannten Spieler oder einer Gilde werden nur die geänderten Werte gespeichert.
   Ein Lauf ist dadurch rund 25 KB groß, ein Tag etwa 1,6 MB (die Summen je Kampf kommen dazu).
3. **Bauen** (`src/build.py`): spielt alle Tagesdateien ab und schreibt `summary.json` (Ranglisten, Gilden, Kämpfe, `stats` und `eras` aus `src/fightstats.py`, `stories`, `channel_stats`, `rules`, `compendium`, `first_kills`, `guild_fights`, `economy`),
   `changelog.json` (das Änderungsprotokoll des Spiels),
   `players.json` (Suchindex) und eine Datei `p/<name>.json` pro Spieler.
4. **Veröffentlichen:** die Action lädt die Dateien samt `site/index.html` auf GitHub Pages. Besucher lesen nur diese
   fertigen Dateien; ihre Zahl ändert nichts an den Anfragen ans Spiel.

Läuft der Sammler außerhalb der Spielzeit (Zeitplan deckt 4 bis 22 Uhr UTC ab, also Sommer- und Winterzeit), tut er
nichts. Ist die Seite nicht erreichbar, fällt der Lauf aus; die nächste Zeitplan-Ausführung versucht es wieder.
Von Hand gestartet (`workflow_dispatch`) sammelt er immer.

GitHubs eigener Zeitplan löst bei kleinen Repos unzuverlässig aus (am 30.09.2026 nur einmal am Tag). Darum startet zusätzlich
ein systemd-Timer (`deploy/chat-rpg-stats-collect.timer`, Einrichtung im Kopf der Service-Datei) die Action alle 15 Minuten
von 7 bis 24 Uhr per `gh workflow run`. Der Zeitplan auf GitHub bleibt als Rückfall.

Änderungen an `site/` oder `src/` lösen nur Bauen und Veröffentlichen aus, ohne neue Anfragen.

## Beobachtungsliste

Das Issue-Formular legt ein Issue mit dem Label `beobachtungsliste` an. Die Action `Beobachtungsliste` liest den
Issue-Text (untrusted: nur ein gültiger Twitch-Name, `^[a-z0-9_]{3,25}$`, und nur wenn es den Spieler im Spiel gibt),
ändert `watchlist.txt`, antwortet und schließt das Issue. Höchstens 150 Einträge, weil jeder eine Anfrage pro Lauf
kostet. Für diese Spieler kommen Schadensminderung, Leben, Erfolge, Statistiken und die Ausrüstung je Platz dazu. Einzelne Quests
und Kämpfe eines Spielers werden nicht gespeichert, nur Werte und ihre Änderungen.

Dieselben Angaben gibt es auch für die Top 100 der Rangliste, ohne Eintrag in die Liste. Ihre Spielerseiten werden im
ersten Lauf des Tages (um 7 Uhr) alle auf einmal gelesen, also zur gleichen Zeit; bis zum nächsten Morgen gilt dieser Stand
(`days.top` im Zustand merkt das Datum der letzten Lesung). Wer die Top 100 verlässt, verliert diese Angaben bis zum nächsten Eintrag.

## Aufbau der Seite

Eine Startseite und vier Bereiche mit einer zweiten Tab-Zeile, damit keine Seite überladen ist (Adresse `#/<Bereich>/<Unterseite>`):

- **Start** (`#/start`, Standard): vier Kennzahlen (erfasste und aktive Spieler, höchster Ausrüstungswert, Kämpfe der letzten 30 Tage, Gilden), die Spielersuche, die fünf Besten nach Ausrüstungswert, die fünf größten Aufsteiger der letzten 24 Stunden, die Gilden mit mindestens 10 aktiven Mitgliedern nach Durchschnitt, "Zuletzt" (letzte Regeländerung und letzter Kampf, mit Links) und darunter eine Karte je Streamer (Kanal der Liste `channels`) (Kanal der Liste `channels`): Live-Status aus `/api/channels`, Chat-Modus (`chatMode`: normal, langsam = nur jedes zehnte !quest im Chat wird beantwortet, still = gar keins), Live-Anteil (Anteil der Läufe, in denen der Kanal live war, seit Beginn der Daten), Kämpfe der letzten 30 Tage in diesem Kanal mit Siegquote, Teilnehmern und Gefallenen, Link zum Twitch-Kanal, Gildenname, Mitglieder, Kasse, durchschnittliche Kampfkraft der aktiven Mitglieder (die Karten sind nach dem Durchschnitt sortiert, Live zuerst) mit Link zur Gildenseite und zur Spielerseite des Streamers. Die Liste der letzten Kämpfe steht nur unter `#/kaempfe/letzte`. Laufende Kämpfe zeigt die Startseite nicht, denn bei einem Abruf alle 15 Minuten wären sie fast immer schon vorbei. Zuschauerzahl und Titel des Streams gibt das Spiel nicht her, sie stehen nicht da.

- **Ranglisten** (`#/rangliste/...`): `kampfkraft` (Standard, mit ATK, DEF und SUP je Spieler), `silber`, `errungenschaften`, `quests`,
  `aufsteiger`. Die vier Ranglisten sind die des Spiels (Parameter `by=gear|gold|errungenschaften|quests`; `gear` ist der Ausrüstungswert, je Top 100).
  **Zwei Werte:** Die Gildenseiten des Spiels nennen für jedes Mitglied und für die Gilde die Kampfkraft (Ausrüstung plus Talente; beim Spieler mit Ausrüstungswert 328 und 32 Talentpunkten ist es 360). Sie ist als Maß für die Stärke unzuverlässig (Talente zählen mit), deshalb rechnet die Seite mit dem Ausrüstungswert, der Summe aus Angriff, Verteidigung und Unterstützung. Den gibt es nur für die Top 100 (Rangliste) und im Profil eines Spielers. Darum liest der Sammler zusätzlich einmal am Tag das Profil jedes aktiven Gildenmitglieds außerhalb der Top 100 (rund 3.300 Spieler, in Scheiben von etwa 55 je Lauf, der Reihe nach nach Namen; die Top 100 liefern den Wert schon, die Beobachtungsliste ebenso). Daraus kommen Rang, Verlauf, Tempo, Aufsteiger, Prognose, Gilden-Durchschnitt, Vergleich mit ähnlichen Spielern (jetzt für alle mit der Verteilung aus dem Profil) und die Spielerseiten. Die Grenze zur Top 100 ist der Ausrüstungswert des Spielers auf Platz 100. Nicht aktive Spieler werden nicht gelesen: sie haben keinen Ausrüstungswert, kommen weder in Rang und Suche noch in die Prognose und haben keine Spielerseite. Bis alle aktiven Spieler einmal gelesen sind (am ersten Tag nach der Umstellung), fehlen auch von ihnen einige im Rang, der dann zu gut ausfällt. Kampfkraft bleibt für die Summen der Gilden (Veränderung in 24 Stunden und 7 Tagen) und als Zeile auf der Spielerseite; die Kampfseiten vergleichen ohnehin die Kampfkraft der Gruppe mit der Empfehlung.
- **Gilden** (`#/gilden/<Gilde>`): `vergleich` (Standard) stellt alle Gilden nebeneinander, sortiert nach dem durchschnittlichen Ausrüstungswert der Aktiven; Gilden mit weniger als 10 aktiven Mitgliedern stehen unten und gewinnen keine Kachel (zwei Mitglieder würden jeden Durchschnitt anführen). Die Kacheln nennen den Streamer-Namen der Gilde. Spalten: Mitglieder, durchschnittlicher Ausrüstungswert der Aktiven, Veränderung der gesamten Kampfkraft der Gilde in 24 Stunden und 7 Tagen (auch je Mitglied), Kasse und ihre Veränderung in 7 Tagen, Spenden, Bossiege und -niederlagen, dazu der Stand der Gebäude (Schmiede, Lager, Kontor, Kriegskasse, Wall: Stufe, Wirkung, Preis, Wirkung und Sperre der nächsten Stufe aus `buildings` der Gildenseite) und je Boss die höchste besiegte Stufe samt Preis der nächsten (`boss.bosses`). Beides kommt aus der Gildenseite, die der Sammler ohnehin liest, und wird nur bei Änderung gespeichert. Unter der Tabelle stehen die ersten Siege der Gilden über jeden Boss (`/api/guilds/first-kills`, eine Anfrage pro Tag); die Gildenseite nennt die der eigenen Gilde. Dazu eine Unterseite pro Gilde, der Tab trägt den Namen des Streamers, die Überschrift den vollen Gildennamen.
- **Spiel** (`#/spiel/...`): `wirtschaft` (Silber in allen Gildenkassen und das Silber der heutigen Top 100 im Verlauf der letzten 30 Tage, Median der Top 100; der Markt ist ohne Anmeldung nicht lesbar und fehlt), `regeln` (die Regeln aus `/api/rules`, nach Themen gruppiert mit deutschen Namen und einem Satz zur Bedeutung; wo die Bedeutung nur vermutet ist, steht "Vermutlich"; unbekannte neue Regeln erscheinen unter "Sonstiges"), `kompendium` (Stufen mit Material und Quellen, die sechs Bosse mit Beutestufen, empfohlener Ausrüstung und Hortstücken, Kampfarten, Projekte sowie die Schmiede-Stufen und die Waren des Lagers aus `/api/compendium`; Tränke zeigt die Seite nur, solange das Spiel noch welche meldet, denn das Lager ersetzt den Alchemisten; der Sammler holt die Seite beim ersten Lauf eines Tages, eine Anfrage, und speichert eine verkürzte Fassung ohne Symbole und Beispieltexte) und `aenderungen` (nach Tagen: die Einträge des Änderungsprotokolls des Spiels zum Aufklappen und dazwischen jede gemessene Änderung einer Regel mit Zeitpunkt, Vorher und Nachher; das Feld `playWindowOpenNow` wird nicht verglichen, es wechselt täglich). Der Sammler holt die Regeln bei jedem Lauf (eine Anfrage) und speichert sie nur bei Änderung. Das Protokoll hat im Spiel keine Schnittstelle: es steht als Text im Skript der Seite `/changelog`, das der Sammler über das Skript der Startseite findet (drei Anfragen, einmal am Tag) und als `changelog.json` ablegt.
- **Kämpfe** (`#/kaempfe/...`): `arten`, `abenteuer`, `ueberleben`, `kraft`, `zeit`, `gilden` (je Gilde die Überfälle auf ihre Kasse mit Abwehr, verlorenem und gewonnenem Silber sowie die beschworenen Bosse mit Siegen, aus `guildName`, `summonedBy` und `treasuryChange` der Kampfberichte; erst ab 0.12.0 gesammelt) und `letzte` (mit Gilde und Kassenänderung, wo der Bericht sie nennt).
- **Spieler** (`#/spieler/<Name>`): eine Seite pro Spieler, erreichbar über die Suche. Der Knopf "Teilen" kopiert eine kurze Zusammenfassung (Ausrüstungswert, Rang, Gilde, Link) in die Zwischenablage. "Vergleich" nennt den Anteil der erfassten Spieler mit niedrigerem Ausrüstungswert. Von oben nach unten: Kennzahlen (die Kachel des Ausrüstungswerts nennt neben dem Ausrüstungswert die Kampfkraft: das Wort in der Titelzeile, die Zahl halb so groß und oben bündig), Verlauf des Ausrüstungswerts und Verteilung der Werte, Gilde und Prognose, Rang und Silber, bei Spielern der Beobachtungsliste zuletzt Kämpfe, Statistik und Ausrüstung.

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
  8 nächsten. Angriff ist rot, Verteidigung blau, Unterstützung grün; deine Werte sind kräftig, das Mittel der anderen blass.
- **Gilde:** Mitglied seit (Beitrittsdatum aus der Gildenliste), Platz bei Ausrüstungswert und Spenden innerhalb der Gilde,
  Anteil der Kampfkraft am Gildenwert, Abstand zur nächsten Spende und Anteil an allen Spenden der Gilde.
- **Quest-Fehlerquote (Beobachtungsliste):** gescheiterte Quests geteilt durch alle Quests (geschafft plus gescheitert),
  in Klammern hinter der Zeile "Quests".
- **Schadensminderung (Beobachtungsliste):** der Wert "Mindert Schaden" der Spielerseite im Spiel (`survivalPercent`), also
  der Anteil des eingehenden Schadens, den die Verteidigung abfängt.
- **Ranglisten Silber, Errungenschaften, Quests:** Rang und Wert wie in der Rangliste des Spiels; "24 h" ist die
  Änderung dieses Werts seit gestern (beim Silber kann sie auch negativ sein, wenn jemand etwas ausgibt).
- **Ausrüstung** (nur Beobachtungsliste): eine Zeile je Stück mit Haltbarkeit (D), Stufe (T, nach Material eingefärbt, mit kleinem Schloss bei gebundenen Stücken und einem Edelstein in der Farbe des Werts bei gefassten), Name und ATK/DEF/SUP, darunter die
  Summe und die Kampfkraft. Die Zahlen tragen die Farben des Spiels (ATK rot, DEF blau, SUP grün) mit einem kurzen Balken im Verhältnis zum
  stärksten Wert; eine Haltbarkeit unter 50 % ist gelb, unter 25 % rot. Auf dem Handy rutschen die Werte unter den Namen.
- **Siegquote** (nur Beobachtungsliste): gewonnene von den Kämpfen, an denen der Spieler teilgenommen hat, je Art
  (Abenteuer, Überfälle, Bosse), aus den Gesamtwerten seit Spielbeginn. Dazu Fallquote und Schaden pro Kampf.
- **Silber:** Silber über die Zeit (Top 100 und Beobachtungsliste).
- **Aufsteiger:** größter Zuwachs in 24 Stunden bzw. 7 Tagen.
- **Kämpfe:** Siegquote pro Kampfart der letzten 30 Tage, Bosse nach Name und Stufe, sonst nach Art und Schwierigkeit. Sortiert nach Siegquote, bei gleicher Quote nach Zahl der Kämpfe (mehr zuerst).
  Das Kampfarchiv des Spiels hält nur die letzten 20 Kämpfe, deshalb sammelt der Sammler sie fortlaufend. Die Kampfseiten nennen dazu den Beginn der Erfassung (`since` in `summary.json`, der erste Lauf); frühere Kämpfe fehlen, die Quoten gelten also nur für die Zeit danach. Derselbe Zeitpunkt steht im Seitenfuß.
  Kampfstatistik (`src/fightstats.py`, `summary.json` -> `stats`, letzte 30 Tage), ab 0.9.0:
  - Für jeden neuen Kampf holt der Sammler die Kampfbericht-Daten des Archivs (`/api/combat/history/{id}`, eine Anfrage je Kampf, nur einmal) und speichert daraus nur Summen: Teilnehmer und Gefallene je Rolle (Schildträger, Kämpfer, Unterstützer), Schaden, erlittener Schaden, Heilung und Verstärkung (insgesamt und je Rolle, seit 0.14.0), Runden, Leben des Bosses, mittleres Silber der Überlebenden und der Gefallenen. Namen und Einzelwerte einzelner Spieler werden nicht gespeichert. Beim ersten Lauf nach der Einführung kommen die 20 Kämpfe des Archivs nach; ältere fehlen.
  - Der laufende Kampf (`/api/combat?kompakt=true`, eine Anfrage je Lauf) nennt als Einziger Durchschnitt der Kampfkraft und der Ausrüstung, die Empfehlung und die Kampfwerte (Dauer, Wut, Gruppenstärke); das Archiv hat dort nur Nullen. Der Sammler übernimmt sie für den Kampf, den das Spiel gerade noch anzeigt, einmal je Kampf. Kämpfe, die zwischen zwei Läufen verschwinden, haben keine Kampfkraft; die Seite weist aus, für wie viele sie vorliegt.
  - **Überleben:** Anteil der Gefallenen (Gefallene durch Teilnehmer, alle Kämpfe mit Einzelheiten zusammen), getrennt nach Siegen und Niederlagen. Wer einen Kampf verliert, fällt mit der ganzen Gruppe (bei Bossen durchweg 100 %); deshalb zeigen die Tabellen nach Rolle, Kampfart, Kampf, Kanal, Tag und Kampfkraft-Abstand und die Streamerkarten nur den Anteil in gewonnenen Kämpfen. Die Durchschnitte für Schaden, erlittenen Schaden, Heilung und Verstärkung ("Verstärkt" nennt das Spiel den Schaden, den Unterstützer anderen dazugeben) gelten je Teilnehmer und Kampf und lassen Geschichten ohne Kampf aus (deren Summen sind alle 0). Die Karte "Was jede Rolle leistet" zeigt sie je Rolle, über alle Kampfarten gemittelt; sie füllt sich erst mit Kämpfen, die seit 0.14.0 gesammelt wurden. Der Anteil je einzelnem Kampf steht in den Listen der letzten Kämpfe (unter Start/Kämpfe/Letzte und in der Kampfkraft-Liste), allerdings nur für Kämpfe mit Einzelheiten; dazu Schaden, Heilung, Runden und für Niederlagen das Leben, das der Boss noch hatte.
  - **Spielversion:** Am 04.10.2026 hat das Spiel Abenteuer zu Geschichten umgebaut (kein Mythic mehr, keine Runden). Unter Kampfarten, Überleben, Kampfkraft und Wann und wo lässt sich die Auswahl auf "Seit dem Update" (ab `fightstats.UPDATE`, 03.10.2026 20:33 UTC) oder "Davor" umstellen (`eras.after` / `eras.before` in `summary.json`, dieselben Zahlen wie `stats`, nur für diese Kämpfe); die Auswahl merkt sich der Browser. Sie erscheint, solange beide Seiten Kämpfe haben, also bis die alten aus dem 30-Tage-Fenster laufen. Die Rundenzahl zählt nur bei Kämpfen mit mehr als einer Runde.
  - **Abenteuer:** Seit dem Update stimmt der Chat jede Szene ab. Aus dem Kampfbericht (`log`) speichert der Sammler je Szene Text, gewählte Option, Stimmen, Folge und Wirkung (Gefahr, Lebensverlust, Silber je Kopf, Zahl der Ausgeschiedenen, Kampf ja/nein); die Namen der Ausgeschiedenen werden nur gezählt. `stories` fasst die letzten 30 Tage je Abenteuer zusammen: Läufe, Siegquote und je Szene (Text und Nummer) die gewählten Optionen mit Häufigkeit, Siegquote der Läufe, mittlerem Stimmenanteil und Folge. Der Chat entscheidet mit Mehrheit, andere Optionen sehen wir nur, wenn ein anderer Lauf sie gewählt hat. Davor liegende Abenteuer haben keinen solchen Bericht.
  - **Kampfkraft:** Durchschnitt der Teilnehmer gegen die Empfehlung (Bereiche unter 80 %, 80 bis 100 %, 100 bis 120 %, über 120 %, jeweils mit Siegquote), Kampfkraft der Siege gegen die der Niederlagen je Kampf.
  - **Wann und wo:** Kämpfe und Siegquote je Stunde (Berliner Zeit), je Kanal und je Tag. Braucht keine Einzelheiten.
  Links ins Spiel (öffnen in einem neuen Tab, nur feste Adressen und die Kampf-ID aus dem Archiv): der Kampfname in den Listen der letzten Kämpfe führt zu `/kampfbericht/{id}`, die Spieler- und Gildenseiten zu `/spieler/{login}` und `/gilden/{login}`, die Kampfseiten zu `/kampf`, der Seitenfuß zu Kämpfen, Bestenliste, Gilden, Markt und Kanälen. Es kommen keine zusätzlichen Anfragen dazu.

Alle Werte sind Schätzungen aus dem, was seit Beginn der Aufzeichnung gesammelt wurde. Am Anfang und bei neuen
Spielern fehlen Tempo und Prognose.
