# Eigene Bilder für die Bauplan-Kacheln

Bilder in diesem Ordner haben Vorrang vor den Vorschaubildern aus dem Star Citizen Wiki. Der Build ordnet sie über den Dateinamen zu; der Pages-Workflow veröffentlicht den Ordner mit.

## Format

| Punkt | Vorgabe |
|---|---|
| Aufnahme | Im Spiel mit **Druck** (englischer Client: **Print**), Gegenstand möglichst frontal und formatfüllend |
| Zuschnitt | quadratisch, nur der Gegenstand, ruhiger Hintergrund |
| Größe | **256 × 256 px** (die Kachel zeigt 72 × 72 px, 256 reicht auch für hochauflösende Bildschirme) |
| Dateiformat | **WebP** (bevorzugt) oder PNG, unter 50 KB |
| Dateiname | **`<gameId>.webp`**, z. B. `6534d6d3-85dc-4c29-aa3d-80cab37c4fa5.webp` |

Die `gameId` ist die Spiel-Kennung des Gegenstands, wie star-head sie liefert. Sie übersteht Umbenennungen und ist derselbe Schlüssel, den das Wiki nutzt.

## Welche Bilder fehlen?

Beim Bauen (`python bauplan_planer_bauen.py`) entsteht neben dem Skript die Arbeitsliste **`bilder_fehlend.csv`** (`gameId;name;kategorie`, Semikolon, UTF-8). Sie nennt alle Baupläne, für die es weder ein eigenes noch ein Wiki-Bild gibt. Die Liste wird nicht ins Repo übernommen.

## Nachweis

Jede eigene Aufnahme bekommt eine Zeile in **`manifest.csv`**: `gameId;name;datei;datum;quelle` (quelle z. B. „eigene Aufnahme, Patch 4.10“). Spielinhalte bleiben © Cloud Imperium Games.
