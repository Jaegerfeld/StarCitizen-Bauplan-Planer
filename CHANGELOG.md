# Changelog

Alle nennenswerten Änderungen an diesem Projekt. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.0.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [1.1.0] – 2026-09-27

### Geändert
- **Katalog (rechte Spalte) als Kachel-/Karten-Raster** statt Zeilenliste — Optik wie der Wikelo-Planer: responsives Grid (auto-fill), jede Karte mit Name + Unterklassen-Badge, Rezept-Chips, Quelle und „+"-Button unten; farbiger linker Akzent (Auswahl = Teal, erworben = Grün).

## [1.0.0] – 2026-09-27

### Hinzugefügt
- Erste Version des **SC Bauplan-Planers** (Standalone-HTML, offline lauffähig).
- Katalog aller craftbaren Baupläne von [star-head.de](https://star-head.de) (~1585) mit Rezept (Material × Menge, Mindestqualität) und Quell-Kontrakt.
- **Layout wie der Wikelo-Planer:** links die verfügbaren Ressourcen eingeben, rechts die Baupläne auswählen.
- **Zweistufiger Kategoriefilter:** Klasse (Rüstung, Helme, FPS-Waffen, Schiffswaffen, Schiffskomponenten, Werkzeuge …) → abhängige Unterklasse (Leichte/Schwere Rüstung, Pistole, Gewehr …).
- Filter „nur erworben / nur nicht erworben" nach Import der eigenen Baupläne.
- **Beschaffungsliste:** Materialbedarf über die Auswahl summiert, mit Bestandsabzug („noch benötigt"); Export als Text/CSV, Zustand als JSON.
- **SCDL-Import:** erworbene Baupläne aus dem SC-Deutsch-Launcher (`sc_bp_erledigt.json`) einlesen und markieren.
- Zweisprachig (DE/EN), Hell/Dunkel, In-App-Refresh (Baupläne live neu laden), localStorage-Persistenz.

[1.1.0]: https://github.com/Jaegerfeld/StarCitizen-Bauplan-Planer/releases/tag/v1.1.0
[1.0.0]: https://github.com/Jaegerfeld/StarCitizen-Bauplan-Planer/releases/tag/v1.0.0
