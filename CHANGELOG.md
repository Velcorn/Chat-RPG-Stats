# Changelog

Nur Änderungen, die Besucher der Seite betreffen. Versionen nach [SemVer](https://semver.org/lang/de/). Solange die
Version mit 0 beginnt, ist das Projekt noch in Entwicklung.

## 0.11.0 (04.10.2026)

**Neu**
- Kämpfe: neue Seite "Abenteuer". Seit dem Update vom 04.10.2026 stimmt der Chat in Abenteuern jede Szene ab. Die Seite zeigt je Abenteuer die Szenen, was der Chat gewählt hat, wie oft das zum Sieg führte und was die Wahl bewirkte (Gefahr, Leben, Silber, Ausgeschiedene).
- Kämpfe: Bei Kampfarten, Überleben, Kampfkraft und Wann und wo lassen sich die Zahlen auf die Zeit seit dem Update oder davor beschränken, weil das Spiel Abenteuer und Kämpfe umgebaut hat.
- Gilden: Gebäude (Werkstatt, Kontor, Kriegskasse, Wall) mit Stufe, Wirkung und Preis der nächsten Stufe sowie der Bossfortschritt (höchste besiegte Stufe, Preis der nächsten) im Vergleich und auf jeder Gildenseite.
- Spiel: neue Seite "Kompendium" mit Tränken, Stufen, Bossen (Beutestufen, empfohlene Ausrüstung, Hortstücke), Kampfarten und Projekten.

**Verbessert**
- Die Rundenzahl zählt nur noch bei Kämpfen mit mehr als einer Runde (Abenteuer haben seit dem Update keine Runden mehr).

## 0.10.3 (03.10.2026)

**Verbessert**
- Bonus-Formel: neue Messung an 70 Ausrüstungszuständen nach den zwei Änderungen des Spiels am 03.10.2026 (Kampfkraft etwa 3,0 x ATK + 0,8 x DEF + 2,7 x SUP - 14, Abweichung um 9), mit dem Knick bei hoher Verteidigung und einem Beispiel, in dem Handschuhe mit weniger Ausrüstung mehr Kampfkraft bringen.

## 0.10.2 (03.10.2026)

**Neu**
- Kämpfe: Die Liste der letzten Kämpfe und die Kampfkraft-Liste zeigen, wie viel Prozent der Teilnehmer im jeweiligen Kampf gefallen sind (nur bei Kämpfen mit Einzelheiten).

**Verbessert**
- Überleben: Wer einen Kampf verliert, fällt mit der ganzen Gruppe, die 100 % sagten nichts aus. Rolle, Kampfart, Kampf, Kanal, Tag und die Streamerkarten zählen jetzt nur das Fallen in gewonnenen Kämpfen, die Spalte "bei Niederlage" entfällt.

## 0.10.1 (03.10.2026)

**Behoben**
- Gilden: Die Vergleichsseite sortiert jetzt nach der durchschnittlichen Kampfkraft (vorher nach der Summe, deshalb stand die größte Gilde oben). Die Kacheln nennen den Streamer-Namen statt des langen Gildennamens, Gilden mit weniger als 10 aktiven Mitgliedern gewinnen keine Kachel mehr.

**Verbessert**
- Regeln: nach Themen gruppiert, mit einem Satz zur Bedeutung jeder Regel.
- Startseite: Kennzahlen, Top 5, Aufsteiger der letzten 24 Stunden, Gildenüberblick und "Zuletzt" statt der Kampfliste (die gibt es weiter unter Kämpfe, "Letzte").

## 0.10.0 (03.10.2026)

**Neu**
- Gilden: neue Seite "Vergleich" mit allen Gilden nebeneinander (Mitglieder, Kampfkraft, Zuwachs in 24 Stunden und 7 Tagen, auch je Mitglied, Kasse, Spenden, Bosse).
- Spiel: neuer Bereich mit "Wirtschaft" (Silber in den Gildenkassen und bei den Top 100 im Verlauf), "Regeln" (die aktuellen Regeln des Spiels) und "Änderungen" (jede Regeländerung mit Zeitpunkt, Vorher und Nachher). Der Markt fehlt, er ist ohne Anmeldung nicht lesbar.
- Startseite: Die Streamerkarten zeigen den Chat-Modus (normal, langsam, still), den Live-Anteil und die Kämpfe des Kanals.
- Spielerseiten: Knopf "Teilen" kopiert eine Kurzfassung mit Link, dazu der Vergleich "Stärker als x % der erfassten Spieler".

## 0.9.0 (02.10.2026)

**Neu**
- Kampf-Statistik mit drei neuen Seiten unter Kämpfe. "Überleben": wie viele Teilnehmer fallen (insgesamt, bei Siegen und Niederlagen, je Rolle, Kampfart und Kampf), dazu Schaden, Heilung, Runden und das Restleben des Bosses nach Niederlagen. "Kampfkraft": die durchschnittliche Kampfkraft der Teilnehmer gegen die Empfehlung des Spiels, mit Siegquote je Abstand. "Wann und wo": Kämpfe und Siegquote je Uhrzeit, Kanal und Tag.
- Die Einzelheiten kommen aus den Kampfberichten des Spiels (eine zusätzliche Anfrage je neuem Kampf, etwa 100 am Tag) und dem laufenden Kampf (eine pro Lauf); gespeichert werden nur Summen je Kampf. Sie gibt es erst ab dem ersten Lauf nach dieser Version, die Seiten nennen den Beginn.

## 0.8.8 (02.10.2026)

**Neu**
- Links ins Spiel: Der Kampfname in den Listen der letzten Kämpfe führt zum Kampfbericht, die Spieler- und Gildenseiten haben "Im Spiel", die Kampfseiten verlinken die Kämpfe des Spiels, und der Seitenfuß führt zu Kämpfen, Bestenliste, Gilden, Markt und Kanälen.

**Verbessert**
- Kämpfe: Die Kampfseiten und der Seitenfuß zeigen, seit wann die Daten erfasst werden ("Erfasst wird seit 30.09.2026, 17:48 Uhr, frühere Kämpfe fehlen"), denn die Siegquoten gelten nur für diese Zeit.

## 0.8.7 (02.10.2026)

**Verbessert**
- Kämpfe: Die Kampfarten sind nach Siegquote sortiert, bei gleicher Quote nach der Zahl der Kämpfe, nicht mehr alphabetisch.

## 0.8.6 (02.10.2026)

**Verbessert**
- Bonus-Formel: neue Messung an 220 statt 14 Ausrüstungszuständen (Kampfkraft etwa 2,7 x ATK + 0,8 x DEF + 2,3 x SUP - 20, Abweichung um 15), dazu die genaue Formel der Schadensminderung. Die Gewichte von vorher (0,9 DEF, 1,6 SUP) stimmten nicht mehr.

## 0.8.5 (01.10.2026)

**Behoben**
- Die Seite zeigte nur "Keine Daten": die Zeile mit den täglichen Anfragen im Fuß (0.8.4) überdeckte die Funktion zum Laden der Daten. Behoben.

## 0.8.4 (01.10.2026)

**Neu**
- Der Fuß der Seite nennt, wie viele Anfragen die Seite täglich an das Spiel schickt (Anfragen des letzten Laufs mal 68 Läufe am Tag). Der Sammler hält die Zahl pro Lauf fest; sie erscheint nach dem nächsten Lauf.

**Behoben**
- Ein Tippfehler in der Menüliste der Kämpfe (beim Entfernen der Händlerseite) ließ das Skript der Seite nicht laufen; behoben, ein Test prüft das Skript jetzt auf Syntaxfehler.

## 0.8.3 (01.10.2026)

**Oberfläche**
- Die Unterseite "Fahrender Händler" ist weg (bei einem Abruf alle 15 Minuten kaum aussagekräftig); der Sammler fragt den Händler auch nicht mehr ab.

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
