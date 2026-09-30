# Changelog

Versionen nach [SemVer](https://semver.org/lang/de/). Solange die Version mit 0 beginnt, ist das Projekt noch in Entwicklung.

## 0.3.1 (30.09.2026)

**Oberfläche**
- Spielerseite aufgeräumt: die Kämpfe zeigen nur noch die eigene Siegquote (ohne Vergleich mit allen Kämpfen, der wegen unterschiedlicher Zeiträume und der Auswahl der Spieler wenig aussagte). Die Diagramme Gildenspende und Markt entfallen; Spendenrang und Markt-Summen stehen weiter als Text.

## 0.3.0 (30.09.2026)

**Neu**
- Spielerseite (Beobachtungsliste): Ausrüstung je Platz mit dem schwächsten Stück, Kampfquoten je Art im Vergleich zu allen Kämpfen, Silber über die Zeit und Markt (Einnahmen minus Ausgaben).

**Geändert**
- Die Quests eines Spielers werden nicht mehr gespeichert und nicht mehr angezeigt (Zeit, Kanal und Text je Quest). Die Gesamtzahlen (geschafft, gescheitert) und die Quest-Rangliste bleiben.
- README: Wünsche und Fehler als Issue melden.

## 0.2.0 (30.09.2026)

**Neu**
- Ranglisten nach Silber und Errungenschaften (zusätzlich zu Ausrüstung und Quests), also alle vier des Spiels. Der Sammler macht dafür 2 Anfragen mehr pro Lauf (jetzt etwa 12).

**Oberfläche**
- Jeder Bereich hat eine zweite Tab-Zeile mit Unterseiten: Ranglisten (Ausrüstung, Silber, Errungenschaften, Quests, Aufsteiger), Gilden (eine Seite pro Gilde), Kämpfe (Kampfarten, letzte Kämpfe, fahrender Händler). Die Gilden-Tabs tragen den Namen des Streamers, der volle Gildenname steht als Überschrift. Die Seiten sind kürzer, die Adressen (`#/gilden/karni`) lassen sich teilen.

## 0.1.1 (30.09.2026)

**Oberfläche**
- Hinweis im Fuß der Seite: fast komplett vibe-coded, Zahlen sind Schätzungen.

**Verbessert**
- Dokumentation: kurze README mit Badges, Details zu Ablauf und Berechnung in `docs/funktionsweise.md`.
- Tests für Sammler, Bau und Beobachtungsliste (Abdeckung von 76 % auf 99 %), CI mit denselben Hooks wie lokal, Abdeckungs-Badge, Dependabot.

## 0.1.0 (30.09.2026)

**Neu**
- Sammler als GitHub Action: alle 15 Minuten von 7 bis 24 Uhr, etwa 10 Anfragen, gespeichert werden nur Änderungen.
- Dashboard auf GitHub Pages: Ranglisten mit Trends, Aufsteiger, Spielerseite mit Tempo, Prognose, Vergleich mit ähnlichen Spielern und Gildenstand, Gilden, Kämpfe und fahrender Händler.
- Beobachtungsliste über ein Issue-Formular: Kampfquoten, Markt, Verlosungen und Quests für eingetragene Spieler.
