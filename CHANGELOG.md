# Changelog

Versionen nach [SemVer](https://semver.org/lang/de/). Solange die Version mit 0 beginnt, ist das Projekt noch in Entwicklung.

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
