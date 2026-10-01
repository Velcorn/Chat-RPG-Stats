# Changelog

Nur Änderungen, die Besucher der Seite betreffen. Versionen nach [SemVer](https://semver.org/lang/de/). Solange die
Version mit 0 beginnt, ist das Projekt noch in Entwicklung.

## 0.8.3 (01.10.2026)

**Verbessert**
- Bonus-Formel: die Formel von vor dem Kampf-Umbau ist ersetzt durch die Messung danach (Kampfkraft etwa 2,7 x ATK + 0,9 x DEF + 1,6 x SUP, nur an einem Spieler gemessen), mit dem Hinweis, warum sich aus den Ranglisten keine Formel anpassen lässt. Alte Talentzahlen sind als "vor dem Umbau" gekennzeichnet.

## 0.8.2 (01.10.2026)

**Behoben**
- Die Links der letzten Kämpfe zum Kampfbericht im Spiel funktionierten nicht und sind entfernt.

## 0.8.1 (01.10.2026)

**Oberfläche**
- Startseite: die Karten "Fahrender Händler" und "Laufende Kämpfe" sind wieder weg. Bei einem Abruf alle 15 Minuten sind beide fast immer schon vorbei, die Anzeige wäre irreführend. Der Händler bleibt unter Kämpfe, die letzten Kämpfe (mit Link zum Kampfbericht) bleiben auf der Startseite.

## 0.8.0 (01.10.2026)

**Neu**
- Gilden: Durchschnitt der Kampfkraft der aktiven Mitglieder, auf der Startseite und auf der Gildenseite. Die Gildenkarten der Startseite sind danach sortiert (Live zuerst).
- Startseite: Kämpfe, die beim letzten Abruf in den Kanälen liefen, neben dem fahrenden Händler. Die letzten Kämpfe verlinken auf den Kampfbericht im Spiel.

**Oberfläche**
- Die Kennzahlen über der Rangliste Kampfkraft sind weg, die Gesamtkampfkraft der Gilden auch.
- Rangliste Kampfkraft: ATK, DEF und SUP stehen in eigenen Spalten und sind sauber ausgerichtet, die Plätze seit gestern stehen direkt neben dem Rang.

## 0.7.0 (01.10.2026)

**Neu**
- Spielerseite (Beobachtungsliste): Fehlerquote der Quests, also der Anteil gescheiterter Quests, in Klammern hinter der Zeile "Quests".
- "Überleben" heißt jetzt "Schadensminderung", wie im Spiel ("Mindert Schaden"): der Wert sagt, wie viel Schaden die Verteidigung abfängt, nicht wie oft jemand überlebt.

## 0.6.0 (01.10.2026)

**Oberfläche**
- Spielerseite aufgeräumt: der Gildenname steht unter dem Namen, die Karten folgen von oben nach unten (Verlauf und Verteilung, Gilde und Prognose, Rang und Silber, dann die Beobachtungsliste mit eigener Überschrift). Die doppelte Zeile "Nächster Rang" in der Prognose entfällt, sie steht schon in der Kachel.
- Gildenkarte: Kampfkraft steht jetzt vor dem Spendenrang.

**Neu**
- Gildenkarte: "Mitglied seit" und der Anteil an allen Spenden der Gilde.

## 0.5.0 (01.10.2026)

**Neu**
- Startseite: eine Karte je Streamer mit Live-Status, Link zum Stream, Gildenstand und Link zur Spielerseite, dazu der fahrende Händler, die letzten Kämpfe und die Spielersuche. Sie ist jetzt die Standardseite; Ranglisten, Gilden und Kämpfe sind wie gehabt über die Tabs erreichbar. Zuschauerzahl und Titel des Streams gibt das Spiel nicht her.
- Die Streamer stehen standardmäßig auf der Beobachtungsliste und haben damit eine ausführliche Spielerseite.

## 0.4.5 (01.10.2026)

**Oberfläche**
- Gildenseite: der Streamername neben dem Gildennamen entfällt, er steht schon im Tab und in der Adresse.

## 0.4.4 (01.10.2026)

**Behoben**
- Die Daten wurden zeitweise nur einmal am Tag aktualisiert. Jetzt sind sie wieder etwa alle 15 Minuten von 7 bis 24 Uhr frisch.

## 0.4.2 (30.09.2026)

**Geändert**
- Das Repository heißt jetzt `Chat-RPG-Stats`, die Seite liegt unter `https://velcorn.github.io/Chat-RPG-Stats/`. Die alten Adressen leiten weiter.

## 0.4.1 (30.09.2026)

**Oberfläche**
- Bonus-Formel: Hinweis, dass die 225 nur der Achsenabschnitt der Anpassung ist und die Zahlen sich mit mehr Daten ändern werden.

## 0.4.0 (30.09.2026)

**Geändert**
- Der Wert heißt jetzt überall Kampfkraft statt Ausrüstung bzw. Ausrüstungswert, denn so nennt das Spiel ihn seit dem 30.09.2026 (Ausrüstung plus Talentbonus). Die Ausrüstung je Platz bleibt, sie zeigt wirklich die Stücke. Die Adresse der Rangliste ist jetzt `#/rangliste/kampfkraft`.

**Neu**
- Rangliste Kampfkraft: Spalte "Bonus" (Kampfkraft minus ATK, DEF und SUP).
- Unterseite "Bonus-Formel": geschätzte Formel für den Talentbonus, was über die Talente bekannt ist und wo die Schätzung an Grenzen stößt.

## 0.3.1 (30.09.2026)

**Oberfläche**
- Spielerseite aufgeräumt: die Kämpfe zeigen nur noch die eigene Siegquote (ohne Vergleich mit allen Kämpfen, der wegen unterschiedlicher Zeiträume und der Auswahl der Spieler wenig aussagte). Die Diagramme Gildenspende und Markt entfallen; Spendenrang und Markt-Summen stehen weiter als Text.

## 0.3.0 (30.09.2026)

**Neu**
- Spielerseite (Beobachtungsliste): Ausrüstung je Platz mit dem schwächsten Stück, Kampfquoten je Art im Vergleich zu allen Kämpfen, Silber über die Zeit und Markt (Einnahmen minus Ausgaben).

**Geändert**
- Die Quests eines Spielers werden nicht mehr gespeichert und nicht mehr angezeigt (Zeit, Kanal und Text je Quest). Die Gesamtzahlen (geschafft, gescheitert) und die Quest-Rangliste bleiben.

## 0.2.0 (30.09.2026)

**Neu**
- Ranglisten nach Silber und Errungenschaften (zusätzlich zu Ausrüstung und Quests), also alle vier des Spiels.

**Oberfläche**
- Jeder Bereich hat eine zweite Tab-Zeile mit Unterseiten: Ranglisten (Ausrüstung, Silber, Errungenschaften, Quests, Aufsteiger), Gilden (eine Seite pro Gilde), Kämpfe (Kampfarten, letzte Kämpfe, fahrender Händler). Die Gilden-Tabs tragen den Namen des Streamers, der volle Gildenname steht als Überschrift. Die Seiten sind kürzer, die Adressen (`#/gilden/karni`) lassen sich teilen.

## 0.1.1 (30.09.2026)

**Oberfläche**
- Hinweis im Fuß der Seite: fast komplett vibe-coded, Zahlen sind Schätzungen.

## 0.1.0 (30.09.2026)

**Neu**
- Dashboard auf GitHub Pages: Ranglisten mit Trends, Aufsteiger, Spielerseite mit Tempo, Prognose, Vergleich mit ähnlichen Spielern und Gildenstand, Gilden, Kämpfe und fahrender Händler. Die Daten werden alle 15 Minuten von 7 bis 24 Uhr aktualisiert.
- Beobachtungsliste über ein Issue-Formular: Kampfquoten, Markt, Verlosungen und Quests für eingetragene Spieler.
