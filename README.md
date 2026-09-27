# StarCitizen Bauplan-Planer (Blueprint Planner)

A single-file, offline HTML tool that lists **every craftable Star Citizen blueprint**, shows the materials each one needs, and builds an exportable **procurement list** from your selection — layout and workflow mirror the [StarCitizen Wikelo-Planer](https://github.com/Jaegerfeld/StarCitizen-Wikelo-Planer).

**🌐 Online version:** https://jaegerfeld.github.io/StarCitizen-Bauplan-Planer/
*(German README: [README.de.md](README.de.md))*

## Features

- **Full catalog** of all craftable blueprints from [star-head.de](https://star-head.de) (~1585), each with its recipe (material × quantity, minimum quality) and the contract that drops it.
- **Wikelo-style layout:** enter the resources you already have on the **left**, pick blueprints on the **right**.
- **Two-level category filter:** class (Armor, Helmets, FPS weapons, Ship weapons, Ship components, Tools …) → dependent subclass (Light/Heavy Armor, Pistol, Rifle …). *(Category labels are in German even in EN mode; blueprint and material names come from star-head in English.)*
- **Owned filter:** show only owned / not-owned blueprints after importing your own list.
- **Procurement list:** material needs summed across your selection, minus your stock ("still needed"); export as text/CSV, save state as JSON.
- **SCDL import (bonus):** load your owned blueprints from the [SC-Deutsch-Launcher](https://sc-deutsch.de) export (`sc_bp_erledigt.json`) to mark what you already have.
- Bilingual (DE/EN), light/dark, in-app live refresh, localStorage persistence.

## Usage

- **Just use it:** open the online version above, or double-click `SC_Bauplan_Planer.html` (works fully offline).
- **Rebuild with fresh data:** run `Bauplan_Planer_aktualisieren.bat` (Windows) / `.sh` (Linux) / `.command` (macOS), or:
  ```
  python bauplan_planer_bauen.py
  ```
  This fetches the blueprints from star-head.de and bakes them into `SC_Bauplan_Planer.html`. Only the Python standard library is required.

## How it works

`bauplan_planer_bauen.py` pulls `https://api.star-head.de/blueprint`, maps each item to a class/subclass via `bp_item_types_v3.json` (an item-type table from the SC-Deutsch-Launcher, included so categories work without the launcher installed), and bakes everything as JSON into a self-contained HTML file. All UI logic lives in that HTML.

## Data & credits

- Blueprints / recipes: **star-head.de**
- Item-type table: **SC-Deutsch-Launcher**
- Owned-blueprint import format: SC-Deutsch-Launcher `sc_bp_erledigt.json`

Recipes and prices are patch-dependent. Unofficial fan tool, not affiliated with Cloud Imperium Games. Star Citizen® is a trademark of CIG.

## License

BSD-3-Clause — see [LICENSE](LICENSE).
