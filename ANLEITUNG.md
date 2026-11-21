# SC Bauplan-Planer – Anleitung

## Kurzanleitung

Der Bauplan-Planer zeigt alle craftbaren Baupläne aus Star Citizen mit Rezept und Quelle. Du wählst Baupläne aus und bekommst eine Beschaffungsliste mit dem summierten Materialbedarf.

### Bereiche

- **Kopfzeile:** Sprache **DE | EN**, **Hell / Dunkel**, **Was ist neu?** (Changelog), **Erworbene (SCDL)** und **Neuesten Stand laden (GitHub)**.
- **Katalog** (rechts): eine Kachel je Bauplan mit Bild, Unterkategorie, Größe · Grade · Klasse, Rezept-Chips (Menge × Material, **Q≥** = Mindestqualität) und Quelle (bis zu drei Kontrakte mit Drop-Chance).
- **Filterleiste:** Suchfeld (Name, Material, Kategorie, Größe wie `s2`), dazu **alle Kategorien**, **alle Unterkategorien**, **alle Größen**, **alle Grade**, **alle Klassen**. Jedes Feld klappt eine Häkchen-Liste auf, mehrere Werte sind möglich. Ohne Haken gilt „alle“.
- **alle / nur erworben / nur nicht erworben:** wirkt erst nach einem SCDL-Import oder dem Laden eines Zustands mit erworbenen Bauplänen.
- **Name A–Z / wenigste Materialien:** Sortierung des Katalogs.
- **nur ausgewählte:** zeigt nur deine gewählten Baupläne. Die anderen Filter gelten weiter.
- **Auswahlleiste** (über dem Katalog): deine gewählten Baupläne mit **−**, **+** und **✕**.
- **Beschaffungsliste** (links oben): Material und **benötigt**. Hast du Bestand eingetragen, kommt die Spalte **noch** dazu.
- **Verfügbare Ressourcen** (links unten): trage hier ein, was du schon hast. **alle 0** setzt alles zurück.

### Häufige Aktionen

- Bauplan wählen: Anzahl im Feld unten auf der Kachel eintragen, dann **+** klicken.
- Liste weitergeben: **📋 Kopieren**, **⬇ .txt** oder **⬇ .csv**.
- Auswahl und Bestand sichern: unter **Auswahl & Bestand** auf **💾 Speichern** (JSON-Datei), später mit **📂 Laden** zurückholen.
- Mehr Treffer: unten im Katalog auf **… N weitere anzeigen** klicken.

### Daten und Speicherung

- Rezepte und Quellen kommen von [star-head.de](https://star-head.de), die Kategorien aus der Item-Typ-Tabelle des SC-Deutsch-Launchers. Die Angaben sind patch-abhängig, prüfe sie im Spiel nach.
- Bilder kommen aus dem [Star Citizen Wiki](https://starcitizen.tools/) und werden beim Ansehen von dort geladen. Ohne Internet bleiben die Kacheln ohne Bild.
- Die Seite läuft auch als Offline-Kopie (`SC_Bauplan_Planer.html`), die Daten sind eingebacken.
- **Neuesten Stand laden (GitHub)** holt den täglich gebauten Datenstand. Ist er schon aktuell, sagt die Seite das.
- Auswahl, Bestand, erworbene Baupläne, Sprache, Hell/Dunkel und der Schalter **nur ausgewählte** bleiben nur in deinem Browser (localStorage). Suche und Filter werden nicht gespeichert.

## Tutorial: Materialbedarf planen

Ziel: Du willst zwei Rüstungsteile bauen und wissen, welche Materialien dir noch fehlen.

1. Öffne den Planer. Am Handy tippst du oben auf den Reiter **Katalog**.
2. Klicke auf **alle Kategorien** und setze den Haken bei **Rüstung**. Klicke daneben, um die Liste zu schließen.
3. Grenze bei Bedarf mit **alle Unterkategorien** weiter ein, zum Beispiel auf **Leichte Rüstung**.
4. Tippe den Namen des Teils ins Suchfeld. Die Trefferzahl steht rechts in der Filterleiste.
5. Trage auf der Kachel unten die Anzahl ein (Standard ist 1) und klicke **+**. Der Bauplan erscheint in der Auswahlleiste über dem Katalog.
6. Wiederhole das für das zweite Teil. Mit **−** und **+** in der Auswahlleiste änderst du die Anzahl, mit **✕** entfernst du einen Bauplan.
7. Sieh dir links die **Beschaffungsliste** an. Sie summiert Material und **benötigt** über alle gewählten Baupläne. Gleiches Material mit unterschiedlicher Mindestqualität steht in eigenen Zeilen.
8. Trage unter **Verfügbare Ressourcen** ein, was du schon hast. Materialien, die deine Auswahl braucht, sind dort farbig hervorgehoben.
9. Jetzt zeigt die Beschaffungsliste die Spalte **noch**. Ein **✓** heißt: dein Bestand reicht.
10. Klicke **📋 Kopieren**, um die Liste in die Zwischenablage zu legen, oder lade sie mit **⬇ .txt** oder **⬇ .csv** herunter.

### Tipps

- Mit **nur ausgewählte** siehst du im Katalog nur deine Auswahl. Blenden andere Filter gewählte Baupläne aus, bietet der Katalog **Filter zurücksetzen** an.
- Materialien sind raffinierte Rohstoffe. Du kaufst sie an Raffinerien oder im TDD oder raffinierst sie selbst.
- Die .csv-Datei hat die Spalten Material, MinQuality, Need, Stock und Left.

## Tutorial: Erworbene abgleichen

Ziel: Du willst sehen, welche Baupläne dir noch fehlen, und deinen Stand auf einem anderen Gerät weiterführen.

1. Exportiere im SC-Deutsch-Launcher deine erledigten Baupläne als `sc_bp_erledigt.json`.
2. Klicke in der Kopfzeile auf **📥 Erworbene (SCDL)** und wähle die Datei aus.
3. Unten erscheint kurz eine Meldung, wie viele erworbene Baupläne erkannt wurden und wie viele nicht im Katalog stehen.
4. Erworbene Baupläne tragen jetzt das Abzeichen **✓ erworben** und einen grünen Rand links.
5. Das Feld **alle** in der Filterleiste ist jetzt aktiv. Wähle **nur nicht erworben**. Am Handy findest du es unter **Weitere Filter**.
6. Kombiniere das mit Kategorie, Größe oder Grade, um gezielt nach fehlenden Bauplänen zu suchen. Die Quellenzeile der Kachel nennt die Kontrakte, die den Bauplan droppen.
7. Klicke unter **Auswahl & Bestand** auf **💾 Speichern**. Du bekommst die Datei `SC_Bauplan_Zustand.json` mit Auswahl, Bestand und erworbenen Bauplänen.
8. Öffne den Planer auf dem anderen Gerät oder in einem anderen Browser und klicke **📂 Laden**. Wähle die gespeicherte Datei.
9. Auswahl, Bestand und erworbene Baupläne sind wieder da.

### Tipps

- Baupläne, die jeder von Anfang an hat, zählen immer als erworben.
- Ein neuer SCDL-Import ersetzt die bisherige Liste der erworbenen Baupläne.
- **📂 Laden** ersetzt deine aktuelle Auswahl und deinen Bestand durch den Inhalt der Datei.
- Ist ein gewählter Bauplan nach einer Datenaktualisierung nicht mehr im Katalog, ist er in der Auswahlleiste durchgestrichen und zählt nicht in der Summe.

## Fragen

### Warum sind manche Kacheln ohne Bild?

Nicht jeder Gegenstand hat ein Bild im Wiki. Offline werden gar keine Bilder geladen.

### Warum ist das Feld „alle“ (erworben) grau?

Es wird erst aktiv, wenn du über **📥 Erworbene (SCDL)** importiert oder einen Zustand mit erworbenen Bauplänen geladen hast.

### Warum ist **nur ausgewählte** gesperrt?

Du hast noch keinen Bauplan gewählt. Wird die letzte Auswahl entfernt, schaltet sich der Schalter selbst aus.

### Stimmen die Rezepte?

Die Daten kommen von star-head.de und hängen vom Patch ab. Prüfe Mengen und Quellen im Spiel nach.

### Geht meine Auswahl verloren, wenn ich den Browser-Speicher lösche?

Ja. Sichere sie vorher mit **💾 Speichern** als Datei.
