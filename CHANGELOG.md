# Changelog

Nur Änderungen, die Besucher der Seite betreffen. Bis einschließlich 0.51.3 galt SemVer.
Seitdem gilt CalVer JJJJ.MM.TT mit genau einer Version pro Kalendertag. Weitere Änderungen
desselben Tages kommen in denselben Eintrag. Es gibt keine zusätzlichen Versionssuffixe und keine Git-Tags.

Ältere Angaben wie "seit 0.45.0" in docs/funktionsweise.md und Code-Kommentaren sind alte
SemVer-Nummern und müssen nicht umgeschrieben werden.

Die letzten 30 bisherigen Versionen sind diesen Tagesversionen zugeordnet:

| Alte SemVer | Tagesversion |
| --- | --- |
| 0.51.3 | 2026.10.17 |
| 0.51.2 | 2026.10.17 |
| 0.51.1 | 2026.10.17 |
| 0.51.0 | 2026.10.16 |
| 0.50.3 | 2026.10.16 |
| 0.50.2 | 2026.10.16 |
| 0.50.1 | 2026.10.16 |
| 0.50.0 | 2026.10.16 |
| 0.49.4 | 2026.10.16 |
| 0.49.3 | 2026.10.16 |
| 0.49.2 | 2026.10.16 |
| 0.49.1 | 2026.10.16 |
| 0.49.0 | 2026.10.16 |
| 0.48.0 | 2026.10.16 |
| 0.47.5 | 2026.10.16 |
| 0.47.4 | 2026.10.16 |
| 0.47.3 | 2026.10.16 |
| 0.47.2 | 2026.10.16 |
| 0.47.1 | 2026.10.16 |
| 0.47.0 | 2026.10.16 |
| 0.46.0 | 2026.10.16 |
| 0.45.18 | 2026.10.16 |
| 0.45.17 | 2026.10.16 |
| 0.45.15 | 2026.10.16 |
| 0.45.14 | 2026.10.15 |
| 0.45.13 | 2026.10.15 |
| 0.45.12 | 2026.10.15 |
| 0.45.11 | 2026.10.15 |
| 0.45.10 | 2026.10.15 |
| 0.45.9 | 2026.10.15 |

## 2026.10.21 (21.10.2026)

### Verbessert
- Höchstwerte: Die Zeile "Mit Spezialitems" ist entfallen, denn kein Spezialitem ist insgesamt besser als die normalen Stücke.
- "Wo ein neues Stück am meisten bringt": "Voll ausgebaut" rechnet jetzt das neue Stück mit Schriftrollen und Stein gegen das getragene, wie es ist (vorher wurden beide ausgebaut, dadurch stand dort fast dasselbe wie bei "Jetzt", bei Ringen immer +3).

## 2026.10.20 (20.10.2026)

### Neu
- Neue Seite Spiel > Höchstwerte: das Beste, was Kämpfer (ATK), Schildträger (DEF) und Unterstützer (SUP) tragen können, mit den übrigen Werten und der Summe, ohne Verbesserungen oder voll ausgebaut, mit den normalen Stücken der höchsten Stufe (Spezialitems schlagen sie insgesamt nicht). Zwei Einhandwaffen sind möglich. Darunter steht je Klasse, welches Stück auf welchem Platz sitzt.

### Verbessert
- Formen: Die Tabelle ist mit dem Stand der Community-Tabelle vom 20.10.2026 vollständig für die Stufen 1 bis 14 (alle Formen je Stufe). Gemessen sind jetzt 514 von 562 Werten (vorher viele Näherungen bei Stufe 12 und 14), die Anteile folgen der höchsten gemessenen Stufe. Der Hinweis unter der Tabelle nennt, welche 48 Werte noch Näherungen sind.

### Oberfläche
- Die Startseite zeigt statt des Schlüsselfinales nur noch den letzten Boss: Mittwoch, 28.10.2026, 18:00 Uhr, mit Countdown in Tagen und Stunden. Der Fortschritt der Schlüssel entfällt, alle sind bereit.
- Beträge stehen ohne das Wort "Silber" (die Beschriftung nennt die Einheit schon). Die großen Zahlen in den Kacheln passen sich der Kachelbreite an und werden nicht mehr mit "..." abgeschnitten.

### Geändert
- Das Schlüsselfinale nennt jetzt den angekündigten Termin "Letzter Boss: Mittwoch, 28.10.2026" und zählt in Tagen bis dahin herunter.

### Entfernt
- Die überholte Prognose für den letzten Gildenschlüssel samt Nettofortschritt und geschätzter Fertigstellungszeit ist entfallen. Fragmente, Bedarf, Prozent und Status jeder Gilde bleiben sichtbar.
- Der Schlüsselfortschritt der Gilden wird nicht mehr gesammelt (eine Anfrage weniger je Gilde und Lauf), alle Schlüssel sind bereit.

## 2026.10.19 (19.10.2026)

### Neu
- Die Startseite zeigt den Schlüsselfortschritt aller Gilden und schätzt aus dem Nettofortschritt der letzten 24 Stunden, wann der letzte Schlüssel fertig wird.
- Die Saisonauswahl oben rechts öffnet den laufenden Saisonbericht und später unveränderliche Archive früherer Saisons. Der Bericht zeigt Abschlusskarten, Rangreise, Meilensteine, Top 10 und den Vergleich mit einer anderen Saison; alle normalen Seiten bleiben auch im Archiv erreichbar.

### Verbessert
- Die Oberfläche hebt Kennzahlen deutlicher hervor, trennt Bereiche klarer und bietet auf großen wie kleinen Bildschirmen mehr Luft und größere Bedienflächen.
- Lange Kennzahlenüberschriften passen auch auf 320 Pixel breite Bildschirme. Ranglisten und andere Tabellen zeigen wieder mehr Zeilen auf einmal.
- Das Schlüsselfinale ordnet die Gilden jetzt klar nach ihrem Fortschritt: geschmiedet, bereit, dann absteigend nach Prozent.

## 2026.10.18 (18.10.2026)

### Neu
- Die eigene Seite "Änderungen der Seite" zeigt die bisherigen Änderungen nach Tagen, getrennt von den Änderungen des Spiels.

### Verbessert
- Versionsnummern folgen jetzt dem Kalender (JJJJ.MM.TT): Alle Änderungen eines Tages teilen sich eine Version und einen Eintrag.

## 2026.10.17 (17.10.2026)

### Verbessert
- Spiel, Verbessern: Die Tabelle der Rollen je Versuch ist einer Zeile gewichen (aufgerundet Stufe durch drei), und die Chancen sind vorerst raus: Einzelbeobachtungen sagen nichts, sie sollen später gemeinsam gesammelt werden.

### Oberfläche
- Schrift: Inter, mit der Seite ausgeliefert (kein Laden von fremden Servern).
- Verbessern: Spalte "Punkte der nächsten Stufe" statt "ein Stufen-Schritt"; der Kostensatz nennt das "mal N" nur, wenn der Regelwert nicht 1 ist.

## 2026.10.16 (16.10.2026)

### Neu
- Spezialitems: Fakers Vermächtnis (Stufe 13, Zweihänder, 135/9/0) ist dabei.
- Gegenstandsformen: Die Werte von 41 weiteren Formen sind hinterlegt (Stufe 10 bis 14, vor allem Brustpanzer, Ringe und Zweihänder), auch wenn gerade niemand sie trägt.
- Zeitraffer unter Gilden: "Wert je Perzentil" und "Spieler je Wert" für alle Spieler und jede Gilde über die Tage, mit Abspielknopf, Regler und Geschwindigkeit. Die Kurven gleiten von Zeitpunkt zu Zeitpunkt, der Anfang steht blass dahinter, dazu die Grenze zur Top 100 und der Durchschnitt je Gilde. Der Zeitraffer beginnt am 08.10.2026, weil die Werte der Spieler außerhalb der Top 100 erst ab da ausreichend vorliegen.
- Zeitraffer Top 100 unter Ranglisten: Die Rangliste seit dem ersten Tag als Wettlauf, alle zwei Stunden, mit einer eigenen Farbe für jeden Spieler, Abspielknopf, Regler und Geschwindigkeit. Angezeigt werden die Top 10, 25, 50 oder 100. Ein Klick auf einen Namen öffnet die Spielerseite. Bis zum 05.10.2026 ordnete das Spiel nach Kampfkraft, das steht dabei.
- Zeitraffer unter Gilden: Zoom in beiden Diagrammen. Über einen Bereich ziehen vergrößert ihn (zum Beispiel nur die besten 20 % oder nur die Werte ab 400), Doppelklick oder "Alles zeigen" geht zurück. Die Achsen passen sich an.
- Beide Zeitraffer: ein Regler für das Tempo (von 0,25x bis 4x, in der Mitte 1x, Doppelklick setzt auf 1x) statt der Knöpfe 1x, 2x und 4x.
- Zeitraffer Top 100: Ein Spieler lässt sich verfolgen (Name ins Feld "Spieler verfolgen", mit Vorschlägen). Seine Zeile ist umrahmt, die anderen sind blasser, darunter stehen sein Platz, sein Wert und seine beste Platzierung, auch wenn er außerhalb der gezeigten Top 10, 25, 50 oder 100 liegt.
- Formen: 7 weitere Formen mit ihren Werten (Rüstung der Stufe 10 und 13 mit "des Hospitaliters" und "des Paladins", ein Ring "des Paladins" und ein Stab "der Wacht" der Stufe 13, dazu drei Funde auf niedrigeren Stufen).
- Spezialitems: Die Karte "Änderungen" nennt, was sich an den Werten der Stücke geändert hat (Datum, Stück, Stufe und ATK/DEF/SUP vorher und jetzt). Geänderte Stücke tragen in der Tabelle den Hinweis "geändert" mit dem Datum.
- Spezialitems: Die Robe des Nekromanten ist als Altstück markiert ("fällt nicht mehr"): Sie fehlt in der Beuteliste des Spiels. Der Eintrag bleibt, weil Spieler sie noch tragen, und steht auch im Verlauf unter "Änderungen".
- Spiel, Verbessern: Was das Verbessern mit Schriftrollen bringt (Punkte je Schritt bis +4 für Einhandwaffen, Rüstung, Schilde, Zweihänder und Ringe), wie viele Rollen ein Versuch je Stufe kostet und wie schwer jeder Schritt ist. Die Chancen nennt das Spiel nicht; die Seite zählt beobachtete Versuche und zeigt Prozente ab 30 Versuchen je Schritt.

### Verbessert
- Spezialitems: Die Höllenfeuerhandschuhe haben die neuen Werte (Stufe 13, 45/14/9 statt Stufe 10, 35/14/9).
- Spezialitems: Bei Bossbeute, deren Stufe gleich dem Loot-Tier ist (Oberschenkelknochen, Höllenfeuerhandschuhe), steht beim Vergleich die Stufe des Stücks ("T13"), ohne zweiten Vergleich.
- Spezialitems: Lek'Mhirs Oberschenkelknochen hat die neuen Werte (112/18/6), und die Seite sagt dazu, welche Stücke nachgemessen sind und unverändert blieben.
- Zeitraffer Top 100: langsamer (jeder Schritt ruht kurz, gleitet und ruht wieder), kräftigere Farben mit Farbverlauf in den Balken und Leuchten beim Ersten. Die Balken beginnen unter dem niedrigsten Wert, damit man den Abstand sieht. Top 50 und Top 100 stehen in mehreren Spalten nebeneinander und passen auf einen Bildschirm, auf dem Handy gibt es nur Top 10 und Top 25.
- Zeitraffer Top 100: Farben dezenter (sanfterer Verlauf, kein Leuchten außer beim Ersten, Rang und Wert wieder grau).
- Beide Zeitraffer laufen langsamer: 1x ist jetzt etwa halb so schnell wie vorher, 2x und 4x entsprechend (Gilden: 32 Sekunden für alles bei 1x, Top 100: gut zwei Minuten).
- Zeitraffer unter Gilden: Die Durchschnitte über den Diagrammen zeigen immer eine Nachkommastelle (auch ",0") und feste Ziffernbreite, damit die Zeile beim Abspielen nicht wackelt.
- Zeitraffer Top 100: 1x ist genau ein Schritt je Sekunde (gut drei Minuten für alles).
- Werte und Überleben in Bosssiegen: Die Reiter stehen vom stärksten Boss abwärts (Ostmauer, Mel'Khmal, Loserqueue, ...), und der stärkste ist vorgewählt.
- Spezialitems: Der Hinweis "Werte ändern sich vermutlich bald" bei Mel'Khmal und Ostmauer entfällt, Änderungen stehen jetzt in der Karte "Änderungen".

### Behoben
- Formen: Der Turmschild der Stufe 1 hat 1/7/0 (nicht 0/8/0).
- Spezialitems: Der Zwangsvollstrecker hat 45/5/0 (nicht 45/0/0), so steht es in der Tabelle der Community.
- Formen: Der Turmschild der Stufe 1 ist wieder 0/8/0. Es gibt zwei Turmschilde der Stufe 1 (0/8/0 und 1/7/0), die Seite zeigt den ersten.
- Kämpfe, Kampfkraft: Der Reiter der Ostmauer bei "Werte und Überleben in Bosssiegen" hieß nur "Verteidigung" und war leicht zu übersehen, jetzt steht dort "Ostmauer".

## 2026.10.15 (15.10.2026)

### Neu
- Handy: Die fünf Bereiche sind jetzt eine feste Leiste am unteren Rand (mit dem Daumen erreichbar), oben bleiben Titel und Suche.
- "Das bin ich" auf der Spielerseite merkt sich deinen Namen (nur in diesem Browser); die Startseite zeigt dann zuerst eine Zeile "Du" mit Rang und Ausrüstung.
- Gilden: Die Auswahl der einzelnen Gilde ist ein Aufklappmenü (praktisch, wenn mehr Gilden dazukommen).
- Aufsteiger lassen sich nach Zuwachs oder nach Ausrüstungswert (AW) sortieren.

### Verbessert
- Die Daten werden jetzt rund um die Uhr gesammelt, nicht nur in der Spielzeit des Spiels (die ab heute 9 bis 3 Uhr läuft). Die Fußzeile nennt das, und die Zahl der Läufe am Tag steigt auf 288.
- Von 1 bis 9 Uhr wird nur noch alle 15 Minuten gesammelt (sonst alle 5), zusammen 224 Läufe am Tag.
- Handy: Die Tabellen sind schmaler (kleinere Schrift und Abstände, lange Spaltenköpfe brechen um, weniger wichtige Spalten wie Gilde, Pro Tag, Kasse 7 Tage oder Kanal sind ausgeblendet). Wo eine Tabelle trotzdem breiter ist als der Bildschirm, bleibt die Namensspalte stehen, und ein Schatten am Rand zeigt, dass es seitlich weitergeht. Betrifft die Ranglisten, Gilden, Kämpfe und Letzte Kämpfe.
- Handy: Gilden, Überfälle je Gilde, Rollen und Kämpfe sind kleine Karten statt einer seitlich scrollenden Tabelle.
- Handy: Spaltenköpfe "AW" (Ausrüstungswert) und "KK" (Kampfkraft); die Rangliste behält Rang und Rangänderung beim Scrollen, lässt ATK, DEF und SUP weg, und die Kampfkraft-Rangliste zeigt den Ausrüstungswert nicht mehr.
- Diagramme auf dem Handy: Ein Finger zeigt die Werte (kein Auswählen eines Bereichs mehr), zwei Finger zoomen, senkrechtes Wischen scrollt die Seite.
- Der Reiter "Regeländerungen" heißt "Changelog" wie im Spiel, die Spielerkarte nennt "Ausrüstung" statt "Ausrüstungswert".
- Die Überfallstufe der Gilde steht nicht mehr auf der Gildenseite.
- Handy: Die Top 5 auf der Startseite schreiben "Ausrüstungswert" aus (es passt dort).
- Gilden im Vergleich: Die Spalten "24 h", "7 Tage" und "7 Tage je Mitglied" (Veränderung des Ausrüstungswerts der Gilde) und die Kachel "Schnellster Aufstieg" sind weg: Sie schwankten mit den Wechseln der aktiven Spieler und sagten wenig. Dafür gibt es die Kachel "Meiste Aktive".
- Überfälle je Gilde: Die Spalte "Kasse gewonnen" ist weg, denn bei Überfällen gewinnt die Kasse nie etwas.
- Regeln: Bei "Fehlschlag kostet erst ab" steht jetzt dabei, dass ein Fehlschlag 10 % des Silbers kostet.
- Regeln: Der Text zum Fehlschlag einer Quest ist knapper formuliert.
- Spezialitems: Lek'Mhirs Oberschenkelknochen (jetzt Stufe 13, 88/18/6 statt Stufe 10, 78/18/6) und Mel'Khmals Nasenring (7/28/1 statt 7/21/1) haben die neuen Werte, die Seite sagt dazu, welche Stücke nachgemessen sind.

### Oberfläche
- Spielerseite: Die große Kachel heißt jetzt "Ausrüstungswert" (vorher "Ausrüstung") neben "Kampfkraft"; auf dem Handy stehen dafür "AW" und "KK" klein nebeneinander.
- Spielerseite: Die Kampfkraft steht als kleinerer Wert neben der großen Zahl, ihr Name klein darunter (statt einer zweiten Beschriftungszeile). Auf dem Handy ohne Kürzel.
- Spielerseite, Ausrüstung: Am Computer steht eine Spalte "Platz" zwischen Stufe und Gegenstand (am Handy nicht).

### Behoben
- Handy: Große Beträge in den Kacheln (Kasse) werden nicht mehr abgeschnitten ("5.787.475 Sil...").
- Die Überfallstufe einer Gilde steht nicht mehr in der Kachel "Bosse", sondern in einer eigenen Kachel.

## 2026.10.14 (14.10.2026)

### Neu
- Spielerseite (bei Spielern mit bekannter Ausrüstung): Die Karte "Wo ein neues Stück am meisten bringt" rechnet für eine wählbare Stufe, was ein einfaches neues Stück je Platz bringt: "Jetzt" gegen alle Punkte des getragenen Teils (mit Schriftrollen und Stein, die beim Ersetzen verloren gehen) und "Voll ausgebaut" mit vier Schriftrollen-Stufen und Stein. Sortiert nach "Jetzt", Ringe zählen 3 Punkte weniger (eine Ringstufe bringt nur 3 Punkte).
- Der Knopf "CSV" neben "Teilen" lädt den Verlauf (Ausrüstungswert, Platz, Silber) als Tabelle herunter, für Excel mit Semikolon.
- Der Titel "Chat-RPG Statistik" führt jetzt zum Quellcode auf GitHub (nicht mehr zur Startseite; dafür gibt es den Knopf "Start"). Dahinter stehen die Version der Seite und der Stand der letzten Aktualisierung.
- Ausrüstungsformen: Neue Funde (Profile und Märkte) tragen sich von selbst ein, die gemessenen Werte und die Zeile "Gesehen" bleiben so aktuell.

### Verbessert
- Siegchance und Siegquote nach Abstand zur Empfehlung: Die Kampfkraft rechnet Met, Tränke und andere Boosts im Kampf nicht mit, deshalb lagen die Gruppen meist unter der Empfehlung (die Kurve kreuzt 50 % bei etwa 76 %). Die Seite liest jetzt zusätzlich die Gruppenausrüstung, die das Spiel selbst angibt (mit Talenten, Tränken und Met, wie die Empfehlung gemessen) und nimmt sie, sobald mindestens 10 Bosskämpfe sie haben; bis dahin gilt weiter die Kampfkraft, mit einem Hinweis auf der Karte. Die Karte heißt jetzt "Siegchance nach Gruppenstärke".
- Der Titel öffnet GitHub in einem neuen Tab (statt im selben).
- Ausrüstungsformen: Die ersten Stücke der Stufe 13 und 14 sind gemessen (Boss-Beute und Märkte): Turmschild 3/65/0, Rüstung des Duellanten 37/24/7, des Pilgers 0/24/44, des Kreuzritters 10/20/38 und der Zweihänder des Kriegsherrn 124/22/0 (Stufe 14). Die übrigen Formen dieser Stufen bleiben geschätzt.

### Oberfläche
- Verteilung der Ausrüstungswerte (Spieler je Wert und Wert je Perzentil): Der Name des Spielers und "Platz 100" stehen nicht mehr als Beschriftung im Diagramm, sondern in einer kleinen Legende darunter (mit Linienart und Wert).

### Behoben
- Zwei-Finger-Zoom in den Verlaufsdiagrammen auf dem Handy (Versuch): Der Browser nahm zwei Finger im Diagramm für ein Scrollen der Seite und brach die Geste ab. Das Diagramm hält ihn dabei jetzt zurück. Auf einem echten Handy noch nicht bestätigt.
- Zwei-Finger-Zoom in den Verlaufsdiagrammen auf dem Handy: Er zoomte nur einen winzigen Schritt und brach dann ab, weil das Diagramm bei jedem Schritt neu gezeichnet wurde und dabei die Finger verlor (dann galt wieder das Ziehen mit einem Finger). Der Zustand der Geste liegt jetzt außerhalb der Zeichnung, der Zoom läuft durch.
- Werte und Überleben in Bosssiegen: Beim Darüberfahren über "Gefallen nach Verteidigung" stand bei Schildträgern eine Zahl ohne Namen ("Ø 221") und bei Kämpfern und Unterstützern der Text "null". Die Zeile ist weg, die Zahl steht ohnehin im Diagramm darunter.

### Entfernt
- Der Knopf "CSV" neben "Teilen" auf der Spielerseite ist wieder weg (0.42.0): Er brachte wenig.

## 2026.10.13 (13.10.2026)

### Neu
- Kämpfe > Kampfkraft: Ein Boss, der stärker gemacht wurde (seine empfohlene Ausrüstung hat sich geändert, zuletzt die Ostmauer), taucht mit seinen älteren Kämpfen nicht mehr in der Siegchance und den Tabellen auf. Die Seite liest dafür einmal am Tag das Kompendium des Spiels (eine zusätzliche Anfrage am Tag).
- Die Seite aktualisiert sich alle 5 statt alle 15 Minuten (7 bis 24 Uhr). Damit die Last klein bleibt, liest ein Lauf nur ein Hundertachtzigstel der übrigen aktiven Spieler (jeder wird weiter etwa einmal am Tag gelesen): etwa 36 Anfragen je Lauf, 7.500 am Tag (etwa 7 in der Minute).
- Ausrüstungsformen: Oben lässt sich eine Stufe wählen (1 bis 14), dann zeigen die Tabellen statt der Prozente die konkreten Werte dieser Stufe. Sie stammen aus der Kompendium-Tabelle von fireworker2000, donmerkuzio und AirFighterKI; eine Spalte nennt, ob ein Wert gemessen oder geschätzt ist.
- Unter "Spiel" gibt es den Reiter "Spezialitems": Bossbeute und besondere Waffen (Notwehr des Prinzen, Kutchers linker Haken, Gumayushis Bogen) mit Stufe, Teil, Quelle und ihren festen Werten, nach der Tabelle von fireworker2000, donmerkuzio und AirFighterKI.
- Die Verteilung der Ausrüstungswerte hat Reiter: "Alle" und je eine Gilde (ab 10 aktiven Mitgliedern). Darunter steht, wie viele aktive Spieler gezählt sind.
- Verteilung der Ausrüstungswerte: Ein Umschalter wechselt von "Spieler je Wert" auf "Wert je Perzentil". Dort liegen "Alle" und alle Gilden als Linien in einem Diagramm (X: Anteil der Spieler darunter, Y: Ausrüstungswert), so lassen sich Gilden unabhängig von ihrer Größe vergleichen. Beim Darüberfahren stehen die Werte aller Linien da, darunter je Gruppe Anzahl, Median und Durchschnitt.
- Wert je Perzentil lässt sich vergrößern: mit der Maus über einen Bereich ziehen (Doppelklick zeigt wieder alles) oder mit den Knöpfen "Alles", "Obere 50 %", "Obere 20 %" und "Obere 5 %" (auch auf dem Handy). Die Y-Achse passt sich dem Bereich an.

### Verbessert
- Die Diagramme zeigen keine Punkte mit +/- mehr an den größten Sprüngen.
- Die Platzierungskurve glättet kurze Einbrüche: Fällt jemand um mindestens 5 Plätze und ist im nächsten Lauf wieder da (meist abgelegte und wieder angelegte Ausrüstung), fehlt der Ausreißer.
- Die Verteilung der Ausrüstungswerte nennt bei der Linie für Platz 100 (und beim Spieler) jetzt auch den Wert.
- Spezialitems: besondere Waffen und Bossbeute stehen in zwei getrennten Karten, die Beute nach Boss gruppiert. Bei Mel'Khmal und Ostmauer steht, dass sich die Werte vermutlich bald ändern.
- Spezialitems: Unter der Summe steht, wie viel sie über oder unter einem normalen Stück derselben Stufe und Art liegt (zum Beispiel Gumayushis Bogen "+2 zu 96").
- Spezialitems: Die Bossbeute wird mit einem normalen Stück derselben Stufe und mit einem im Loot-Tier des Bosses verglichen (zum Beispiel Mel'Khmals Streitaxt "+17 zu 86 (T8) | -13 zu 116 (Loot T11)"). Der Vergleich steht jetzt unter dem Namen, damit er auf dem Handy Platz hat.
- Ausrüstungsformen: Die Auswahl der Stufe nutzt jetzt alle Funde aus den Profilen (Stufe 2 bis 12, rund 3.500 Stücke, Steine und Verbesserungen herausgerechnet). Wo es Funde gibt, steht "gemessen" statt der Näherung. Stufe 9 ist komplett gemessen.
- Ausrüstungsformen: Die Werte der Stufenauswahl stammen jetzt auch von den Marktangeboten (alle 2.100 offenen Angebote, einmalig gelesen) und reichen von Stufe 1 bis 12. Damit sind 342 von 480 Kombinationen aus Form und Stufe gemessen statt geschätzt. Das Turmschild hat auf Stufe 1 und 2 zwei Varianten (zum Beispiel 0/8/0 und 1/7/0), die Seite zeigt die häufigere.
- Der Verlauf des Ausrüstungswerts glättet kurze Einbrüche: Fällt der Wert um mindestens 5 % und ist innerhalb einer Stunde wieder mindestens zur Hälfte oben (meist abgelegte und wieder angelegte Ausrüstung), fehlt der Ausreißer.
- Verteilung der Ausrüstungswerte: Alle Reiter ("Alle" und die Gilden) haben dieselbe Skala der Ausrüstungswerte (gleicher Bereich und gleiche Balkenbreite der Ausrüstungswerte; die Höhe passt sich jedem Reiter an), damit sich die Gilden direkt vergleichen lassen.
- Verteilung der Ausrüstungswerte: Die Reiter teilen nur noch die Achse der Ausrüstungswerte (Bereich und Balkenbreite). Die Höhe passt sich wieder jedem Reiter an, damit auch kleine Gilden lesbar bleiben.
- Unter der Verteilung stehen jetzt Median und Durchschnitt der gezeigten Spieler.
- Wert je Perzentil: tolkin ist rot, karni lila und sola blau.
- Wert je Perzentil: Die Knöpfe "Alles", "Obere 50 %", "Obere 20 %" und "Obere 5 %" sind wieder weg. Das Vergrößern geht wie bei den anderen Diagrammen durch Ziehen über einen Bereich, Doppelklick zeigt wieder alles.

### Oberfläche
- Die Karte "Rollen in der Top 100" (Anteil Schildträger, Kämpfer und Unterstützer in der Top 10, 25, 50 und 100) steht jetzt auf der Startseite statt über der Rangliste; die Rangliste beginnt direkt mit der Tabelle.
- Formen aktualisiert: Mit den vielen neuen Stücken der Stufe 11 und 12 stammen jetzt zwanzig weitere Formen von diesen Stufen statt von Stufe 9 (z. B. Festung 9/49/0, Bollwerks 6/44/8, Zerstörer 110/6/0, Turmschild 3/55/0). Waffen in der Schildhand zählen jetzt als Einhandwaffen mit.
- "Kampfkraft je Kampf" ist nach der empfohlenen Ausrüstung sortiert und dann nach der durchschnittlichen Kampfkraft: Die Bosse stehen oben, die Abenteuer (ohne Empfehlung) unten.
- Werte und Überleben in Bosssiegen: Alle drei Rollenkarten zeigen den Anteil Gefallener nach Verteidigung (bei Kämpfern und Unterstützern stand er vorher nach Angriff und Unterstützung, was mit dem Fallen wenig zu tun hat) und darunter, was der Hauptwert der Rolle bringt: eingesteckter Schaden, Schaden oder Verstärkung je Stufe.

### Behoben
- Die Platzierungskurve zeigt keine Lücke mehr, wenn ein Spieler weniger als 6 Stunden aus der Rangliste fehlt (meist abgelegte und wieder angelegte Ausrüstung). Längere Abwesenheiten bleiben als Lücke.
- "des Prinzen" stand als Form bei den Einhandwaffen, ist aber keine: Es gehört zur Waffe "Notwehr des Prinzen". Sie, Kutchers linker Haken und Gumayushis Bogen haben eigene Werte und stehen nicht in der Tabelle (steht jetzt im Hinweis).
- Formen: Viele Zweihänder (Armbrüste, Dreizacke, Kriegshämmer und andere) wurden nicht erkannt, deshalb standen bei einigen Zweihandformen noch Stufe 3, 6 oder 8. Sie zeigen jetzt Funde der Stufen 11 und 12.

### Geändert
- Die Verteilung zählt jetzt nur aktive Spieler (bisher alle Spieler mit Wert, auch lange Inaktive). Die Grenze zu Platz 100 bleibt die der Rangliste aller Spieler.

## 2026.10.12 (12.10.2026)

### Neu
- Alle Verläufe lassen sich vergrößern: über einen Zeitraum ziehen (auf dem Handy mit zwei Fingern), Doppelklick oder "Alles" zurück; Knöpfe für die letzten 24 Stunden und 7 Tage. Der Hinweis nennt die Änderung zum Wert davor und seit dem Anfang des Ausschnitts, die größten Sprünge sind markiert, die Linie zeichnet sich beim Öffnen.
- Spielerseite: Vergleichslinie im Verlauf des Ausrüstungswerts (Grenze Top 100, Platz 1, nächster Platz, beliebiger Spieler), "Verteilung der Werte" als Dreieck aus ATK, DEF und SUP mit allen bekannten Spielern, Verteilung der Ausrüstungswerte als Säulen.
- Startseite: Verteilung der Ausrüstungswerte aller Spieler mit der Grenze zur Top 100.
- Kämpfe > Kampfkraft: Siegchance der Bosse nach Kampfkraft der Gruppe als Punkte und Kurve.
- Ranglisten > Ausrüstungswert: Die Karte "Rollen in der Top 100" zeigt je Top 10, 25, 50 und 100 den Anteil Schildträger, Kämpfer und Unterstützer. Die Rolle wird am größten Wert der Ausrüstung gelesen (Verteidigung, Angriff oder Unterstützung), die gewählte Rolle nennt das Spiel nicht.
- Spielerseite (Top 100 und Beobachtungsliste): Unter "Statistik" zeigt eine kleine Kurve die Schadensminderung nach Verteidigung (100 x DEF / (DEF + 80), wie das Spiel rechnet) mit dem Wert des Spielers und dem Hinweis, wie wenig zehn Punkte Verteidigung mehr noch bringen. Die Zeile "Schadensminderung" steht direkt über der Kurve.

### Oberfläche
- Formen: Die Anteile stehen wieder als ganze Prozent und ergeben trotzdem 100 %: Was die Rundung übrig lässt, steckt im Hauptwert (fett), gleiche Werte bleiben gleich ("des Segens" 19/19/62).
- Spielerseite: Der Vergleich auf den Balken für ATK, DEF und SUP zählt nur noch Spieler derselben Klasse (gleicher Hauptwert) mit ähnlichem Ausrüstungswert. Der Strich ist ihr Median, ein helles Band zeigt ihre mittlere Hälfte. Vorher mischte das Mittel Schildträger, Kämpfer und Unterstützer.
- Spielerseite: Strich und Band auf den Balken für ATK, DEF und SUP sind deutlicher. Der Vergleich nimmt mehr Spieler derselben Klasse (bis 10 % Abstand im Ausrüstungswert, sonst die 20 nächsten), und das Band reicht von 10 bis 90 % statt über die mittlere Hälfte.
- Werte und Überleben in Bosssiegen: Kurven mit Sicherheitsband statt Balken.
- Ausrüstung: Was Schriftrollen und Stein einem Stück geben, steht als grünes "+x" neben dem Wert, den sie erhöhen (die Aufteilung beim Überfahren oder Antippen); das "+4" im Namen und der Edelstein am Stufenfeld fallen weg, das Schloss sitzt unten rechts. Eine kurze Legende erklärt beides, auf dem Handy zeigt ein Antippen den Tooltip. Ältere Lesungen zeigen die Stufe der Verbesserung noch als Marke hinter dem Namen, bis das Profil neu gelesen ist.
- Ausrüstung: Die Stufe einer Verbesserung mit unbekanntem Ziel steht als normaler Text hinter dem Namen statt in einer Box.
- Ausrüstung auf dem Handy: Das "+x" sitzt über der oberen rechten Ecke des Werts, die Spalten sind schmaler, weniger Namen brechen um.
- Ausrüstung auf dem Handy: Das "+x" sitzt weiter rechts und mit mehr Abstand zur Trennlinie über dem Wert, wie eine normale Hochzahl.
- Verläufe: Die markierten Sprünge (+ und -) sind besser lesbar: größere, kräftigere Zahlen mit dunklem Rand und größere Punkte.
- Formen: Die Tabelle rechnet jetzt auch verbesserte und gefasste Stücke ein (deren Schriftrollen- und Steinpunkte werden herausgerechnet) und ist damit auf höheren Stufen genauer: zwölf Formen haben neue Werte von Stufe 10 bis 12 statt 9 (z. B. Berserker 38/20/0, Paladins 0/28/35, Zorns 18/6/6). Nur "des Prinzen" fehlt weiter in den Daten.
- Spielerseite neu geordnet und gestrafft: Verlauf, Ausrüstung, Prognose und Gilde in einer Karte, Rang und Silber, Kämpfe und Statistik; Dreieck und Säulen der Ausrüstungswerte sind eingeklappt ("Vergleich mit allen Spielern"). Weniger Text in Prognose und Gilde, "Mitglied seit" und der Anteil an den Spenden fallen weg (die Anteile stehen noch als Hinweis beim Überfahren).
- Kürzere Texte auf der ganzen Seite, vor allem bei den Formen: ein Satz oben, die Methode in einem Aufklappfeld.
- Kämpfe > Kampfkraft aufgeräumt: Die Siegchance steht oben (mit den Durchschnitten in einer Zeile statt einer eigenen Karte), dann die Tabelle nach Abstand zur Empfehlung; die Tabelle "Kampfkraft je Kampf" ist eingeklappt.
- Formen: Waffen und Schilde stehen links, Rüstung und Ringe rechts.
- Kürzere Texte auf Regeln (jede Regel eine kurze Zeile), Regeländerungen, Kämpfe, Gilden und Ranglisten.

### Behoben
- Formen: Die Anteile stehen mit einer Nachkommastelle und ergeben in jeder Zeile genau 100 % (vorher z. B. "des Segens" 19/19/63 und "Wappenschild" 9/75/15).
- Die markierten Sprünge in den Verläufen überlappen sich nicht mehr (auf dem Handy lagen zwei Zahlen übereinander).

## 2026.10.11 (11.10.2026)

### Neu
- Spielerseite: Die Ausrüstung steht oben in einer Karte wie auf der Charakterseite des Spiels: große Zahl, Kampfkraft, Rang, Änderung in 24 Stunden, Abstand zum nächsten Rang (auf Platz 1 der Vorsprung auf Platz 2), Tempo und Balken für ATK, DEF und SUP mit einem Strich für das Mittel ähnlicher Spieler. Die vier Kacheln und die Karte "Verteilung" sind darin aufgegangen.
- Kämpfe > Kampfkraft: "Werte und Überleben in Bosssiegen" zeigt je Boss, wie viele Schildträger nach Verteidigung fallen und wie viel sie einstecken, wie viel Schaden Kämpfer nach Angriff machen und wie viel Verstärkung Unterstützer nach Unterstützung bringen, dazu das Fallen nach Verteidigung, in Stufen von 10. Gezählt wird ab heute bei jedem neuen Bosskampf, ohne Namen und ohne zusätzliche Anfrage.

### Verbessert
- Kämpfe hat nur noch drei Unterseiten: Übersicht (je Kampf Siege, Teilnehmer, Gefallene und Boss-Leben, dazu Rollen und Überleben), Kampfkraft und Letzte Kämpfe. Überfälle und Bosse je Gilde stehen jetzt im Gilden-Vergleich, Kämpfe nach Uhrzeit, Kanal und Tag entfallen.
- Die Kanalkarten auf der Startseite zeigen nur noch Live-Status, Live-Anteil, Kämpfe und Links; Mitglieder und Kasse stehen auf der Gildenseite. Der Chat-Modus ("Chat langsam") ist weg: Quests laufen über die Seite des Spiels.
- Rangverlauf ohne Lücken: Er beginnt mit der Rangliste nach Ausrüstungswert (04.10.) und überspringt kurze Aussetzer.
- Die Spielerseite nennt keine Bossstufe mehr (es gibt nur noch eine je Boss). "Stärker als 100 %" heißt jetzt "Die meiste Ausrüstung der erfassten Spieler". Neben einem Zweihänder fehlt die leere Schild-Zeile.
- Rangverlauf: Die Beschriftungen "Top 10/25/50" stehen links oder rechts in ihrem Band, wo die Linie Platz lässt, und fehlen, wenn das Band zu schmal ist oder die Linie beide Enden kreuzt.
- Ausrüstung auf dem Handy: Die Haltbarkeit steht klein unter der Stufe, ATK, DEF und SUP stehen in drei schmalen Spalten rechts neben dem Namen wie auf dem großen Bildschirm.
- Ausrüstung und Statistik der Top 100 sind jetzt aktuell: Ändert sich der Ausrüstungswert eines Spielers in der Rangliste, liest der nächste Lauf sein Profil neu, nicht erst am nächsten Morgen. Das kostet im Mittel etwa 6 Anfragen je Lauf mehr (statt 100, wenn alle jedes Mal gelesen würden).
- Formen: 14 Formen auf höheren Stufen nachgeprüft (bis Stufe 12, aus den Profilen der Top 100 und der Beobachtungsliste). Die Spalte "Gesehen" nennt die neuen Werte, die Anteile verschieben sich um höchstens etwa einen Prozentpunkt. Keine neue Form, keine widerspricht der Tabelle; "des Prinzen" ist weiter nicht zu sehen.

### Oberfläche
- "Werte und Überleben in Bosssiegen" in drei Rollenkarten nebeneinander (auf dem Handy untereinander): Stufen von 20, je Zeile ein Balken für den Anteil Gefallener und einer für Einstecken, Schaden oder Verstärkung. Die Tabellen "nach Verteidigung" für Kämpfer und Unterstützer entfallen, sie zeigten keinen Unterschied.
- Abenteuer stehen nur mit ihrem Namen da, ohne Beutespanne: Seit dem Spiel-Update vom 11.10.2026 gibt ein Abenteuer jedem höchstens die eigene Stufe.

### Behoben
- ATK, DEF und SUP in der Rangliste und auf der Spielerseite zählen jetzt Verbesserungen und Steine mit. Die Rangliste des Spiels nennt die Werte ohne sie; die Seite nimmt die Summen der Ausrüstung aus dem letzten Profil, solange sie zum Ausrüstungswert passen.
- Spieler auf der Beobachtungsliste außerhalb der Top 100 hatten auf ihrer Seite keine Ausrüstung und Statistik, obwohl ihr Profil bei jedem Lauf gelesen wurde (seit 0.23.0, der Lauf in zwei Teilen: der erste Teil, nach dem die Seite gebaut wird, vergaß ihre Profile).

## 2026.10.10 (10.10.2026)

### Neu
- Spiel -> Regeln: Oben steht, wann sich zuletzt eine Regel geändert hat und wann zuletzt geprüft wurde; bei jeder Regel, deren Änderung gemessen wurde, steht ihr Zeitpunkt.
- Ranglisten -> Kampfkraft: die Top 100 aller erfassten Spieler nach der Kampfkraft (Ausrüstung plus Talente) mit der Veränderung in 24 Stunden, daneben der Ausrüstungswert. Die Reihenfolge weicht von der des Spiels deutlich ab.
- Startseite: Der Spieler mit dem höchsten Ausrüstungswert ist anklickbar.

### Verbessert
- Die Erklärungen aller Regeln neu geschrieben, nach dem Handbuch und den Seiten des Spiels statt nach Vermutung. Mehrere stimmten nicht: Schriftrollen (je Versuch, nicht je drei Stufen), die Wartezeit zum Zurückziehen eines Angebots (für das eigene Angebot, nicht für Käufe), Quests bis zum Kampf (davor zieht man als Begleiter mit), das Aktivitätsfenster (gilt für Truhen) und der Händlerpreis (Richtpreis, nicht fest).
- Kompendium: Hinweis, dass die dort geführten Abenteuer die von vor dem 04.10. sind.
- Regeln: Die Hinweise zur Abenteuer-Beute und zur Spielzeit geben nur noch wieder, was das Spiel selbst dazu schreibt.
- Der Sammler fragt zwei Ranglisten und das Kompendium nicht mehr ab: etwa 3 Anfragen weniger je Lauf.
- Die Seite erscheint früher mit den Ranglisten, Gilden, Kämpfen und Kanälen: Der Sammler veröffentlicht sie jetzt nach etwa 40 Sekunden und liest erst danach die Profile (Beobachtungsliste, Top 100, Scheibe der übrigen Spieler), die dann beim nächsten Lauf auf der Seite stehen. Die Rangliste ist damit um gut zwei Minuten aktueller, die Zahl der Anfragen bleibt gleich.
- Kämpfe heißen in den Listen jetzt wie im Spiel: Abenteuer nur mit Namen ("Der Gipfel der Stürme"), Überfälle mit Namen und Schwierigkeit ("Harpyienschwarm 5"), statt "Name (Überfall Schwierigkeit 5)". Bosse stehen ohne Stufe da, denn es gibt nur noch eine je Boss.
- Abenteuer nennen hinter dem Namen die Stufen, die dort bisher als Beute fielen ("Der Gipfel der Stürme 6-10"). Die Spannen sind von Hand beobachtet (Stand 10.10.2026, je Abenteuer nur wenige Läufe) und können noch wachsen.
- Bei den Kämpfen steht die Auswahl jetzt auf "Seit dem Update (04.10.)"; "Alle" und "Davor" bleiben wählbar. Kampfarten sind nach Zahl der Kämpfe sortiert, Arten mit weniger als 5 Kämpfen stehen nur noch als Zeile darunter.
- Erste Siege über die Bosse: eine Zeile je Boss ohne Stufe.

### Behoben
- Abenteuer-Geschichten heißen nicht mehr "Abenteuer Schwierigkeit 3" und tragen die 3 nicht mehr im Titel: Alle Geschichten kommen seit dem 04.10. mit Schwierigkeit 3, die Zahl sagt nichts.
- Aufsteiger: Spieler, deren gemessener Wert kurz eingebrochen war (am 08. und 09.10. bei etwa zwei Dutzend auf 0 bis 60 % ihrer Ausrüstung) und dann zurückkehrte, führten die Liste mit Zuwächsen um +300 an. Gezählt wird jetzt nur noch, was über dem eigenen Höchstwert der Vorwoche liegt; ein Wiederanstieg nach einem Einbruch ist kein Aufstieg.
- In den Tabellen nach Kampf und Kampfart stehen Abenteuer und Überfälle jetzt mit ihrem Namen ("Der Gipfel der Stürme", "Harpyienschwarm 5") und werden je Name ausgewertet. Vorher standen dort nur "Abenteuer" und "Überfall 5", weil die Tabellen nach Art und Schwierigkeit zusammenfassten.
- Aufsteiger (7 Tage): Die Liste war leer, weil bis zum 04.10. die Rangliste des Spiels die Kampfkraft war und ihre Höchstwerte jeden Anstieg verdeckten. Gezählt werden nur noch Werte ab dem 04.10. (22 Uhr UTC); die 7-Tage-Liste füllt sich ab dem 11.10.

### Entfernt
- Was das Spiel selbst genauso zeigt: das Kompendium, die Ranglisten Silber, Errungenschaften und Quests sowie die Tabellen Gebäude und Gildenbosse auf den Gildenseiten. Der Gildenvergleich zeigt die Stufen weiter.
- Die Rangliste "Ausrüstungswert" liegt jetzt unter `#/rangliste/ausruestungswert`; unter `#/rangliste/kampfkraft` steht die neue Rangliste.
- Die Tabelle "Gebäude und Gildenbosse" im Gildenvergleich ist weg. Sie war fehlerhaft und zeigte nur, was das Spiel auf seiner Gildenseite selbst zeigt.
- Die Unterseite "Abenteuer" unter Kämpfe (Wahlen des Chats je Szene) ist weg: zu lang und ohne Nutzen für die Entscheidungen im Spiel.
- "Wirtschaft" unter Spiel ist weg. Der Verlauf des Silbers in den Gildenkassen steht jetzt im Gildenvergleich; das Silber der Top 100 entfällt.
- Unter Spiel steht nur noch, wann sich eine Regel geändert hat ("Regeländerungen"). Das Änderungsprotokoll des Spiels gibt die Seite nicht mehr wieder, es steht im Spiel.
- Die Karte "Aufsteiger" auf der Startseite, die zweite Tabelle "Letzte Kämpfe mit Kampfkraft" unter Kampfkraft und die Spalte "Ø Runden" (Runden gibt es seit dem 04.10. nicht mehr).

## 2026.10.09 (09.10.2026)

### Neu
- Für die Top 100 der Rangliste gibt es jetzt auch Ausrüstung je Platz, Kampfquoten und Schadensminderung, einmal am Tag aktualisiert.
- Gildenseite: die neuen Gebäude (Feldkasse, Akademie, Archiv, Handelsposten, Hochofen) mit Unterhalt und Bauzeit.
- Spiel -> Formen: Wie jede Namensendung ("des Schlächters", "des Pilgers", ...) die Punkte eines Stücks auf Angriff, Verteidigung und Unterstützung verteilt, für Rüstung, Waffen, Ringe und Schilde, mit den Werten der höchsten gesehenen Stufe. Nach einer Übersicht von fireworker2000 (Discord), nachgeprüft an beobachteter Ausrüstung und Marktangeboten.

### Verbessert
- Die Top 100 werden jeden Tag im ersten Lauf (um 7 Uhr) alle auf einmal aktualisiert, statt über den Tag verteilt. Ihre Ausrüstung und Kampfquoten sind damit zur gleichen Zeit gleich alt.

### Oberfläche
- Die Gebäude- und Bosstabellen der Gildenseite stehen untereinander in voller Breite statt abgeschnitten nebeneinander.
- Formen: Am Desktop stehen die Karten in zwei gleich hohen Spalten, und alle Tabellen haben dieselben Spaltenbreiten, damit die Balken untereinander ausgerichtet sind und nichts abgeschnitten wird.
- Formen: Beide Spalten enden am Desktop auf gleicher Höhe (die letzte Karte der kürzeren Spalte füllt den Rest), die Hinweise zu den Einhandwaffen stehen jetzt im Textblock unten.

## 2026.10.08 (08.10.2026)

### Oberfläche
- Die Stufe in der Ausrüstung ist nach dem Material des Stücks eingefärbt (von Holz bis Nova, die Farben stammen aus den Item-Symbolen des Spiels). Am Stufenfeld zeigt oben links ein kleines Schloss gebundene Stücke (Händler, Schmiede, Siegel, eigener Laden), die nicht auf den Markt dürfen, und oben rechts ein Edelstein ein gefasstes Stück, in der Farbe des Werts (Angriff rot, Verteidigung blau, Unterstützung grün).

## 2026.10.07 (07.10.2026)

### Neu
- Gilden: Im Vergleich stehen die ersten Siege der Gilden über jeden Boss (Stufe, Gilde, Zeitpunkt), auf der Gildenseite die der eigenen Gilde. Das Lager ist als fünftes Gebäude dabei, die Werkstatt heißt wie im Spiel Schmiede; die Gebäude nennen Wirkung und Sperre der nächsten Stufe.
- Kämpfe: neue Seite "Gilden" mit den Überfällen auf die Kasse jeder Gilde (abgewehrt, Silber verloren und gewonnen) und den beschworenen Bossen. Die letzten Kämpfe zeigen Gilde und Kassenänderung. Beides wird erst ab diesem Stand gesammelt.
- Spiel: Das Kompendium zeigt die Schmiede-Stufen und die Waren des Lagers.
- Spiel: Die Seite "Änderungen" zeigt jetzt auch das Änderungsprotokoll des Spiels, nach Tagen sortiert und zum Aufklappen, zwischen den gemessenen Regeländerungen.
- Kämpfe, Überleben: Die Tabelle nach Kampfart zeigt jetzt auch Heilung und Verstärkung (der Schaden, den Unterstützer anderen dazugeben), die Kennzahlen dazu die Verstärkung.
- Neue Karte "Was jede Rolle leistet": Schaden, erlittener Schaden, Heilung und Verstärkung je Rolle. Sie füllt sich mit den Kämpfen, die ab jetzt gesammelt werden.
- Der Sammler liest einmal am Tag das Profil jedes aktiven Gildenmitglieds (rund 55 Anfragen mehr je Lauf, etwa 4.900 statt 1.200 am Tag). Der Vergleich mit ähnlichen Spielern zeigt dadurch für alle die eigene Verteilung.
- Die Grenze zur Top 100 ist der Ausrüstungswert des Spielers auf Platz 100; die Kampfkraft steht als Zeile auf der Spielerseite.

### Verbessert
- Das Kompendium nennt sechs Bosse und keine Tränke mehr, weil das Lager den Alchemisten ersetzt hat.

### Oberfläche
- Die Ausrüstung auf der Spielerseite ist neu gestaltet: eine Zeile je Stück mit Haltbarkeit (D), Stufe (T), Name und ATK/DEF/SUP in Rot, Blau und Grün mit kurzen Balken, dazu eine Summenzeile. Auf dem Handy stehen die Werte unter dem Namen.
- Der Vergleich mit ähnlichen Spielern nutzt dieselben Farben (Angriff rot, Verteidigung blau, Unterstützung grün); deine Werte sind kräftig, das Mittel der anderen blass.
- Die Verlaufsdiagramme sehen neu aus: eine Stufenlinie (ein Wert gilt, bis der nächste kommt) mit Fläche darunter, gestrichelten Hilfslinien und einem Wertschild am Ende. Im Rangdiagramm sind die Bereiche Top 10, Top 25 und Top 50 hinterlegt.
- Die Ausrüstung auf der Spielerseite nennt unter der Summe auch die Kampfkraft; die Kachel des Ausrüstungswerts zeigt sie neben der Zahl: das Wort in der Titelzeile, die Zahl halb so groß und oben bündig mit dem Ausrüstungswert.

### Behoben
- Die Durchschnitte für Schaden, erlittenen Schaden und Heilung zählten Geschichten mit, in denen es nicht zum Kampf kam (alle Werte 0). Sie waren dadurch zu niedrig.

### Inkompatibel
- Rang, Verlauf, Tempo, Aufsteiger, Prognose, Gilden-Durchschnitt und Spielerseiten rechnen jetzt mit dem Ausrüstungswert (Angriff + Verteidigung + Unterstützung) statt mit der Kampfkraft. Der Verlauf beginnt dadurch neu, Tempo und Aufsteiger gibt es erst nach einem halben bis einem Tag wieder.
- Spieler, die laut Gilde nicht aktiv sind, haben keinen Ausrüstungswert und fehlen deshalb in Rang, Suche und Prognose.

### Geändert
- Der Wert aus der Rangliste heißt auf der ganzen Seite wieder Ausrüstungswert statt Kampfkraft (Ranglisten, Gilden, Start, Spielerseite). "Kampfkraft" bleibt nur auf den Kampfseiten, wo es den Durchschnitt aus Ausrüstung und Talenten gegen die Empfehlung meint.
- Spielerseite, Ausrüstung: Die Markierung "schwächstes" ist weg. Statt "beschädigt" steht die Haltbarkeit in Prozent, sobald ein Stück unter 100 % liegt.
- Die Werte von den Gildenseiten heißen jetzt wieder Kampfkraft statt Ausrüstungswert: Verlauf, Tempo, Aufsteiger, Gilden, Start und Spielerseiten. Das Spiel liefert dort Ausrüstung plus Talente (bei einem Spieler mit Ausrüstungswert 328 sind es 360), nicht den reinen Ausrüstungswert.
- Den reinen Ausrüstungswert gibt es nur für die Top 100: In der Rangliste steht die Kampfkraft jetzt als eigene Spalte daneben, auf der Spielerseite steht er als Zeile unter "Prognose".
- Die Grenze zur Top 100 in der Prognose ist die Kampfkraft des Spielers auf Platz 100, damit der Abstand zur eigenen Kampfkraft passt.

### Entfernt
- Die Seite "Bonus-Formel" und die Spalte "Bonus" in der Kampfkraft-Rangliste: Seit dem Umbau der Talente am 04.10.2026 zählt die Rangliste nur noch ATK, DEF und SUP.

### Hinweis
- Am ersten Tag nach der Umstellung sind noch nicht alle aktiven Spieler gelesen, der Rang fällt dann etwas zu gut aus.

## 2026.10.04 (04.10.2026)

### Neu
- Kämpfe: neue Seite "Abenteuer". Seit dem Update vom 04.10.2026 stimmt der Chat in Abenteuern jede Szene ab. Die Seite zeigt je Abenteuer die Szenen, was der Chat gewählt hat, wie oft das zum Sieg führte und was die Wahl bewirkte (Gefahr, Leben, Silber, Ausgeschiedene).
- Kämpfe: Bei Kampfarten, Überleben, Kampfkraft und Wann und wo lassen sich die Zahlen auf die Zeit seit dem Update oder davor beschränken, weil das Spiel Abenteuer und Kämpfe umgebaut hat.
- Gilden: Gebäude (Werkstatt, Kontor, Kriegskasse, Wall) mit Stufe, Wirkung und Preis der nächsten Stufe sowie der Bossfortschritt (höchste besiegte Stufe, Preis der nächsten) im Vergleich und auf jeder Gildenseite.
- Spiel: neue Seite "Kompendium" mit Tränken, Stufen, Bossen (Beutestufen, empfohlene Ausrüstung, Hortstücke), Kampfarten und Projekten.

### Verbessert
- Die Rundenzahl zählt nur noch bei Kämpfen mit mehr als einer Runde (Abenteuer haben seit dem Update keine Runden mehr).

## 2026.10.03 (03.10.2026)

### Neu
- Gilden: neue Seite "Vergleich" mit allen Gilden nebeneinander (Mitglieder, Kampfkraft, Zuwachs in 24 Stunden und 7 Tagen, auch je Mitglied, Kasse, Spenden, Bosse).
- Spiel: neuer Bereich mit "Wirtschaft" (Silber in den Gildenkassen und bei den Top 100 im Verlauf), "Regeln" (die aktuellen Regeln des Spiels) und "Änderungen" (jede Regeländerung mit Zeitpunkt, Vorher und Nachher). Der Markt fehlt, er ist ohne Anmeldung nicht lesbar.
- Startseite: Die Streamerkarten zeigen den Chat-Modus (normal, langsam, still), den Live-Anteil und die Kämpfe des Kanals.
- Spielerseiten: Knopf "Teilen" kopiert eine Kurzfassung mit Link, dazu der Vergleich "Stärker als x % der erfassten Spieler".
- Kämpfe: Die Liste der letzten Kämpfe und die Kampfkraft-Liste zeigen, wie viel Prozent der Teilnehmer im jeweiligen Kampf gefallen sind (nur bei Kämpfen mit Einzelheiten).

### Verbessert
- Regeln: nach Themen gruppiert, mit einem Satz zur Bedeutung jeder Regel.
- Startseite: Kennzahlen, Top 5, Aufsteiger der letzten 24 Stunden, Gildenüberblick und "Zuletzt" statt der Kampfliste (die gibt es weiter unter Kämpfe, "Letzte").
- Überleben: Wer einen Kampf verliert, fällt mit der ganzen Gruppe, die 100 % sagten nichts aus. Rolle, Kampfart, Kampf, Kanal, Tag und die Streamerkarten zählen jetzt nur das Fallen in gewonnenen Kämpfen, die Spalte "bei Niederlage" entfällt.
- Bonus-Formel: neue Messung an 70 Ausrüstungszuständen nach den zwei Änderungen des Spiels am 03.10.2026 (Kampfkraft etwa 3,0 x ATK + 0,8 x DEF + 2,7 x SUP - 14, Abweichung um 9), mit dem Knick bei hoher Verteidigung und einem Beispiel, in dem Handschuhe mit weniger Ausrüstung mehr Kampfkraft bringen.

### Behoben
- Gilden: Die Vergleichsseite sortiert jetzt nach der durchschnittlichen Kampfkraft (vorher nach der Summe, deshalb stand die größte Gilde oben). Die Kacheln nennen den Streamer-Namen statt des langen Gildennamens, Gilden mit weniger als 10 aktiven Mitgliedern gewinnen keine Kachel mehr.

## 2026.10.02 (02.10.2026)

### Neu
- Links ins Spiel: Der Kampfname in den Listen der letzten Kämpfe führt zum Kampfbericht, die Spieler- und Gildenseiten haben "Im Spiel", die Kampfseiten verlinken die Kämpfe des Spiels, und der Seitenfuß führt zu Kämpfen, Bestenliste, Gilden, Markt und Kanälen.
- Kampf-Statistik mit drei neuen Seiten unter Kämpfe. "Überleben": wie viele Teilnehmer fallen (insgesamt, bei Siegen und Niederlagen, je Rolle, Kampfart und Kampf), dazu Schaden, Heilung, Runden und das Restleben des Bosses nach Niederlagen. "Kampfkraft": die durchschnittliche Kampfkraft der Teilnehmer gegen die Empfehlung des Spiels, mit Siegquote je Abstand. "Wann und wo": Kämpfe und Siegquote je Uhrzeit, Kanal und Tag.
- Die Einzelheiten kommen aus den Kampfberichten des Spiels (eine zusätzliche Anfrage je neuem Kampf, etwa 100 am Tag) und dem laufenden Kampf (eine pro Lauf); gespeichert werden nur Summen je Kampf. Sie gibt es erst ab dem ersten Lauf nach dieser Version, die Seiten nennen den Beginn.

### Verbessert
- Bonus-Formel: neue Messung an 220 statt 14 Ausrüstungszuständen (Kampfkraft etwa 2,7 x ATK + 0,8 x DEF + 2,3 x SUP - 20, Abweichung um 15), dazu die genaue Formel der Schadensminderung. Die Gewichte von vorher (0,9 DEF, 1,6 SUP) stimmten nicht mehr.
- Kämpfe: Die Kampfarten sind nach Siegquote sortiert, bei gleicher Quote nach der Zahl der Kämpfe, nicht mehr alphabetisch.
- Kämpfe: Die Kampfseiten und der Seitenfuß zeigen, seit wann die Daten erfasst werden ("Erfasst wird seit 30.09.2026, 17:48 Uhr, frühere Kämpfe fehlen"), denn die Siegquoten gelten nur für diese Zeit.

## 2026.10.01 (01.10.2026)

### Neu
- Startseite: eine Karte je Streamer mit Live-Status, Link zum Stream, Gildenstand und Link zur Spielerseite, dazu der fahrende Händler, die letzten Kämpfe und die Spielersuche. Sie ist jetzt die Standardseite; Ranglisten, Gilden und Kämpfe sind wie gehabt über die Tabs erreichbar. Zuschauerzahl und Titel des Streams gibt das Spiel nicht her.
- Die Streamer stehen standardmäßig auf der Beobachtungsliste und haben damit eine ausführliche Spielerseite.
- Gildenkarte: "Mitglied seit" und der Anteil an allen Spenden der Gilde.
- Spielerseite (Beobachtungsliste): Fehlerquote der Quests, also der Anteil gescheiterter Quests, in Klammern hinter der Zeile "Quests".
- "Überleben" heißt jetzt "Schadensminderung", wie im Spiel ("Mindert Schaden"): der Wert sagt, wie viel Schaden die Verteidigung abfängt, nicht wie oft jemand überlebt.
- Gilden: Durchschnitt der Kampfkraft der aktiven Mitglieder, auf der Startseite und auf der Gildenseite. Die Gildenkarten der Startseite sind danach sortiert (Live zuerst).
- Startseite: Kämpfe, die beim letzten Abruf in den Kanälen liefen, neben dem fahrenden Händler. Die letzten Kämpfe verlinken auf den Kampfbericht im Spiel.
- Der Fuß der Seite nennt, wie viele Anfragen die Seite täglich an das Spiel schickt (Anfragen des letzten Laufs mal 68 Läufe am Tag). Der Sammler hält die Zahl pro Lauf fest; sie erscheint nach dem nächsten Lauf.

### Verbessert
- Bonus-Formel: die Formel von vor dem Kampf-Umbau ist ersetzt durch die Messung danach (Kampfkraft etwa 2,7 x ATK + 0,9 x DEF + 1,6 x SUP, nur an einem Spieler gemessen), mit dem Hinweis, warum sich aus den Ranglisten keine Formel anpassen lässt. Alte Talentzahlen sind als "vor dem Umbau" gekennzeichnet.

### Oberfläche
- Gildenseite: der Streamername neben dem Gildennamen entfällt, er steht schon im Tab und in der Adresse.
- Spielerseite aufgeräumt: der Gildenname steht unter dem Namen, die Karten folgen von oben nach unten (Verlauf und Verteilung, Gilde und Prognose, Rang und Silber, dann die Beobachtungsliste mit eigener Überschrift). Die doppelte Zeile "Nächster Rang" in der Prognose entfällt, sie steht schon in der Kachel.
- Gildenkarte: Kampfkraft steht jetzt vor dem Spendenrang.
- Die Kennzahlen über der Rangliste Kampfkraft sind weg, die Gesamtkampfkraft der Gilden auch.
- Rangliste Kampfkraft: ATK, DEF und SUP stehen in eigenen Spalten und sind sauber ausgerichtet, die Plätze seit gestern stehen direkt neben dem Rang.
- Startseite: die Karten "Fahrender Händler" und "Laufende Kämpfe" sind wieder weg. Bei einem Abruf alle 15 Minuten sind beide fast immer schon vorbei, die Anzeige wäre irreführend. Der Händler bleibt unter Kämpfe, die letzten Kämpfe (mit Link zum Kampfbericht) bleiben auf der Startseite.
- Die Unterseite "Fahrender Händler" ist weg (bei einem Abruf alle 15 Minuten kaum aussagekräftig); der Sammler fragt den Händler auch nicht mehr ab.

### Behoben
- Die Daten wurden zeitweise nur einmal am Tag aktualisiert. Jetzt sind sie wieder etwa alle 15 Minuten von 7 bis 24 Uhr frisch.
- Die Links der letzten Kämpfe zum Kampfbericht im Spiel funktionierten nicht und sind entfernt.
- Ein Tippfehler in der Menüliste der Kämpfe (beim Entfernen der Händlerseite) ließ das Skript der Seite nicht laufen; behoben, ein Test prüft das Skript jetzt auf Syntaxfehler.
- Die Seite zeigte nur "Keine Daten": die Zeile mit den täglichen Anfragen im Fuß (0.8.4) überdeckte die Funktion zum Laden der Daten. Behoben.

## 2026.09.30 (30.09.2026)

### Neu
- Dashboard auf GitHub Pages: Ranglisten mit Trends, Aufsteiger, Spielerseite mit Tempo, Prognose, Vergleich mit ähnlichen Spielern und Gildenstand, Gilden, Kämpfe und fahrender Händler. Die Daten werden alle 15 Minuten von 7 bis 24 Uhr aktualisiert.
- Beobachtungsliste über ein Issue-Formular: Kampfquoten, Markt, Verlosungen und Quests für eingetragene Spieler.
- Ranglisten nach Silber und Errungenschaften (zusätzlich zu Ausrüstung und Quests), also alle vier des Spiels.
- Spielerseite (Beobachtungsliste): Ausrüstung je Platz mit dem schwächsten Stück, Kampfquoten je Art im Vergleich zu allen Kämpfen, Silber über die Zeit und Markt (Einnahmen minus Ausgaben).
- Rangliste Kampfkraft: Spalte "Bonus" (Kampfkraft minus ATK, DEF und SUP).
- Unterseite "Bonus-Formel": geschätzte Formel für den Talentbonus, was über die Talente bekannt ist und wo die Schätzung an Grenzen stößt.

### Oberfläche
- Hinweis im Fuß der Seite: fast komplett vibe-coded, Zahlen sind Schätzungen.
- Jeder Bereich hat eine zweite Tab-Zeile mit Unterseiten: Ranglisten (Ausrüstung, Silber, Errungenschaften, Quests, Aufsteiger), Gilden (eine Seite pro Gilde), Kämpfe (Kampfarten, letzte Kämpfe, fahrender Händler). Die Gilden-Tabs tragen den Namen des Streamers, der volle Gildenname steht als Überschrift. Die Seiten sind kürzer, die Adressen (`#/gilden/karni`) lassen sich teilen.
- Spielerseite aufgeräumt: die Kämpfe zeigen nur noch die eigene Siegquote (ohne Vergleich mit allen Kämpfen, der wegen unterschiedlicher Zeiträume und der Auswahl der Spieler wenig aussagte). Die Diagramme Gildenspende und Markt entfallen; Spendenrang und Markt-Summen stehen weiter als Text.
- Bonus-Formel: Hinweis, dass die 225 nur der Achsenabschnitt der Anpassung ist und die Zahlen sich mit mehr Daten ändern werden.

### Geändert
- Die Quests eines Spielers werden nicht mehr gespeichert und nicht mehr angezeigt (Zeit, Kanal und Text je Quest). Die Gesamtzahlen (geschafft, gescheitert) und die Quest-Rangliste bleiben.
- Der Wert heißt jetzt überall Kampfkraft statt Ausrüstung bzw. Ausrüstungswert, denn so nennt das Spiel ihn seit dem 30.09.2026 (Ausrüstung plus Talentbonus). Die Ausrüstung je Platz bleibt, sie zeigt wirklich die Stücke. Die Adresse der Rangliste ist jetzt `#/rangliste/kampfkraft`.
- Das Repository heißt jetzt `Chat-RPG-Stats`, die Seite liegt unter `https://velcorn.github.io/Chat-RPG-Stats/`. Die alten Adressen leiten weiter.
