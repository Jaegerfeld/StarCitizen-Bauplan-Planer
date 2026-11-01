#!/usr/bin/env python3
# =============================================================================
# Autor:          Robert Seebauer
# Repository:     https://github.com/Jaegerfeld/StarCitizen-Bauplan-Planer
# KI-Unterstützung: Erstellt mit Unterstützung von Claude (Anthropic)
# Erstellt:       27.09.2026
# Geändert:       01.11.2026
# Lizenz:         BSD-3-Clause (siehe LICENSE)
#
# Fachliche Funktion:
#   Generator des SC Bauplan-Planers. Lädt alle craftbaren Baupläne samt Rezepten
#   (Material, Menge, Mindestqualität) und Beschaffungsquellen (Kontrakte mit
#   Drop-Chance) von der star-head.de-API (https://api.star-head.de/blueprint) und
#   reduziert sie auf ein schlankes App-Schema. Kontraktnamen mit Platzhaltern oder
#   rohen Übersetzungs-Keys werden lesbar gemacht; Größe, Grad und Klasse kommen aus
#   der Item-Beschreibung.
#
#   Die Einordnung in eine zweistufige Kategorie (Klasse -> Unterklasse) läuft über
#   die Item-Typ-Tabelle des SC-Deutsch-Launchers (bp_item_types_v3.json, zuerst aus
#   %APPDATA%/sc-deutsch-launcher/blueprints/, sonst die Kopie im Repo) und die
#   Taxonomie TAXO; unbekannte Typen landen unter „Sonstiges“.
#
#   Kachel-Bilder: eigene Aufnahmen in bilder/<gameId>.webp|png|jpg haben Vorrang,
#   sonst Vorschaubilder aus der Star-Citizen-Wiki-API (starcitizen.tools vor
#   star-citizen.wiki), die nur verlinkt und nie ins Repo kopiert werden. Der
#   Bild-Cache führt die lokale und die veröffentlichte data.json zusammen (der
#   jüngere Eintrag gewinnt); ohne Bild wird nach 7 Tagen erneut gefragt, mit Bild
#   nach 30 Tagen aufgefrischt, höchstens 150 Auffrischungen je Lauf (schont die
#   Wiki-API).
#
#   Ergebnisse: SC_Bauplan_Planer.html (eine offline lauffähige Seite mit
#   eingebackenen Daten, gameId weggelassen, Wiki-Thumbs gekürzt), data.json
#   (derselbe Stand plus Bild-Cache; der tägliche GitHub-Build veröffentlicht sie auf
#   GitHub Pages, der Knopf „Neuesten Stand laden“ in der App holt sie von dort statt
#   direkt von star-head) und bilder_fehlend.csv (Arbeitsliste der Baupläne ohne
#   Bild). Kopfzeile, „Was ist neu?“-Dialog und Design kommen aus kopfzeile.py und
#   sc_design.py, der Changelog aus CHANGELOG.md.
#
#   Aufruf (überall lauffähig, Pfade relativ zum Skript):
#       python bauplan_planer_bauen.py
# =============================================================================
"""Build script for the SC Blueprint Planner: fetches data and writes the offline page."""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import kopfzeile as kz
import sc_design as sd
from version import VERSION

#: star-head.de endpoint that returns all blueprints with recipes and reward sources.
BLUEPRINT_URL = "https://api.star-head.de/blueprint"
#: Folder of this script; all inputs and outputs are resolved relative to it.
HERE = Path(__file__).parent
#: The generated offline page.
OUT_HTML = HERE / "SC_Bauplan_Planer.html"
#: The same data set as a separate file (plus image cache) for the in-app refresh.
OUT_JSON = HERE / "data.json"
#: Published data set (daily GitHub build); source for the refresh button in the app.
DATA_URL = "https://jaegerfeld.github.io/StarCitizen-Bauplan-Planer/data.json"

# Tile images: own captures take priority, otherwise a thumbnail from the Star Citizen Wiki.
# The images are only linked (hotlinked), never copied into the repo.
#: Own images: bilder/<gameId>.webp|png|jpg.
OWN_DIR = HERE / "bilder"
#: Star Citizen Wiki API v2 item endpoint (append the gameId).
WIKI_ITEM_URL = "https://api.star-citizen.wiki/api/v2/items/"
#: Accepted image sources in order of preference, mapped to their short code on the page.
WIKI_SOURCES = {"starcitizen.tools": "w", "star-citizen.wiki": "c"}
#: Width of the thumbnails in pixels.
THUMB_PX = 160
#: Days after which an item without a wiki image is looked up again.
IMG_MISS_DAYS = 7
#: Days after which a found wiki image is refreshed ...
IMG_HIT_DAYS = 30
#: ... but at most this many refreshes per run (spares the wiki API).
IMG_REFRESH_MAX = 150
#: Size segment of a MediaWiki thumbnail path (e.g. "/320px-").
_THUMB_RE = re.compile(r"/(\d+)px-")
#: Original file URL on starcitizen.tools: host, hash dirs a and ab, file name.
_MEDIA_RE = re.compile(r"^(https://media\.starcitizen\.tools)/([0-9a-f])/([0-9a-f]{2})/([^/?]+)")

_appdata = os.environ.get("APPDATA", "")
#: Where to look for the SCDL item-type table: launcher folder first, then the repo copy.
ITMAP_CANDIDATES = [
    Path(_appdata) / "sc-deutsch-launcher" / "blueprints" / "bp_item_types_v3.json"
    if _appdata else None,
    HERE / "bp_item_types_v3.json",
]

#: Two-level taxonomy: fine star-head/SCDL item type -> (class, subclass), German labels.
TAXO = {
    "Light Armor": ("Rüstung", "Leichte Rüstung"),
    "Medium Armor": ("Rüstung", "Mittlere Rüstung"),
    "Heavy Armor": ("Rüstung", "Schwere Rüstung"),
    "Core Armor": ("Rüstung", "Rüstungskern"),
    "Undersuit": ("Rüstung", "Undersuit"),
    "Backpack": ("Rüstung", "Rucksack"),
    "Light Helmet": ("Helme", "Leichter Helm"),
    "Medium Helmet": ("Helme", "Mittlerer Helm"),
    "Heavy Helmet": ("Helme", "Schwerer Helm"),
    "Helmet": ("Helme", "Helm"),
    "Char_Clothing_Torso_0": ("Kleidung", "Oberkörper"),
    "Char_Clothing_Torso_1": ("Kleidung", "Oberkörper"),
    "Char_Clothing_Legs": ("Kleidung", "Beine"),
    "Char_Clothing_Feet": ("Kleidung", "Füße"),
    "FPS, Pistol": ("FPS-Waffen", "Pistole"),
    "FPS, Rifle": ("FPS-Waffen", "Gewehr"),
    "FPS, SMG": ("FPS-Waffen", "SMG"),
    "FPS, Shotgun": ("FPS-Waffen", "Schrotflinte"),
    "FPS, Sniper": ("FPS-Waffen", "Scharfschützengewehr"),
    "FPS, LMG": ("FPS-Waffen", "LMG"),
    "FPS Weapon": ("FPS-Waffen", "Sonstige Waffe"),
    "Magazine": ("Magazine", "Magazin"),
    "Laser Cannon": ("Schiffswaffen", "Laser-Kanone"),
    "Laser Repeater": ("Schiffswaffen", "Laser-Repeater"),
    "Laser Gatling": ("Schiffswaffen", "Laser-Gatling"),
    "Ballistic Cannon": ("Schiffswaffen", "Ballistik-Kanone"),
    "Ballistic Gatling": ("Schiffswaffen", "Ballistik-Gatling"),
    "Ballistic Repeater": ("Schiffswaffen", "Ballistik-Repeater"),
    "Mass Driver": ("Schiffswaffen", "Mass Driver"),
    "Neutron Cannon": ("Schiffswaffen", "Neutronen-Kanone"),
    "Scatter Gun": ("Schiffswaffen", "Scattergun"),
    "Dist. Cannon": ("Schiffswaffen", "Distortion-Kanone"),
    "Dist. Repeater": ("Schiffswaffen", "Distortion-Repeater"),
    "Ship Weapon": ("Schiffswaffen", "Sonstige Waffe"),
    "Power Plant": ("Schiffskomponenten", "Kraftwerk"),
    "Cooler": ("Schiffskomponenten", "Kühler"),
    "Shield": ("Schiffskomponenten", "Schild"),
    "Radar": ("Schiffskomponenten", "Radar"),
    "Quantum Drive": ("Schiffskomponenten", "Quantum-Antrieb"),
    "Mining Laser": ("Werkzeuge", "Mining-Laser"),
    "Salvage Head": ("Werkzeuge", "Salvage-Kopf"),
    "Salvage Modifier": ("Werkzeuge", "Salvage-Modul"),
    "Tractor Beam": ("Werkzeuge", "Traktorstrahl"),
    "Fuel Nozzle": ("Werkzeuge", "Tankdüse"),
}
#: Order of the classes in the category filter.
CLASS_ORDER = [
    "Rüstung", "Helme", "Kleidung", "FPS-Waffen", "Magazine",
    "Schiffswaffen", "Schiffskomponenten", "Werkzeuge", "Sonstiges",
]

#: Game placeholder in contract names, e.g. "~mission(Location)".
_PLACEHOLDER = re.compile(r"~\w+\([^)]*\)")
#: Untranslated localisation key (lower case, digits and underscores only).
_RAWKEY = re.compile(r"^[a-z0-9_]+$")
#: Raw key of the Black Box Recovery contracts; the group is the faction/variant.
_BLACKBOX = re.compile(r"blackbox_recover_title_([a-z]+)_")


def get_json(url: str, timeout: int = 60):
    """
    Fetch and decode JSON from a URL.

    Sends a browser User-Agent header, because star-head sometimes blocks requests
    without one.

    Args:
        url:     Address to fetch.
        timeout: Socket timeout in seconds.

    Returns:
        The decoded JSON value.

    Raises:
        urllib.error.URLError: On network or HTTP errors.
        json.JSONDecodeError: If the response is not valid JSON.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed URL)
        return json.loads(r.read().decode("utf-8"))


def load_itmap() -> dict[str, str]:
    """
    Load the SCDL item-type table (item name -> fine item type).

    Tries the candidates in ITMAP_CANDIDATES in order; an unreadable file is
    reported and skipped.

    Returns:
        Mapping of lower-cased item names to their type, or an empty dict if no
        table was found (all blueprints then fall into class "Sonstiges").
    """
    for cand in ITMAP_CANDIDATES:
        if cand and cand.exists():
            try:
                raw = json.loads(cand.read_text(encoding="utf-8"))
                print(f"  Item-Typen aus {cand} ({len(raw)} Einträge).")
                return {str(k).strip().lower(): str(v) for k, v in raw.items()}
            except Exception as e:  # noqa: BLE001
                print(f"  Hinweis: {cand} nicht lesbar: {e}")
    print("  Hinweis: keine Item-Typ-Tabelle gefunden -> Klasse 'Sonstiges'.")
    return {}


def clean_source(name: str) -> str:
    """
    Make a contract name from star-head readable.

    Game placeholders such as ``~mission(...)`` become "(Ort)"; raw localisation
    keys (lower case and underscores only) are turned into title case, with the
    Black Box Recovery keys mapped to "Black Box Recovery (XYZ)".

    Args:
        name: Contract name as delivered by the API.

    Returns:
        The cleaned display name.
    """
    name = _PLACEHOLDER.sub("(Ort)", name).strip()
    if _RAWKEY.fullmatch(name):
        m = _BLACKBOX.match(name)
        if m:
            return f"Black Box Recovery ({m.group(1).upper()})"
        return name.replace("_", " ").title()
    return name


def categorize(fine_type: str) -> tuple[str, str]:
    """
    Map a fine item type to its (class, subclass) pair via TAXO.

    Args:
        fine_type: Item type from the SCDL table.

    Returns:
        (class, subclass); unknown types become ("Sonstiges", fine_type).
    """
    return TAXO.get(fine_type, ("Sonstiges", fine_type or "Sonstiges"))


def spec_fields(desc: str) -> dict:
    """
    Extract size, grade and class from an item description (e.g. 'S1 · A · Civilian').

    star-head delivers the description with literal '\\n' sequences and partly with
    non-breaking spaces; both are normalised before the three lines are read.

    Args:
        desc: Item description text.

    Returns:
        Dict with the keys ``sz`` (size without the leading "S"), ``gr`` and
        ``kl``; only fields that are present are included.
    """
    text = (desc or "").replace("\\n", "\n").replace("\xa0", " ")
    out = {}
    for key, short in (("Size", "sz"), ("Grade", "gr"), ("Class", "kl")):
        m = re.search(r"(?mi)^" + key + r":\s*(.+?)\s*$", text)
        if m:
            val = m.group(1).strip()
            if short == "sz":
                val = val.lstrip("Ss").strip()  # 'S0' -> '0'
            if val:
                out[short] = val
    return out


def thumb_url(url: str) -> str:
    """
    Turn a wiki image URL into a small thumbnail URL (THUMB_PX wide).

    For starcitizen.tools an existing thumbnail path is resized to THUMB_PX, or a
    MediaWiki thumbnail path is built from the original file URL. URLs from other
    sources are returned unchanged.

    Args:
        url: Image URL from the wiki API.

    Returns:
        The thumbnail URL.
    """
    if "/thumb/" in url and _THUMB_RE.search(url):
        return _THUMB_RE.sub(f"/{THUMB_PX}px-", url, count=1)
    m = _MEDIA_RE.match(url)
    if m:
        host, a, ab, fn = m.groups()
        tail = ".webp" if not fn.lower().endswith(".webp") else ""
        return f"{host}/thumb/{a}/{ab}/{fn}/{THUMB_PX}px-{fn}{tail}"
    return url


def wiki_image(gid: str) -> tuple[str, str]:
    """
    Look up the thumbnail of one item in the Star Citizen Wiki API.

    Args:
        gid: The item's gameId.

    Returns:
        (thumbnail URL, source code from WIKI_SOURCES), or ("", "") if the item
        has no image from an accepted source or the lookup fails.
    """
    try:
        d = get_json(WIKI_ITEM_URL + gid, timeout=30).get("data") or {}
    except Exception:  # noqa: BLE001 (404 = item missing from the wiki)
        return "", ""
    imgs = d.get("images") or []
    for wanted in WIKI_SOURCES:               # starcitizen.tools first
        for im in imgs:
            if im.get("source") == wanted and im.get("thumbnail_url"):
                return thumb_url(im["thumbnail_url"]), WIKI_SOURCES[wanted]
    return "", ""


def load_img_cache() -> dict[str, list]:
    """
    Merge the image cache from the local and the published data.json.

    For each gameId the younger entry wins. This way the daily build only asks
    the wiki about new or due items. Unreadable or unreachable sources are skipped.

    Returns:
        Cache mapping ``{gameId: [url, source, ISO date of the check]}``; the URL
        is empty if the wiki had no image.
    """
    cache: dict[str, list] = {}
    sources = []
    if OUT_JSON.exists():
        try:
            sources.append(json.loads(OUT_JSON.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    try:
        sources.append(get_json(DATA_URL, timeout=30))
    except Exception:  # noqa: BLE001
        print("  Hinweis: veröffentlichte data.json nicht erreichbar – Bild-Cache nur lokal.")
    for src in sources:
        for gid, val in (src.get("imgCache") or {}).items():
            if gid not in cache or val[2] > cache[gid][2]:
                cache[gid] = val
    return cache


def own_images() -> dict[str, str]:
    """
    List the own images in the bilder/ folder.

    Returns:
        Mapping ``{lower-cased gameId: relative path "bilder/<file>"}`` for all
        .webp, .png, .jpg and .jpeg files.
    """
    out = {}
    if OWN_DIR.is_dir():
        for p in sorted(OWN_DIR.iterdir()):
            if p.suffix.lower() in (".webp", ".png", ".jpg", ".jpeg"):
                out[p.stem.lower()] = f"bilder/{p.name}"
    return out


def attach_images(entries: list[dict]) -> dict[str, list]:
    """
    Attach a tile image to every blueprint, in place.

    Own images win; otherwise the cached wiki thumbnail is used. Items that are
    new to the cache are looked up in the wiki, plus the oldest due entries
    (IMG_MISS_DAYS / IMG_HIT_DAYS, at most IMG_REFRESH_MAX per run).

    Args:
        entries: Blueprint entries from build_data(); each gets ``img`` (URL or
            path) and ``imgs`` ("e" own, "w"/"c" wiki) if an image exists.

    Returns:
        The image cache reduced to the gameIds still in use, for data.json.
    """
    own = own_images()
    cache = load_img_cache()
    today = date.today()
    due_new, due_old = [], []
    for gid in sorted({e["gid"] for e in entries if e["gid"]} - set(own)):
        hit = cache.get(gid)
        if not hit:
            due_new.append(gid)
            continue
        age = (today - date.fromisoformat(hit[2])).days
        if (not hit[0] and age >= IMG_MISS_DAYS) or (hit[0] and age >= IMG_HIT_DAYS):
            due_old.append((hit[2], gid))
    due = due_new + [g for _, g in sorted(due_old)[:IMG_REFRESH_MAX]]
    if due:
        print(f"  Wiki-Bilder: {len(due_new)} neu, {len(due) - len(due_new)} aufzufrischen ...")
        with cf.ThreadPoolExecutor(4) as ex:
            for gid, (url, src) in zip(due, ex.map(wiki_image, due), strict=True):
                cache[gid] = [url, src, today.isoformat()]
    n_own = n_wiki = 0
    for e in entries:
        gid = e["gid"].lower()
        if gid in own:
            e["img"], e["imgs"] = own[gid], "e"
            n_own += 1
        elif cache.get(e["gid"], ["", ""])[0]:
            e["img"], e["imgs"] = cache[e["gid"]][0], cache[e["gid"]][1]
            n_wiki += 1
    print(f"  Bilder: {n_own} eigene, {n_wiki} aus dem Wiki, "
          f"{len(entries) - n_own - n_wiki} ohne Bild.")
    used = {e["gid"] for e in entries}
    return {g: v for g, v in cache.items() if g in used}


#: A thumbnail URL built by thumb_url() for starcitizen.tools, which the page can rebuild.
_SCT_THUMB = re.compile(
    r"^https://media\.starcitizen\.tools/thumb/([0-9a-f]/[0-9a-f]{2})/([^/]+)/"
    + str(THUMB_PX) + r"px-\2\.webp(\?\w+)?$")
#: Worklist of blueprints without an image (basis for own captures).
MISSING_CSV = HERE / "bilder_fehlend.csv"


def compact_entry(e: dict) -> dict:
    """
    Shrink a blueprint entry for embedding in the page.

    Drops the gameId and shortens a starcitizen.tools thumbnail to '~a/ab/file?q';
    the page rebuilds the full URL in imgUrl().

    Args:
        e: Blueprint entry from build_data().

    Returns:
        A new, compacted entry dict.
    """
    out = {k: v for k, v in e.items() if k != "gid"}
    m = _SCT_THUMB.match(out.get("img", ""))
    if m:
        out["img"] = "~" + m.group(1) + "/" + m.group(2) + (m.group(3) or "")
    return out


def write_missing_list(entries: list[dict]) -> None:
    """
    Write MISSING_CSV, the worklist of blueprints without an image.

    Semicolon-separated (gameId;name;kategorie), sorted by class and name, UTF-8
    with BOM so that Excel opens it correctly.

    Args:
        entries: Blueprint entries after attach_images().
    """
    rows = sorted((e["cls"], e["name"], e["gid"]) for e in entries if not e.get("img"))
    lines = ["gameId;name;kategorie"] + [f"{g};{n};{c}" for c, n, g in rows]
    MISSING_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print(f"Geschrieben: {MISSING_CSV.name} ({len(rows)} Baupläne ohne Bild)")


def build_data() -> dict:
    """
    Fetch all blueprints and reduce them to the lean app schema.

    Blueprints without a name or without a recipe are skipped. Per contract only
    the highest drop chance is kept. Each entry carries name, class/subclass,
    costs (``n`` material, ``q`` quantity, ``mq`` minimum quality), sources
    (``c`` contract, ``p`` drop chance in %), ``def`` (granted by default), the
    gameId and the spec fields; images are attached at the end.

    Returns:
        Data set with ``blueprints``, ``imgCache``, ``classOrder``, ``generated``
        (UTC timestamp) and ``n``.

    Raises:
        urllib.error.URLError: If star-head cannot be reached.
    """
    print("Lade Baupläne (star-head.de) ...")
    bp = get_json(BLUEPRINT_URL)
    print(f"  {len(bp)} Baupläne empfangen.")
    itmap = load_itmap()

    out = []
    for b in bp:
        name = str(b.get("name", "")).strip()
        if not name:
            continue
        costs = []
        for c in (b.get("costs") or []):
            cn = (c.get("commodity") or {}).get("name")
            if not cn:
                continue
            costs.append({"n": cn, "q": c.get("quantity") or 0, "mq": c.get("minQuality") or 0})
        if not costs:
            continue
        src: dict[str, int] = {}
        for r in (b.get("rewards") or []):
            cnm = clean_source(str(r.get("contractName") or ""))
            if not cnm:
                continue
            ch = int(r.get("dropChance") or 0)
            if cnm not in src or ch > src[cnm]:
                src[cnm] = ch
        sources = [{"c": k, "p": v} for k, v in sorted(src.items())]
        cls, sub = categorize(itmap.get(name.lower(), "Sonstiges"))
        entry = {
            "name": name,
            "cls": cls,
            "sub": sub,
            "costs": costs,
            "src": sources,
            "def": 1 if b.get("grantedByDefault") else 0,
            "gid": str((b.get("item") or {}).get("gameId") or ""),
        }
        entry.update(spec_fields((b.get("item") or {}).get("description") or ""))
        out.append(entry)

    out.sort(key=lambda x: x["name"].lower())
    n_src = sum(1 for x in out if x["src"])
    mats = {c["n"] for x in out for c in x["costs"]}
    print(f"  {len(out)} Baupläne mit Rezept, {n_src} mit Quelle, {len(mats)} Materialien.")
    img_cache = attach_images(out)
    return {
        "blueprints": out,
        "imgCache": img_cache,
        "classOrder": CLASS_ORDER,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "n": len(out),
    }


def fill_header(html: str) -> str:
    """
    Insert the shared header, design assets, "What's new?" dialog and changelog.

    Replaces the placeholders <!--FH_HEADER-->, /*FH_CSS*/, /*FH_JS*/,
    <!--SD_FONTS--> and <!--FH_DIALOG--> with output from kopfzeile.py and
    sc_design.py; the changelog is read from CHANGELOG.md.

    Args:
        html: The page template.

    Returns:
        The template with all shared parts filled in.
    """
    b = kz.bi
    actions = (
        '<button class="btn fh-btn" id="scdlBtn" type="button" title="sc_bp_erledigt.json aus dem SCDL-Launcher laden">'
        f'📥 {b("Erworbene (SCDL)", "Import owned (SCDL)")}</button>')
    refresh = ('<button class="btn fh-btn" id="refreshBtn" type="button" title="Neuesten täglich gebauten Datenstand von GitHub laden">'
               f'🔄 {b("Neuesten Stand laden (GitHub)", "Load latest build (GitHub)")}</button>')
    head = kz.header_html(
        "bauplan",
        eyebrow=("Crafting · Materialplanung", "Crafting · Material planning"),
        title=("SC Bauplan-Planer", "SC Blueprint Planner"),
        lede=("Baupläne wählen, Materialbedarf sehen, Beschaffung planen. Rezepte und Quellen von "
              "star-head.de – patch-abhängig, im Spiel gegenprüfen.",
              "Pick blueprints, see the material needs, plan the procurement. Recipes and sources "
              "from star-head.de – patch-dependent, verify in game."),
        version=VERSION, actions=actions, refresh=refresh,
        data='<span id="buildStat"></span>')
    html = html.replace("<!--FH_HEADER-->", head)
    html = html.replace("/*FH_CSS*/", kz.CSS + sd.CSS).replace("/*FH_JS*/", kz.JS + sd.JS)
    html = html.replace("<!--SD_FONTS-->", sd.FONTS)
    return html.replace("<!--FH_DIALOG-->", kz.dialog_html("bauplan", VERSION) + "\n"
                        + kz.changelog_script(HERE / "CHANGELOG.md"))


def main() -> int:
    """
    Build the data set and write the page, data.json and the missing-image list.

    Returns:
        Exit code: 0 on success, 1 if the blueprints could not be fetched.
    """
    try:
        data = build_data()
    except Exception as e:  # noqa: BLE001
        print(f"FEHLER: Baupläne nicht erreichbar: {e}", file=sys.stderr)
        return 1
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")  # no premature </script>
    # The image cache (check data per gameId) belongs in data.json only, not in the page;
    # in the page the gameIds are dropped and wiki thumbnail URLs shortened (see imgUrl in JS).
    page = {k: v for k, v in data.items() if k != "imgCache"}
    page["blueprints"] = [compact_entry(e) for e in data["blueprints"]]
    write_missing_list(data["blueprints"])
    page_payload = json.dumps(page, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = fill_header(HTML_TEMPLATE).replace("/*__DATA__*/{}", page_payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Geschrieben: {OUT_HTML} ({OUT_HTML.stat().st_size // 1024} KB)")
    # Same data set as a separate file: the "Load latest build" button in the
    # app fetches it from GitHub Pages instead of calling star-head directly.
    OUT_JSON.write_text(payload, encoding="utf-8")
    print(f"Geschrieben: {OUT_JSON} ({OUT_JSON.stat().st_size // 1024} KB)")
    return 0


# ============================================================ HTML template
#: The page template; main() replaces the placeholder /*__DATA__*/{} with the JSON data
#: set and fill_header() inserts the shared parts.
HTML_TEMPLATE = r"""<!DOCTYPE html>
<!-- SC Bauplan-Planer (SC Blueprint Planner) - generated by bauplan_planer_bauen.py, do not edit by hand. -->
<html lang="de" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SC Bauplan-Planer</title>
<meta name="description" content="Alle craftbaren Star-Citizen-Baupläne: Materialbedarf, Bestandsabgleich und exportierbare Beschaffungslisten.">
<!--SD_FONTS-->
<style>
  :root{
    --bg:#f4f6f8; --panel:#ffffff; --panel2:#eef1f5; --ink:#141922; --muted:#5a6472;
    --line:#d5dbe3; --accent:#0e7c86; --accent2:#c9822a; --ok:#2e8b57; --bad:#b3452f;
    --glow:rgba(14,124,134,.16); --shadow:0 2px 10px rgba(20,25,34,.08);
    --disp:'Exo 2',system-ui,sans-serif; --body:'Rajdhani',system-ui,sans-serif;
  }
  :root[data-theme="dark"]{
    --bg:#0a0e14; --panel:#121822; --panel2:#0e131c; --ink:#e8edf4; --muted:#8b97a8;
    --line:#243040; --accent:#3fd0dd; --accent2:#f0a94a; --ok:#57c98a; --bad:#e8785c;
    --glow:rgba(63,208,221,.14); --shadow:0 4px 20px rgba(0,0,0,.4);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.45;-webkit-font-smoothing:antialiased}
  .hazard{height:5px;background:repeating-linear-gradient(45deg,var(--accent2) 0 14px,transparent 14px 28px);opacity:.9}
  .wrap{max-width:1360px;margin:0 auto;padding:0 14px 60px}
  h1{font-family:var(--disp);font-weight:800;font-size:clamp(22px,3.5vw,32px);margin:0;letter-spacing:.01em}
  .eyebrow{font-family:var(--disp);font-weight:600;letter-spacing:.24em;text-transform:uppercase;color:var(--accent);font-size:11px;margin:0 0 4px}
  header{padding:22px 0 6px}
  .toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:14px 0 4px}
  .btn{font-family:var(--disp);font-weight:600;font-size:13px;letter-spacing:.04em;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 13px;cursor:pointer;transition:.15s}
  .btn:hover{border-color:var(--accent);color:var(--accent)}
  .btn.pri{background:var(--accent);color:var(--bg);border-color:var(--accent)}
  .btn.pri:hover{filter:brightness(1.08);color:var(--bg)}
  .spacer{flex:1 1 auto}
  .stat{font-family:var(--disp);font-size:12px;color:var(--muted);letter-spacing:.04em}

  .cols{display:grid;grid-template-columns:360px 1fr;gap:16px;margin-top:14px;align-items:start}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
  .left{position:sticky;top:12px;display:flex;flex-direction:column;gap:14px;max-height:calc(100vh - 24px);overflow:auto}
  .ph{font-family:var(--disp);font-weight:800;font-size:15px;letter-spacing:.02em;padding:12px 14px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px}
  .ph .n{margin-left:auto;font-size:12px;color:var(--muted);font-weight:600}
  .pbody{padding:10px 14px}

  /* left: resources */
  .restools{display:flex;gap:6px;padding:8px 14px 0}
  .resgrid{display:grid;grid-template-columns:1fr 74px;gap:4px 8px;padding:8px 14px 12px;font-size:13.5px;align-items:center}
  .resgrid label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .resgrid label.hot{color:var(--accent2);font-weight:700}
  input[type=number]{font-family:var(--body);font-size:14px;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:6px 8px;width:100%}
  input[type=search],select{font-family:var(--body);font-size:15px;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
  select{cursor:pointer}
  /* Multi-select filter: looks like a select, opens a checkbox list */
  .ms{position:relative}
  .ms>summary{list-style:none;font-family:var(--body);font-size:15px;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 30px 8px 10px;min-height:40px;cursor:pointer;white-space:nowrap;max-width:240px;overflow:hidden;text-overflow:ellipsis;position:relative;box-sizing:border-box}
  .ms>summary::-webkit-details-marker{display:none}
  .ms>summary::after{content:'▾';position:absolute;right:10px;top:50%;transform:translateY(-50%);color:var(--muted)}
  .ms[open]>summary::after{content:'▴'}
  .ms>summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .ms.has>summary{border-color:var(--accent);color:var(--accent);font-weight:600}
  .mspanel{position:absolute;z-index:40;top:calc(100% + 4px);left:0;min-width:240px;max-height:360px;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);padding:6px}
  .mspanel label{display:flex;gap:8px;align-items:center;min-height:34px;padding:4px 8px;border-radius:6px;cursor:pointer;font-size:14.5px;white-space:nowrap}
  .mspanel label:hover{background:var(--panel2)}
  .mspanel input{width:16px;height:16px;margin:0;accent-color:var(--accent);flex:0 0 auto}
  .mspanel .grp{font-family:var(--disp);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:8px 8px 2px}
  .mspanel .msclear{width:100%;margin:0 0 4px;min-height:34px}
  .mspanel .msclear:disabled{opacity:.45;cursor:default}

  table.mat{width:100%;border-collapse:collapse;font-size:14px}
  table.mat th,table.mat td{text-align:left;padding:5px 6px;border-bottom:1px solid var(--line)}
  table.mat th{font-family:var(--disp);font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
  table.mat td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--disp);font-weight:700}
  table.mat td.need{color:var(--accent2)}
  table.mat td.done{color:var(--ok)}
  .qbadge{font-size:10px;color:var(--accent2);border:1px solid var(--accent2);border-radius:10px;padding:0 5px;margin-left:5px}
  .warnbar{background:rgba(179,69,47,.12);color:var(--bad);border:1px solid var(--bad);border-radius:8px;padding:7px 10px;font-size:13px;margin-bottom:8px}
  .expbar{display:flex;gap:6px;flex-wrap:wrap;padding:10px 14px;border-top:1px solid var(--line)}
  .note{font-size:12.5px;color:var(--muted);padding:0 14px 12px}

  /* right: filters + catalog */
  .filters{display:flex;gap:8px;flex-wrap:wrap;padding:14px;border-bottom:1px solid var(--line);align-items:center}
  .filters input[type=search]{flex:1 1 220px;min-width:150px}
  .filters .fx{font-size:12.5px;color:var(--muted);font-family:var(--disp);margin-left:auto}
  .selbar{display:flex;flex-wrap:wrap;gap:6px;padding:10px 14px;border-bottom:1px solid var(--line);align-items:center;min-height:44px}
  .selchip{display:inline-flex;align-items:center;gap:6px;background:var(--panel2);border:1px solid var(--line);border-radius:20px;padding:3px 6px 3px 10px;font-size:13px}
  .selchip.miss{border-color:var(--bad);color:var(--bad);text-decoration:line-through}
  .selchip b{font-family:var(--disp)}
  .selchip .sx{cursor:pointer;border:none;background:none;color:var(--bad);font-size:15px;line-height:1;padding:0 2px}
  .selchip .st{cursor:pointer;border:none;background:none;color:var(--muted);font-weight:700;font-size:14px;padding:0 3px}
  .selempty{color:var(--muted);font-size:13.5px}

  .list{max-height:78vh;overflow:auto;padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px;align-content:start}
  .bp{display:flex;flex-direction:column;gap:7px;padding:13px 14px;border:1px solid var(--line);border-left:3px solid var(--line);border-radius:12px;background:var(--panel);box-shadow:var(--shadow);transition:.15s}
  .bp:hover{border-color:var(--accent);transform:translateY(-2px)}
  .bp.insel{border-color:var(--accent);border-left-color:var(--accent);background:rgba(63,208,221,.05)}
  .bp.own{border-left-color:var(--ok)}
  .bp .hd{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
  .bp .top{display:flex;gap:10px;align-items:flex-start}
  .bp .top .hd{flex:1;min-width:0}
  .bp .pic{flex:0 0 72px;width:72px;height:72px;border-radius:8px;background:var(--panel2);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;overflow:hidden}
  .bp .pic img{width:100%;height:100%;object-fit:contain;display:block}
  .bp .pic.none{display:none}
  .bp .pic .ph{font-family:var(--disp);font-size:10px;color:var(--muted);text-align:center;line-height:1.1;padding:2px}
  .bp .nm{font-family:var(--disp);font-weight:700;font-size:16px}
  .bp .badge{font-family:var(--disp);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);border:1px solid var(--line);border-radius:20px;padding:1px 8px;margin-left:8px;white-space:nowrap}
  .bp .owned{color:var(--ok);border-color:var(--ok)}
  .bp .recipe{display:flex;gap:6px;flex-wrap:wrap;margin-top:2px}
  .chip{font-size:13px;background:var(--panel2);border:1px solid var(--line);border-radius:7px;padding:2px 8px;white-space:nowrap}
  .chip .q{color:var(--accent2);font-weight:700}
  .bp .spec{font-size:12px;color:var(--accent);font-family:var(--disp);font-weight:600;letter-spacing:.04em}
  .bp .srcline{font-size:12.5px;color:var(--muted);margin-top:1px}
  .bp .srcline .none{color:var(--bad)}
  .scrollcap{max-height:33vh;overflow:auto}
  a.btn{text-decoration:none;display:inline-flex;align-items:center}
  .btn.swap{border-color:var(--accent2);color:var(--accent2)}
  .btn.swap:hover{background:var(--accent2);color:var(--bg)}
  .btn.onlysel{min-height:36px}
  .btn.onlysel[aria-pressed="true"]{background:var(--accent);color:var(--bg);border-color:var(--accent)}
  .btn.onlysel[aria-pressed="true"]:hover{filter:brightness(1.08);color:var(--bg)}
  .btn.onlysel:disabled{opacity:.45;cursor:not-allowed}
  .addbox{display:flex;align-items:center;gap:6px;margin-top:auto;padding-top:6px;border-top:1px solid var(--line)}
  .addbox input{width:56px;text-align:center}
  .addbtn{font-family:var(--disp);font-weight:700;font-size:14px;background:var(--accent);color:var(--bg);border:none;border-radius:8px;padding:8px 14px;cursor:pointer;margin-left:auto}
  .addbtn:hover{filter:brightness(1.08)}
  .morebtn{grid-column:1/-1;display:block;width:100%;margin:4px 0;text-align:center}
  .empty{color:var(--muted);font-size:14px;padding:16px}

  footer{margin-top:26px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
  .toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:10px 18px;border-radius:10px;font-family:var(--disp);font-weight:600;opacity:0;pointer-events:none;transition:.25s;z-index:50}
  .toast.show{opacity:1}
  .en{display:none}
  [data-lang="en"] .de{display:none}
  [data-lang="en"] .en{display:revert}

  @media(max-width:920px){
    .cols{grid-template-columns:1fr}
    .left{position:static;max-height:none}
    .list{max-height:none}
  }
  .statebar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;padding:8px 14px 12px;border-top:1px dashed var(--line)}
  .statebar .statelbl{font-family:var(--disp);font-weight:700;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-right:4px}
  .cols>*{min-width:0}
  .statebar .statelbl{flex:1 1 100%;margin:0 0 2px}
  .fmorebtn{display:none}
  @media(max-width:919px){.left{gap:0}.left .card{margin-bottom:0}}
  @media(max-width:600px){.fmorebtn{display:inline-flex;align-items:center;gap:4px}.filters:not(.showmore) .fopt{display:none}.filters{padding:10px}.filters input[type=search]{flex:1 1 100%}.list{grid-template-columns:1fr;max-height:none;padding:10px}}
/*FH_CSS*/
</style>
</head>
<body>
<div class="hazard"></div>
<div class="wrap">
<!--FH_HEADER-->

  <div class="sc-ptabs" id="bpTabs"></div>
  <div class="cols">
    <!-- LEFT: PROCUREMENT (top, scrollable) + RESOURCES -->
    <div class="left">
      <div class="card" id="cardList">
        <div class="ph"><span class="de">Beschaffungsliste</span><span class="en">Procurement list</span><span class="n" id="matN"></span></div>
        <div class="pbody scrollcap" id="matBody"></div>
        <p class="note"><span class="de">Materialien sind raffinierte Rohstoffe – kaufbar an Raffinerien/TDD oder selbst raffinieren.</span><span class="en">Materials are refined commodities – buy at refineries/TDD or refine them yourself.</span></p>
        <div class="expbar">
          <button class="btn pri" id="copyBtn" type="button">📋 <span class="de">Kopieren</span><span class="en">Copy</span></button>
          <button class="btn" id="txtBtn" type="button">⬇ .txt</button>
          <button class="btn" id="csvBtn" type="button">⬇ .csv</button>
        </div>
        <div class="statebar">
          <span class="statelbl"><span class="de">Auswahl &amp; Bestand</span><span class="en">Selection &amp; stock</span></span>
          <button class="btn" id="stateBtn" type="button" title="Auswahl + Bestand als JSON speichern">💾 <span class="de">Speichern</span><span class="en">Save</span></button>
          <button class="btn" id="loadStateBtn" type="button" title="Gespeicherten Zustand laden">📂 <span class="de">Laden</span><span class="en">Load</span></button>
        </div>
      </div>

      <div class="card" id="cardRes">
        <div class="ph"><span class="de">Verfügbare Ressourcen</span><span class="en">Available resources</span><span class="n" id="resN"></span></div>
        <div class="restools">
          <button class="btn" id="resClear" type="button" style="padding:4px 9px;font-size:12px"><span class="de">alle 0</span><span class="en">reset</span></button>
          <span class="stat" style="align-self:center"><span class="de">Bestand, den du schon hast</span><span class="en">what you already own</span></span>
        </div>
        <div class="resgrid" id="resGrid"></div>
      </div>
    </div>

    <!-- RIGHT: FILTERS + SELECTION + CATALOG -->
    <div class="card" id="cardCat">
      <div class="filters">
        <input type="search" id="q" placeholder="Suchen … (Name / Material)" autocomplete="off">
        <details class="ms" id="fClass"></details>
        <details class="ms" id="fSub"></details>
        <button class="btn fmorebtn" id="fMoreBtn" type="button" aria-expanded="false"><span class="de">Weitere Filter</span><span class="en">More filters</span> <span id="fMoreN"></span></button>
        <details class="ms fopt" id="fSize"></details>
        <details class="ms fopt" id="fGrade"></details>
        <details class="ms fopt" id="fKls"></details>
        <select id="fOwned" class="fopt" disabled>
          <option value="all" data-i18n="ownAll">alle</option>
          <option value="yes" data-i18n="ownYes">nur erworben</option>
          <option value="no" data-i18n="ownNo">nur nicht erworben</option>
        </select>
        <select id="fSort" class="fopt">
          <option value="name" data-i18n="sortName">Name A–Z</option>
          <option value="mats" data-i18n="sortMats">wenigste Materialien</option>
        </select>
        <button class="btn onlysel" id="onlySel" type="button" aria-pressed="false"><span id="onlySelBox">☐</span> <span data-i18n="onlySel">nur ausgewählte</span> <span id="onlySelN"></span></button>
        <span class="fx"><span id="catCount"></span></span>
      </div>
      <div class="selbar" id="selBar"></div>
      <div class="list" id="list"></div>
    </div>
  </div>

  <footer>
    <p><span class="de">Daten: star-head.de (Baupläne/Rezepte) · Kategorien: SC-Deutsch-Launcher-Typen. Erworbene Baupläne per SCDL-Export (<code>sc_bp_erledigt.json</code>). Rezepte patch-abhängig.</span><span class="en">Data: star-head.de (blueprints/recipes) · categories from SC-Deutsch-Launcher types. Owned blueprints via SCDL export (<code>sc_bp_erledigt.json</code>). Recipes patch-dependent.</span></p>
    <p><span class="de">Bilder: <a href="https://starcitizen.tools/" target="_blank" rel="noopener">Star Citizen Wiki</a> (verlinkt, werden beim Ansehen von dort geladen) und eigene Aufnahmen · Spielinhalte © Cloud Imperium Games. Ohne Internet bleiben die Kacheln ohne Bild.</span><span class="en">Images: <a href="https://starcitizen.tools/" target="_blank" rel="noopener">Star Citizen Wiki</a> (linked, loaded from there when viewed) and own captures · game content © Cloud Imperium Games. Offline, tiles show no images.</span></p>
    <p><span id="footStat"></span> · <span class="de">Inoffiziell, nicht mit CIG verbunden. Alle Angaben ohne Gewähr.</span><span class="en">Unofficial, not affiliated with CIG. No guarantee.</span></p>
  </footer>
</div>

<input type="file" id="fileScdl" accept=".json" hidden>
<input type="file" id="fileState" accept=".json" hidden>
<div class="toast" id="toast"></div>

<script>
const RAW = /*__DATA__*/{};
const DATA_URL='https://jaegerfeld.github.io/StarCitizen-Bauplan-Planer/data.json';
let CUR_GEN=RAW.generated||'';
</script>
<script>
"use strict";
/* ---------- i18n ---------- */
const I18N={
  de:{ownAll:'alle',ownYes:'nur erworben',ownNo:'nur nicht erworben',sortName:'Name A–Z',sortMats:'wenigste Materialien',
    src:'Quelle',srcNone:'Quelle unbekannt',mat:'Material',need:'benötigt',left:'noch',allClass:'alle Kategorien',allSub:'alle Unterkategorien',allSize:'alle Größen',allGrade:'alle Grade',allKls:'alle Klassen',
    selEmpty:'Noch keine Baupläne gewählt – im Katalog „+" klicken.',matEmpty:'Wähle Baupläne, um den Materialbedarf zu sehen.',
    owned:'erworben',added:'hinzugefügt',copied:'in Zwischenablage kopiert',have:'Bestand',
    orphan:'nicht im Katalog',orphanWarn:n=>`⚠ ${n} gewählte(r) Bauplan/Baupläne nicht im Katalog – nicht in der Summe enthalten.`,
    scdlOk:(n,u)=>`${n} erworbene erkannt${u?`, ${u} nicht im Katalog`:''}.`,scdlErr:'Datei nicht lesbar (sc_bp_erledigt.json erwartet).',
    refOk:'Neuester Stand geladen.',refErr:'GitHub nicht erreichbar – bestehende Daten bleiben.',refSame:'Du hast bereits den neuesten Stand.',stateOk:'Zustand geladen.',stateErr:'Zustand nicht lesbar.',
    results:'Treffer',more:n=>`… ${n} weitere anzeigen`,
    onlySel:'nur ausgewählte',onlySelTip:'Katalog auf die gewählten Baupläne beschränken (andere Filter gelten weiter)',
    onlySelHidden:n=>`Die übrigen Filter blenden ${n} gewählte(n) Bauplan/Baupläne aus.`,resetFilters:'Filter zurücksetzen',msClear:'Auswahl löschen (alle)',
    imgWiki:'Bild: Star Citizen Wiki (starcitizen.tools) · © CIG',imgOwn:'Bild: eigene Aufnahme · © CIG'},
  en:{ownAll:'all',ownYes:'owned only',ownNo:'not owned only',sortName:'Name A–Z',sortMats:'fewest materials',
    src:'Source',srcNone:'source unknown',mat:'Material',need:'need',left:'left',allClass:'all categories',allSub:'all subcategories',allSize:'all sizes',allGrade:'all grades',allKls:'all classes',
    selEmpty:'No blueprints selected yet – click “+” in the catalog.',matEmpty:'Select blueprints to see the material needs.',
    owned:'owned',added:'added',copied:'copied to clipboard',have:'stock',
    orphan:'not in catalog',orphanWarn:n=>`⚠ ${n} selected blueprint(s) not in catalog – excluded from totals.`,
    scdlOk:(n,u)=>`${n} owned detected${u?`, ${u} not in catalog`:''}.`,scdlErr:'File not readable (expected sc_bp_erledigt.json).',
    refOk:'Latest build loaded.',refErr:'GitHub unreachable – keeping current data.',refSame:'You already have the latest build.',stateOk:'State loaded.',stateErr:'State not readable.',
    results:'results',more:n=>`… show ${n} more`,
    onlySel:'selected only',onlySelTip:'Limit the catalog to your selected blueprints (other filters still apply)',
    onlySelHidden:n=>`The other filters hide ${n} selected blueprint(s).`,resetFilters:'Reset filters',msClear:'Clear selection (all)',
    imgWiki:'Image: Star Citizen Wiki (starcitizen.tools) · © CIG',imgOwn:'Image: own capture · © CIG'}
};
const LS={lang:'scbp_lang',theme:'scbp_theme',sel:'scbp_sel',stock:'scbp_stock',owned:'scbp_owned',ownMeta:'scbp_ownmeta',onlySel:'scbp_onlysel'};
const root=document.documentElement;
let LANG=(load(LS.lang)==='en')?'en':'de';
// Look up a UI string (or string function) in the current language.
function t(k){return I18N[LANG][k];}

/* ---------- state ---------- */
let BP=[], CLASS_ORDER=[], SUBS={}, MATS=[], SIZES=[], GRADES=[], KLS=[];
const GRADE_RANK={A:0,B:1,C:2,D:3};
let SEL=load(LS.sel)||{}, STOCK=load(LS.stock)||{}, OWNED=load(LS.owned)||{}, OWNMETA=load(LS.ownMeta)||null;
let renderCap=150;

/* ---------- helpers ---------- */
// Read a JSON value from localStorage; null if missing, unreadable or storage blocked.
function load(k){try{const v=localStorage.getItem(k);return v?JSON.parse(v):null;}catch(e){return null;}}
// Write a JSON value to localStorage; failures (private mode, quota) are ignored.
function save(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
// Escape text for use in HTML content and attribute values.
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
// Show a short status message at the bottom of the page for about two seconds.
function toast(m){const el=document.getElementById('toast');el.textContent=m;el.classList.add('show');clearTimeout(el._t);el._t=setTimeout(()=>el.classList.remove('show'),2200);}
// Offer text as a file download via a temporary object URL.
function down(name,text,type){const b=new Blob([text],{type:type||'text/plain'});const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1500);}
// JS twin of clean_source() in the build script (readable contract names); currently not called by the page.
function cleanSrc(s){s=String(s).replace(/~\w+\([^)]*\)/g,'(Ort)').trim();if(/^[a-z0-9_]+$/.test(s)){const m=s.match(/blackbox_recover_title_([a-z]+)_/);if(m)return'Black Box Recovery ('+m[1].toUpperCase()+')';return s.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());}return s;}
// JS twin of spec_fields() in the build script (size/grade/class from a description); currently not called by the page.
function specOf(desc){desc=String(desc||'').replace(/\\n/g,'\n').replace(/ /g,' ');const g=k=>{const m=desc.match(new RegExp('^'+k+':\\s*(.+?)\\s*$','mi'));return m?m[1].trim():'';};const o={};let s=g('Size').replace(/^s/i,'').trim();if(s)o.sz=s;const gr=g('Grade');if(gr)o.gr=gr;const kl=g('Class');if(kl)o.kl=kl;return o;}

// Load a data set: build the search text per blueprint, mark default-granted ones as owned
// (until an SCDL import exists) and derive the filter value lists and status lines.
function ingest(raw){
  BP=(raw.blueprints||[]).map(b=>{
    const s=(b.name+' '+(b.cls||'')+' '+(b.sub||'')+' '+(b.sz?'s'+b.sz:'')+' '+(b.gr||'')+' '+(b.kl||'')+' '+b.costs.map(c=>c.n).join(' ')).toLowerCase();
    return Object.assign({},b,{_s:s});
  });
  BP.forEach(b=>{if(b.def && OWNMETA===null) OWNED[b.name]=1;});
  const present=new Set(BP.map(b=>b.cls));
  CLASS_ORDER=(raw.classOrder||[]).filter(c=>present.has(c));
  [...present].forEach(c=>{if(!CLASS_ORDER.includes(c))CLASS_ORDER.push(c);});
  SUBS={};
  for(const b of BP){(SUBS[b.cls]=SUBS[b.cls]||new Set()).add(b.sub);}
  for(const k in SUBS)SUBS[k]=[...SUBS[k]].sort((a,b)=>a.localeCompare(b));
  MATS=[...new Set(BP.flatMap(b=>b.costs.map(c=>c.n)))].sort((a,b)=>a.localeCompare(b));
  SIZES=[...new Set(BP.map(b=>b.sz).filter(Boolean))].sort((a,b)=>(parseInt(a,10)||0)-(parseInt(b,10)||0));
  GRADES=[...new Set(BP.map(b=>b.gr).filter(Boolean))].sort((a,b)=>((GRADE_RANK[a]??9)-(GRADE_RANK[b]??9))||a.localeCompare(b));
  KLS=[...new Set(BP.map(b=>b.kl).filter(Boolean))].sort((a,b)=>a.localeCompare(b));
  document.getElementById('buildStat').textContent=(raw.source||'')+' '+(raw.generated||'');
  document.getElementById('footStat').textContent=BP.length+' '+(LANG==='de'?'Baupläne':'blueprints')+' · '+MATS.length+' '+(LANG==='de'?'Materialien':'materials');
}

/* ---------- filters ---------- */
const qEl=document.getElementById('q'), fClass=document.getElementById('fClass'),
      fSub=document.getElementById('fSub'), fOwned=document.getElementById('fOwned'),
      fSort=document.getElementById('fSort'), listEl=document.getElementById('list'),
      fSize=document.getElementById('fSize'), fGrade=document.getElementById('fGrade'), fKls=document.getElementById('fKls');

/* ---------- Multi-select (details/summary + checkboxes) ----------
   Empty selection = all. Values as a Set in MS[id].sel; changes fire 'mschange' on the element. */
const MS={};
// Turn a <details> element into a multi-select filter; only one panel is open at a time.
function msInit(el,allKey){
  MS[el.id]={el,sel:new Set(),items:[],allKey};
  el.innerHTML='<summary></summary><div class="mspanel" role="group"></div>';
  el.addEventListener('change',e=>{
    const i=e.target; if(!i.matches('input[type=checkbox]')) return;
    const m=MS[el.id]; if(i.checked) m.sel.add(i.value); else m.sel.delete(i.value);
    msLabel(el.id); el.querySelector('.msclear').disabled=!m.sel.size;
    el.dispatchEvent(new Event('mschange'));
  });
  el.addEventListener('click',e=>{
    if(!e.target.closest('.msclear')) return;
    MS[el.id].sel.clear(); msRender(el.id); el.dispatchEvent(new Event('mschange'));
  });
  el.addEventListener('toggle',()=>{if(el.open) Object.values(MS).forEach(m=>{if(m.el!==el) m.el.open=false;});});
}
// Set the options of a multi-select; selected values that no longer exist are dropped.
function msSet(id,items){   // items: [{v,label,grp?}]
  const m=MS[id]; m.items=items; const ok=new Set(items.map(x=>x.v));
  [...m.sel].forEach(v=>{if(!ok.has(v)) m.sel.delete(v);}); msRender(id);
}
// Draw the checkbox list, with group headings when the options span several groups.
function msRender(id){
  const m=MS[id]; let grp=null, html=`<button class="btn msclear" type="button"${m.sel.size?'':' disabled'}>${t('msClear')}</button>`;
  const grouped=new Set(m.items.map(x=>x.grp||'')).size>1;
  for(const x of m.items){
    if(grouped && x.grp!==grp){grp=x.grp; html+=`<div class="grp">${esc(grp)}</div>`;}
    html+=`<label><input type="checkbox" value="${esc(x.v)}"${m.sel.has(x.v)?' checked':''}>${esc(x.label)}</label>`;
  }
  m.el.querySelector('.mspanel').innerHTML=html; msLabel(id);
}
// Update the summary text: placeholder, up to two names, or first name plus count.
function msLabel(id){
  const m=MS[id], n=m.sel.size, lab=v=>(m.items.find(x=>x.v===v)||{label:v}).label;
  const vals=m.items.filter(x=>m.sel.has(x.v)).map(x=>x.v);
  const txt=!n?t(m.allKey):n<=2?vals.map(lab).join(', '):lab(vals[0])+' +'+(n-1);
  const s=m.el.querySelector('summary'); s.textContent=txt; s.title=n?vals.map(lab).join(', '):t(m.allKey);
  m.el.classList.toggle('has',n>0);
}
document.addEventListener('click',e=>{Object.values(MS).forEach(m=>{if(m.el.open&&!m.el.contains(e.target)) m.el.open=false;});});
document.addEventListener('keydown',e=>{if(e.key==='Escape') Object.values(MS).forEach(m=>{if(m.el.open){m.el.open=false;m.el.querySelector('summary').focus();}});});
[[fClass,'allClass'],[fSub,'allSub'],[fSize,'allSize'],[fGrade,'allGrade'],[fKls,'allKls']].forEach(([el,k])=>msInit(el,k));

// Fill the category filter and rebuild the dependent filters.
function buildClassFilter(){
  msSet('fClass',CLASS_ORDER.map(c=>({v:c,label:c})));
  buildSubFilter();
  buildSpecFilters();
}
// Fill the size, grade and class filters from the current data.
function buildSpecFilters(){
  msSet('fSize',SIZES.map(s=>({v:s,label:'S'+s})));
  msSet('fGrade',GRADES.map(s=>({v:s,label:s})));
  msSet('fKls',KLS.map(s=>({v:s,label:s})));
}
// Fill the subcategory filter with the subcategories of the chosen categories (none chosen: all), grouped by category.
function buildSubFilter(){
  const cl=MS.fClass.sel;
  const items=CLASS_ORDER.filter(c=>!cl.size||cl.has(c)).flatMap(c=>(SUBS[c]||[]).map(s=>({v:c+'|'+s,label:s,grp:c})));
  msSet('fSub',items);
}
const onlySelBtn=document.getElementById('onlySel');
let ONLY_SEL=load(LS.onlySel)===true;
// Number of selected blueprints that exist in the current catalog.
function selCount(){return Object.keys(SEL).filter(n=>BP.some(x=>x.name===n)).length;}
// Sync the selected-only toggle with the selection; switches it off when nothing is selected.
function syncOnlySel(){
  const n=selCount();
  if(!n&&ONLY_SEL){ONLY_SEL=false;save(LS.onlySel,false);}   // no selection, no empty catalog
  onlySelBtn.setAttribute('aria-pressed',ONLY_SEL?'true':'false');
  document.getElementById('onlySelBox').textContent=ONLY_SEL?'☑':'☐';   // second signal besides the colour
  onlySelBtn.disabled=!n;
  onlySelBtn.title=t('onlySelTip');
  document.getElementById('onlySelN').textContent=n?'('+n+')':'';
}
// Clear search and all filters and redraw the catalog.
function resetFilters(){qEl.value='';Object.keys(MS).forEach(id=>MS[id].sel.clear());buildSubFilter();Object.keys(MS).forEach(msRender);fOwned.value='all';renderCap=150;renderList();}
// Apply search and filters to the catalog and sort it; the owned filter only applies once ownership data exists.
function filtered(){
  const q=qEl.value.trim().toLowerCase(), ow=fOwned.value,
        cl=MS.fClass.sel, su=MS.fSub.sel, sz=MS.fSize.sel, gr=MS.fGrade.sel, kl=MS.fKls.sel,
        hasOwn=OWNMETA!==null||Object.keys(OWNED).length>0;
  let arr=BP.filter(b=>{
    if(ONLY_SEL && !SEL[b.name]) return false;
    if(q && !b._s.includes(q)) return false;
    if(cl.size && !cl.has(b.cls)) return false;
    if(su.size && !su.has(b.cls+'|'+b.sub)) return false;
    if(sz.size && !sz.has(b.sz)) return false;
    if(gr.size && !gr.has(b.gr)) return false;
    if(kl.size && !kl.has(b.kl)) return false;
    if(hasOwn && ow==='yes' && !OWNED[b.name]) return false;
    if(hasOwn && ow==='no' && OWNED[b.name]) return false;
    return true;
  });
  if(fSort.value==='mats') arr.sort((a,b)=>a.costs.length-b.costs.length||a.name.localeCompare(b.name));
  else arr.sort((a,b)=>a.name.localeCompare(b.name));
  return arr;
}
// Recipe as chips: quantity, material and minimum-quality badge.
function recipeChips(b){
  return b.costs.map(c=>`<span class="chip"><span class="q">${c.q}×</span> ${esc(c.n)}${c.mq>0?`<span class="qbadge">Q≥${c.mq}</span>`:''}</span>`).join('');
}
// Spec line (size, grade, class); empty if the item has none.
function specBadge(b){
  const p=[]; if(b.sz)p.push('S'+b.sz); if(b.gr)p.push(b.gr); if(b.kl)p.push(b.kl);
  return p.length?`<div class="spec">${esc(p.join(' · '))}</div>`:'';
}
// Source line: first three contracts with drop chance (100 % is not shown), plus a count of the rest.
function srcLine(b){
  if(!b.src||!b.src.length) return `<div class="srcline"><span class="none">✖ ${t('srcNone')}</span></div>`;
  const parts=b.src.slice(0,3).map(s=>esc(s.c)+(s.p<100?` (${s.p}%)`:''));
  return `<div class="srcline">▸ ${t('src')}: ${parts.join(' · ')}${b.src.length>3?` +${b.src.length-3}`:''}</div>`;
}
/* Tile image: own image (bilder/<gameId>) or thumbnail from the Star Citizen Wiki (linked).
   Loads only when scrolled into view; if loading fails (offline, image removed), the frame disappears. */
const IMG_SRC={e:'imgOwn',w:'imgWiki',c:'imgWiki'};
// Expand the shortened wiki thumbnail from the build script back into a full starcitizen.tools URL.
function imgUrl(s){   // '~a/ab/Datei?q' -> starcitizen.tools-Thumb (160 px); volle URLs bleiben
  if(!s||s[0]!=='~') return s||'';
  const m=/^~([0-9a-f]\/[0-9a-f]{2})\/([^?]+)(\?.*)?$/.exec(s); if(!m) return '';
  return `https://media.starcitizen.tools/thumb/${m[1]}/${m[2]}/160px-${m[2]}.webp${m[3]||''}`;
}
// Tile image markup with source tooltip; lazy-loaded, hidden on load error.
function picHtml(b){
  if(!b.img) return '';
  const tip=t(IMG_SRC[b.imgs]||'imgWiki');
  return `<div class="pic" title="${esc(tip)}"><img src="${esc(imgUrl(b.img))}" alt="${esc(b.name)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.parentNode.classList.add('none')"></div>`;
}
// Draw the catalog tiles up to renderCap, with a show-more button and a hint when filters hide selected items.
function renderList(){
  syncOnlySel(); syncMoreN();
  const arr=filtered();
  document.getElementById('catCount').textContent=arr.length+' '+t('results');
  const slice=arr.slice(0,renderCap);
  let html=slice.map(b=>`
    <div class="bp${SEL[b.name]?' insel':''}${OWNED[b.name]?' own':''}" data-nm="${esc(b.name)}">
      <div class="top">${picHtml(b)}<div class="hd"><span class="nm">${esc(b.name)}</span><span class="badge">${esc(b.sub)}</span>${OWNED[b.name]?`<span class="badge owned">✓ ${t('owned')}</span>`:''}</div></div>
      ${specBadge(b)}
      <div class="recipe">${recipeChips(b)}</div>
      ${srcLine(b)}
      <div class="addbox"><input type="number" min="1" value="1" aria-label="qty"><button class="addbtn" type="button">+</button></div>
    </div>`).join('');
  if(arr.length>renderCap) html+=`<button class="btn morebtn" id="moreBtn" type="button">${t('more')(arr.length-renderCap)}</button>`;
  // With "selected only": say when the other filters hide selected blueprints
  const hidden=ONLY_SEL?selCount()-arr.length:0;
  if(hidden>0) html=`<div class="empty" style="grid-column:1/-1">${t('onlySelHidden')(hidden)} <button class="btn" id="resetF" type="button">${t('resetFilters')}</button></div>`+html;
  listEl.innerHTML=html||`<div class="empty">—</div>`;
}

/* ---------- selection ---------- */
// Add a quantity of a blueprint to the selection and redraw.
function addSel(name,qty){SEL[name]=(SEL[name]||0)+Math.max(1,qty|0);save(LS.sel,SEL);renderSel();renderMats();renderList();toast(t('added'));}
// Set the quantity of a selected blueprint; 0 or less removes it.
function setSel(name,qty){if(qty<=0)delete SEL[name];else SEL[name]=qty;save(LS.sel,SEL);renderSel();renderMats();renderList();}
// Draw the selection chips; blueprints missing from the catalog are struck through.
function renderSel(){
  if(window.BP_TABS) BP_TABS.count('list',Object.keys(SEL).length);
  const keys=Object.keys(SEL);
  const bar=document.getElementById('selBar');
  if(!keys.length){bar.innerHTML=`<span class="selempty">${t('selEmpty')}</span>`;return;}
  bar.innerHTML=keys.sort((a,b)=>a.localeCompare(b)).map(n=>{
    const miss=!BP.find(x=>x.name===n);
    return `<span class="selchip${miss?' miss':''}" data-nm="${esc(n)}" title="${miss?esc(t('orphan')):''}">
      <button class="st dec" type="button">−</button><b>${SEL[n]}×</b> ${esc(n)}<button class="st inc" type="button">+</button><button class="sx" type="button" title="entfernen">✕</button></span>`;
  }).join('');
}

/* ---------- material aggregation ---------- */
// Sum the materials of all selected blueprints, separately per minimum quality, largest first.
function aggregate(){
  const agg={};
  for(const [nm,cnt] of Object.entries(SEL)){
    const b=BP.find(x=>x.name===nm); if(!b)continue;
    for(const c of b.costs){const k=c.n+'|'+c.mq;(agg[k]=agg[k]||{n:c.n,mq:c.mq,q:0}).q+=c.q*cnt;}
  }
  return Object.values(agg).sort((a,b)=>b.q-a.q||a.n.localeCompare(b.n));
}
// Draw the procurement table; the remaining column appears only when stock is entered.
function renderMats(){
  const rows=aggregate();
  const miss=Object.keys(SEL).filter(n=>!BP.find(x=>x.name===n));
  const warn=miss.length?`<div class="warnbar">${t('orphanWarn')(miss.length)}</div>`:'';
  document.getElementById('matN').textContent=rows.length?rows.length+' '+t('mat'):'';
  const body=document.getElementById('matBody');
  if(!rows.length){body.innerHTML=warn||`<div class="empty" style="padding:6px 0">${t('matEmpty')}</div>`;return;}
  const hasStock=rows.some(r=>(STOCK[r.n]||0)>0);
  let h='<table class="mat"><thead><tr><th>'+t('mat')+'</th><th style="text-align:right">'+t('need')+'</th>';
  if(hasStock)h+='<th style="text-align:right">'+t('left')+'</th>';
  h+='</tr></thead><tbody>';
  for(const r of rows){
    const have=STOCK[r.n]||0,leftv=Math.max(0,r.q-have);
    h+=`<tr><td>${esc(r.n)}${r.mq>0?`<span class="qbadge">Q≥${r.mq}</span>`:''}</td><td class="num">${r.q.toLocaleString()}</td>`;
    if(hasStock)h+=`<td class="num ${leftv>0?'need':'done'}">${leftv>0?leftv.toLocaleString():'✓'}</td>`;
    h+='</tr>';
  }
  body.innerHTML=warn+h+'</tbody></table>';
}
// Draw the stock inputs for all materials; materials needed by the selection are highlighted.
function renderRes(){
  document.getElementById('resN').textContent=MATS.length;
  const need=new Set(aggregate().map(r=>r.n));
  document.getElementById('resGrid').innerHTML=MATS.map(m=>
    `<label class="${need.has(m)?'hot':''}" title="${esc(m)}">${esc(m)}</label><input type="number" min="0" data-mat="${esc(m)}" value="${STOCK[m]||''}" placeholder="0">`).join('');
}

/* ---------- export ---------- */
// Procurement list as plain text (blueprints, then materials with stock and remainder).
function exportText(){
  const rows=aggregate(), d=new Date().toISOString().slice(0,10);
  let s=`SC Beschaffungsliste — ${d}\n\n`+(LANG==='de'?'Baupläne:':'Blueprints:')+'\n';
  for(const [n,c] of Object.entries(SEL).sort((a,b)=>a[0].localeCompare(b[0]))) s+=`  ${c}× ${n}\n`;
  s+='\n'+(LANG==='de'?'Materialien:':'Materials:')+'\n';
  for(const r of rows){const have=STOCK[r.n]||0,leftv=Math.max(0,r.q-have);
    s+=`  ${r.q}× ${r.n}${r.mq>0?` (Q≥${r.mq})`:''}${have?`  [${t('have')} ${have} → ${t('left')} ${leftv}]`:''}\n`;}
  return s;
}
// Material totals as CSV (material, minimum quality, need, stock, remainder).
function exportCsv(){
  let s='Material,MinQuality,Need,Stock,Left\n';
  for(const r of aggregate()){const have=STOCK[r.n]||0,leftv=Math.max(0,r.q-have);
    s+=`"${r.n}",${r.mq},${r.q},${have},${leftv}\n`;}
  return s;
}

/* ---------- SCDL import ---------- */
// Import owned blueprints from the SCDL export sc_bp_erledigt.json (list or {blueprints}); entries with
// isDone false are skipped, names matched case-insensitively, default-granted ones always count as owned.
function importScdl(obj){
  const list=Array.isArray(obj)?obj:(obj&&obj.blueprints);
  if(!Array.isArray(list)) throw new Error('bad');
  const names=new Map(BP.map(b=>[b.name.toLowerCase(),b.name]));
  OWNED={}; let matched=0; const unmatched=[];
  for(const e of list){
    if(e&&typeof e==='object'&&e.isDone===false)continue;
    const key=(typeof e==='string'?e:(e.key||e.name||'')).trim();
    if(!key)continue;
    const real=names.get(key.toLowerCase());
    if(real){OWNED[real]=1;matched++;} else unmatched.push(key);
  }
  BP.forEach(b=>{if(b.def)OWNED[b.name]=1;});
  OWNMETA={ts:new Date().toISOString(),matched,unmatched};
  save(LS.owned,OWNED);save(LS.ownMeta,OWNMETA);
  fOwned.disabled=false;
  renderList();renderSel();
  toast(t('scdlOk')(matched,unmatched.length));
}

/* ---------- refresh ---------- */
// Refresh button: replace the embedded data with the latest published data.json.
async function refresh(){
  // Loads the data set last built on GitHub (daily). No direct access to
  // star-head from the browser any more - this spares the community API.
  const btn=document.getElementById('refreshBtn'); if(btn.dataset.busy)return;
  btn.dataset.busy='1'; btn.disabled=true;
  try{
    const r=await fetch(DATA_URL,{cache:'no-store'}); if(!r.ok)throw new Error('HTTP '+r.status);
    const raw=await r.json();
    if(!raw||!Array.isArray(raw.blueprints)||!raw.blueprints.length)throw new Error('leer');
    if(raw.generated&&raw.generated===CUR_GEN){toast(t('refSame'));return;}
    CUR_GEN=raw.generated||'';
    ingest(Object.assign({},raw,{source:'GitHub'}));
    buildClassFilter();renderRes();renderList();renderSel();renderMats();
    toast(t('refOk'));
  }catch(e){toast(t('refErr'));}
  finally{btn.dataset.busy='';btn.disabled=false;}
}

/* ---------- events ---------- */
let qt=null;
qEl.addEventListener('input',()=>{clearTimeout(qt);qt=setTimeout(()=>{renderCap=150;renderList();},130);});
fClass.addEventListener('mschange',()=>{buildSubFilter();renderCap=150;renderList();});
[fSub,fSize,fGrade,fKls].forEach(el=>el.addEventListener('mschange',()=>{renderCap=150;renderList();}));
[fOwned,fSort].forEach(el=>el.addEventListener('change',()=>{renderCap=150;renderList();}));
document.getElementById('fMoreBtn').addEventListener('click',e=>{const f=e.currentTarget.closest('.filters');const on=f.classList.toggle('showmore');e.currentTarget.setAttribute('aria-expanded',on?'true':'false');});
// Show how many of the filters behind More filters are active (narrow screens).
function syncMoreN(){const n=['fSize','fGrade','fKls'].reduce((a,k)=>a+(MS[k]&&MS[k].sel.size?1:0),0)+(fOwned.value!=='all'?1:0);document.getElementById('fMoreN').textContent=n?'('+n+')':'';}
onlySelBtn.addEventListener('click',()=>{ONLY_SEL=!ONLY_SEL;save(LS.onlySel,ONLY_SEL);renderCap=150;renderList();});
listEl.addEventListener('click',e=>{if(e.target.closest('#resetF'))resetFilters();});
listEl.addEventListener('click',e=>{
  if(e.target.id==='moreBtn'){renderCap+=200;renderList();return;}
  const add=e.target.closest('.addbtn'); if(add){const row=add.closest('.bp');addSel(row.dataset.nm,parseInt(row.querySelector('input').value,10)||1);}
});
document.getElementById('selBar').addEventListener('click',e=>{
  const chip=e.target.closest('.selchip'); if(!chip)return; const nm=chip.dataset.nm;
  if(e.target.classList.contains('inc'))setSel(nm,(SEL[nm]||0)+1);
  else if(e.target.classList.contains('dec'))setSel(nm,(SEL[nm]||0)-1);
  else if(e.target.classList.contains('sx'))setSel(nm,0);
});
document.getElementById('resGrid').addEventListener('input',e=>{
  const m=e.target.dataset.mat; if(!m)return; const v=parseInt(e.target.value,10)||0;
  if(v>0)STOCK[m]=v;else delete STOCK[m]; save(LS.stock,STOCK);renderMats();
});
document.getElementById('resClear').addEventListener('click',()=>{STOCK={};save(LS.stock,STOCK);renderRes();renderMats();});
document.getElementById('copyBtn').addEventListener('click',()=>{const s=exportText();navigator.clipboard?.writeText(s).then(()=>toast(t('copied')),()=>down('SC_Beschaffungsliste.txt',s));});
document.getElementById('txtBtn').addEventListener('click',()=>down('SC_Beschaffungsliste.txt',exportText()));
document.getElementById('csvBtn').addEventListener('click',()=>down('SC_Beschaffungsliste.csv',exportCsv(),'text/csv'));
document.getElementById('stateBtn').addEventListener('click',()=>down('SC_Bauplan_Zustand.json',JSON.stringify({schema:'scbp1',sel:SEL,stock:STOCK,owned:OWNED,ownMeta:OWNMETA},null,1),'application/json'));
document.getElementById('loadStateBtn').addEventListener('click',()=>document.getElementById('fileState').click());
document.getElementById('scdlBtn').addEventListener('click',()=>document.getElementById('fileScdl').click());
document.getElementById('refreshBtn').addEventListener('click',refresh);
document.getElementById('fileScdl').addEventListener('change',e=>{const f=e.target.files[0];if(!f)return;const rd=new FileReader();rd.onload=()=>{try{importScdl(JSON.parse(rd.result));}catch(err){toast(t('scdlErr'));}};rd.readAsText(f);e.target.value='';});
document.getElementById('fileState').addEventListener('change',e=>{const f=e.target.files[0];if(!f)return;const rd=new FileReader();rd.onload=()=>{try{const o=JSON.parse(rd.result);SEL=o.sel||{};STOCK=o.stock||{};if(o.owned){OWNED=o.owned;OWNMETA=o.ownMeta||{ts:'',matched:Object.keys(OWNED).length,unmatched:[]};fOwned.disabled=false;}save(LS.sel,SEL);save(LS.stock,STOCK);save(LS.owned,OWNED);save(LS.ownMeta,OWNMETA);renderRes();renderList();renderSel();renderMats();toast(t('stateOk'));}catch(err){toast(t('stateErr'));}};rd.readAsText(f);e.target.value='';});

document.getElementById('langBtn').addEventListener('click',e=>{
  const lb=e.target.closest('[data-lang]'); if(!lb||lb.dataset.lang===LANG) return;
  LANG=lb.dataset.lang; save(LS.lang,LANG);
  root.setAttribute('data-lang',LANG); root.setAttribute('lang',LANG);
  applyI18n();buildClassFilter();renderRes();renderList();renderSel();renderMats();
});
document.getElementById('themeBtn').addEventListener('click',()=>{
  const next=root.getAttribute('data-theme')==='dark'?'light':'dark';
  root.setAttribute('data-theme',next);save(LS.theme,next);
});
// Translate all elements marked with data-i18n.
function applyI18n(){document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});}

/* ---------- Tabs on narrow screens (catalog first) ---------- */
window.BP_TABS=scPanels(document.getElementById('bpTabs'),[
  {key:'kat',label:'<span class="de">Katalog</span><span class="en">Catalog</span>',els:[document.getElementById('cardCat')]},
  {key:'list',label:'<span class="de">Beschaffung</span><span class="en">Procurement</span>',els:[document.getElementById('cardList')]},
  {key:'res',label:'<span class="de">Bestand</span><span class="en">Stock</span>',els:[document.getElementById('cardRes')]}],'kat');
/* ---------- init ---------- */
(function init(){
  const th=load(LS.theme); if(th)root.setAttribute('data-theme',th);
  root.setAttribute('data-lang',LANG); root.setAttribute('lang',LANG);
  ingest(RAW);
  if(OWNMETA!==null)fOwned.disabled=false;
  applyI18n();buildClassFilter();renderRes();renderList();renderSel();renderMats();
})();
/*FH_JS*/
</script>
<!--FH_DIALOG-->
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
