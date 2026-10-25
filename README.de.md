# StarCitizen Bauplan-Planer

Ein Standalone-HTML-Tool (offline lauffähig), das **alle craftbaren Star-Citizen-Baupläne** auflistet, den Materialbedarf jedes Bauplans zeigt und aus deiner Auswahl eine exportierbare **Beschaffungsliste** baut — Layout und Bedienung wie beim [StarCitizen Wikelo-Planer](https://github.com/Jaegerfeld/StarCitizen-Wikelo-Planer).

**🌐 Online-Version:** https://jaegerfeld.github.io/StarCitizen-Bauplan-Planer/

## Funktionen

- **Kompletter Katalog** aller craftbaren Baupläne von [star-head.de](https://star-head.de) (~1585), je mit Rezept (Material × Menge, Mindestqualität) und dem Kontrakt, der ihn droppt.
- **Layout wie der Wikelo-Planer:** links die **verfügbaren Ressourcen** eingeben, rechts die **Baupläne auswählen**.
- **Zweistufiger Kategoriefilter:** Klasse (Rüstung, Helme, FPS-Waffen, Schiffswaffen, Schiffskomponenten, Werkzeuge …) → abhängige Unterklasse (Leichte/Schwere Rüstung, Pistole, Gewehr …).
- **Erworben-Filter:** nach dem Import der eigenen Liste nur erworbene / nicht erworbene Baupläne zeigen.
- **Beschaffungsliste:** Materialbedarf über die Auswahl summiert, abzüglich Bestand („noch benötigt"); Export als Text/CSV, Zustand als JSON.
- **SCDL-Import (Zugabe):** erworbene Baupläne aus dem [SC-Deutsch-Launcher](https://sc-deutsch.de) (`sc_bp_erledigt.json`) einlesen und markieren.
- Zweisprachig (DE/EN), Hell/Dunkel, localStorage-Persistenz.
- **Täglich frische Daten:** die Online-Version wird jeden Tag neu gebaut (GitHub Actions, 05:00 UTC). Der Knopf „Neuesten Stand laden (GitHub)“ in der App holt die `data.json` dieses Builds von GitHub Pages – auch aus einer Offline-Kopie heraus – statt star-head direkt abzufragen.

## Nutzung

- **Einfach benutzen:** die Online-Version oben öffnen oder `SC_Bauplan_Planer.html` doppelklicken (läuft komplett offline).
- **Mit frischen Daten neu bauen:** `Bauplan_Planer_aktualisieren.bat` (Windows) / `.sh` (Linux) / `.command` (macOS) starten, oder:
  ```
  python bauplan_planer_bauen.py
  ```
  Das zieht die Baupläne von star-head.de und backt sie in `SC_Bauplan_Planer.html`. Es wird nur die Python-Standardbibliothek benötigt.

## Wie es funktioniert

`bauplan_planer_bauen.py` lädt `https://api.star-head.de/blueprint`, ordnet jedes Item über `bp_item_types_v3.json` (Item-Typ-Tabelle des SC-Deutsch-Launchers, mitgeliefert, damit die Kategorien auch ohne Launcher stimmen) einer Klasse/Unterklasse zu und backt alles als JSON in eine einzige HTML-Datei. Die gesamte UI-Logik liegt in dieser HTML.

## Daten & Credits

- Baupläne / Rezepte: **star-head.de**
- Item-Typ-Tabelle: **SC-Deutsch-Launcher**
- Import-Format der erworbenen Baupläne: SC-Deutsch-Launcher `sc_bp_erledigt.json`

Rezepte und Preise sind patch-abhängig. Inoffizielles Fan-Tool, nicht mit Cloud Imperium Games verbunden. Star Citizen® ist eine Marke von CIG.

## Lizenz

BSD-3-Clause — siehe [LICENSE](LICENSE).
