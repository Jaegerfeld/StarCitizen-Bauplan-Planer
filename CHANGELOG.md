# Changelog

Alle nennenswerten Änderungen an diesem Projekt. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.0.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [1.7.0] – 2026-11-01

### Hinzugefügt
- **„Was ist neu?“** in der Kopfzeile: zeigt dieses Changelog in einem Dialog, mit der aktuellen Version im Titel und einem Link auf die Datei auf GitHub. Der Text wird beim Bauen aus `CHANGELOG.md` übernommen und funktioniert auch in der Offline-Kopie. Schließen per Esc, Klick daneben oder ✕.

### Geändert
- **Einheitliche Kopfzeile** in allen vier SC-Tools (Bauplan-, Wikelo-, Handels-Planer, Screenshot-Auswerter): Kicker, Titel mit Version, Einzeiler, Aktionszeile (Sprache DE | EN mit sichtbarer aktiver Sprache, Hell/Dunkel, „Was ist neu?“, Tool-Aktionen, „Neuesten Stand laden“), eigene Zeile „Weitere Tools“ mit denselben Zielen in derselben Reihenfolge, Datenzeile. Quelle ist `kopfzeile.py`, in allen vier Repos identisch.
- Die Version steht jetzt am Titel; die Kopfzeile hat einen Einzeiler wie die anderen Tools.

## [1.6.0] – 2026-11-01

### Geändert
- **Mehrfachauswahl in den Filtern** Kategorie, Unterkategorie, Größe, Grade und Klasse: Jedes Feld klappt eine Häkchen-Liste auf, z. B. „Rüstung + Helme“ oder „S1–S3“. Ohne Haken gilt „alle“. Das Feld nennt die Auswahl („Rüstung, Helme“, ab drei Einträgen „S1 +2“) und bekommt einen farbigen Rand. Unterkategorien sind nach Kategorie gruppiert und folgen der Kategorieauswahl; wird eine Kategorie abgewählt, fallen ihre Unterkategorien aus der Auswahl. „Auswahl löschen“ oben in jeder Liste, Schließen per Klick daneben oder Esc.
- „alle / nur erworben“ und die Sortierung bleiben Einfachauswahl.

## [1.5.0] – 2026-11-01

### Hinzugefügt
- **Bilder in den Kacheln:** Jede Kachel zeigt ein kleines Bild des Gegenstands (72 × 72 px). Quelle ist das Vorschaubild aus dem **Star Citizen Wiki**, zugeordnet über die Spiel-Kennung (`gameId`) aus star-head; die Bilder werden nur verlinkt, nicht ins Repo kopiert. Stand des ersten Laufs: 1.312 von 1.585 Bauplänen mit Bild. Rüstungsteile (Core/Arms/Legs) zeigen meist das Bild des ganzen Sets.
- **Eigene Bilder** im Ordner `bilder/` (`<gameId>.webp`) haben Vorrang vor dem Wiki; Format und Nachweis in `bilder/LIESMICH.md`. Der Build schreibt die Arbeitsliste `bilder_fehlend.csv` mit allen Bauplänen ohne Bild.
- Bilder laden erst beim Hineinscrollen; lädt ein Bild nicht (z. B. offline), bleibt die Kachel ohne Bildrahmen. Quellenvermerk im Tooltip und in der Fußzeile.

### Geändert
- Der Build merkt sich die Wiki-Zuordnung in `data.json` (`imgCache`) und fragt danach nur neue Gegenstände ab; ohne Bild wird nach 7 Tagen erneut geschaut, Treffer werden nach 30 Tagen aufgefrischt (höchstens 150 pro Lauf).

## [1.4.0] – 2026-11-01

### Hinzugefügt
- **Schalter „nur ausgewählte“** in der Filterleiste: beschränkt den Katalog auf die gewählten Baupläne, mit Anzahl im Schalter. Die übrigen Filter (Suche, Kategorie, Größe …) gelten weiter; blenden sie gewählte Baupläne aus, sagt der Katalog das und bietet „Filter zurücksetzen“ an. Ohne Auswahl ist der Schalter gesperrt; wird die letzte Auswahl entfernt, schaltet er sich aus. Der Zustand bleibt im Browser gespeichert.

## [1.3.1] – 2026-10-25

### Hinzugefügt
- Kopfzeile: Links zum **Handels-Planer** und zur **Guides-Übersicht** (jaegerfeld.github.io/sc-guides), damit man von jedem Planer zurück zur Übersichtsseite kommt.

## [1.3.0] – 2026-10-25

### Geändert
- **Aktualisierung läuft über GitHub:** Die Online-Version wird täglich (05:00 UTC) per GitHub Actions neu gebaut; dabei entsteht neben der HTML eine `data.json` mit demselben Datenstand.
- **Knopf „Aktualisieren“ → „Neuesten Stand laden (GitHub)“:** lädt die `data.json` des letzten Builds von GitHub Pages statt `api.star-head.de/blueprint` direkt aus dem Browser. Das schont die Community-API (eine Abfrage pro Tag statt eine pro Klick). Funktioniert auch aus der Offline-Kopie. Meldet, wenn der Stand schon aktuell ist.
- Filter „alle Erworben“ heißt jetzt „alle“ (DE) bzw. „all“ (EN) – er meint alle Baupläne, ob erworben oder nicht.

## [1.2.0] – 2026-09-27

### Hinzugefügt
- **Klassifizierung von Komponenten/Waffen** (Größe · Grade · Klasse, z. B. „S1 · A · Civilian") aus der star-head-Beschreibung — auf jeder Kachel angezeigt und über drei neue **Filter** (Größe, Grade, Klasse) filterbar.
- **Wechsel-Button** in der Kopfzeile zum [Wikelo-Ressourcen-Planer](https://jaegerfeld.github.io/StarCitizen-Wikelo-Planer/) (und umgekehrt).

### Geändert
- **Beschaffungsliste** steht jetzt **über** den verfügbaren Ressourcen und ist scrollbar (max. ~⅓ Bildschirmhöhe) — man braucht die Liste öfter als die Bestandseingabe.
- **Speichern/Laden** (Zustand) in die zentrale Kopfzeile neben „Aktualisieren" verschoben und klar benannt.
- Kategorie-Filter umbenannt zu „Kategorie/Unterkategorie" (macht „Klasse" für die Komponenten-Klasse frei).

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
