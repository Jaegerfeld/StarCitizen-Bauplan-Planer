"""Gemeinsame Kopfzeile und „Was ist neu?“-Dialog der SC-Tools.

Diese Datei ist in allen vier Repos IDENTISCH (StarCitizen-Bauplan-Planer, -Wikelo-Planer,
-Handels-Planer, -Screenshot-Auswerter). Änderungen immer in alle vier übernehmen –
sonst laufen die Kopfzeilen wieder auseinander.

Aufbau (fest): Warnstreifen (Seite) · Kicker · Titel + Version · Einzeiler · Aktionszeile ·
Navigationszeile · Datenzeile. Aktionszeile immer: Sprache, Hell/Dunkel, „Was ist neu?“,
Tool-Aktionen, „Neuesten Stand laden“. Navigationszeile immer dieselben Ziele in derselben
Reihenfolge (das aktuelle Tool fehlt). Der Changelog-Text kommt aus CHANGELOG.md des Repos,
wird beim Bauen eingebacken (funktioniert offline) und verlinkt die Datei auf GitHub.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

KIT_VERSION = "1"

# (Schlüssel, Name DE, Name EN, Online-URL, Symbol) – Reihenfolge = Navigationsreihenfolge
TOOLS = [
    ("bauplan", "Bauplan-Planer", "Blueprint Planner",
     "https://jaegerfeld.github.io/StarCitizen-Bauplan-Planer/", "🛠️"),
    ("wikelo", "Wikelo-Planer", "Wikelo Planner",
     "https://jaegerfeld.github.io/StarCitizen-Wikelo-Planer/", "🧮"),
    ("handel", "Handels-Planer", "Trade Planner",
     "https://jaegerfeld.github.io/StarCitizen-Handels-Planer/", "📈"),
    ("auswerter", "Screenshot-Auswerter", "Screenshot Reader",
     "https://jaegerfeld.github.io/StarCitizen-Screenshot-Auswerter/", "📷"),
    ("guides", "Guides-Übersicht", "Guides overview", "https://jaegerfeld.github.io/sc-guides/", "📚"),
]
REPOS = {
    "bauplan": "https://github.com/Jaegerfeld/StarCitizen-Bauplan-Planer",
    "wikelo": "https://github.com/Jaegerfeld/StarCitizen-Wikelo-Planer",
    "handel": "https://github.com/Jaegerfeld/StarCitizen-Handels-Planer",
    "auswerter": "https://github.com/Jaegerfeld/StarCitizen-Screenshot-Auswerter",
}


def bi(de: str, en: str) -> str:
    """Zweisprachiger Text (fh-de / fh-en, umgeschaltet über <html lang|data-lang>)."""
    return f'<span class="fh-de">{de}</span><span class="fh-en">{en}</span>'


def lang_seg(seg_id: str = "langBtn") -> str:
    """Sprachumschalter DE | EN; die aktive Sprache steht über aria-pressed fest."""
    return (f'<div class="fh-seg" id="{seg_id}" role="group" aria-label="Sprache / Language">'
            '<button type="button" data-lang="de">DE</button>'
            '<button type="button" data-lang="en">EN</button></div>')


def theme_btn() -> str:
    return f'<button class="btn fh-btn" id="themeBtn" type="button">{bi("Hell / Dunkel", "Light / Dark")}</button>'


def news_btn() -> str:
    return (f'<button class="btn fh-btn" id="fhNews" type="button" aria-haspopup="dialog">'
            f'🆕 {bi("Was ist neu?", "What’s new?")}</button>')


def header_html(tool: str, eyebrow: tuple[str, str], title: tuple[str, str], lede: tuple[str, str],
                version: str, actions: str = "", refresh: str = "", data: str = "",
                theme: bool = True, lang: str | None = None) -> str:
    """Kopfzeile nach festem Aufbau. `actions` = Tool-Aktionen (Knöpfe mit class "btn fh-btn"),
    `refresh` = „Neuesten Stand laden“-Knopf, `data` = Inhalt der Datenzeile (darf ids tragen)."""
    nav = "".join(
        f'<a href="{url}" target="_blank" rel="noopener"><span aria-hidden="true">{ico}</span> '
        f'{bi(de, en)}<span class="fh-ext" aria-hidden="true">↗</span></a>'
        for key, de, en, url, ico in TOOLS if key != tool)
    return f"""<header class="fh">
  <p class="fh-eyebrow">{bi(*eyebrow)}</p>
  <h1 class="fh-title">{bi(*title)} <span class="fh-ver" title="Version">v{html.escape(version)}</span></h1>
  <p class="fh-lede">{bi(*lede)}</p>
  <div class="fh-actions">
    {lang or lang_seg()}
    {theme_btn() if theme else ""}
    {news_btn()}
    {actions}
    {refresh}
  </div>
  <nav class="fh-nav" aria-label="Weitere Tools"><span class="fh-navlbl">{bi("Weitere Tools", "More tools")}</span>{nav}</nav>
  <p class="fh-data">{data}</p>
</header>"""


def dialog_html(tool: str, version: str) -> str:
    """„Was ist neu?“-Dialog (gefüllt per JS aus dem eingebackenen CHANGELOG.md)."""
    gh = REPOS.get(tool, "https://github.com/Jaegerfeld") + "/blob/main/CHANGELOG.md"
    return f"""<div class="fh-modal" id="fhCl" hidden>
  <div class="fh-dlg" role="dialog" aria-modal="true" aria-labelledby="fhClT">
    <div class="fh-dhead"><b id="fhClT">{bi("Was ist neu?", "What’s new?")} <span class="fh-ver">v{html.escape(version)}</span></b>
      <button class="fh-x" id="fhClX" type="button" aria-label="Schließen / Close">✕</button></div>
    <p class="fh-ennote fh-en">The changelog is kept in German only.</p>
    <div class="fh-dbody" id="fhClBody"></div>
    <div class="fh-dfoot"><a href="{gh}" target="_blank" rel="noopener">{bi("Vollständiges Changelog auf GitHub", "Full changelog on GitHub")} ↗</a></div>
  </div>
</div>"""


def changelog_json(path: Path) -> str:
    """CHANGELOG.md als JSON-String für <script type="application/json"> (</ entschärft)."""
    md = path.read_text(encoding="utf-8") if path.exists() else ""
    return json.dumps(md, ensure_ascii=False).replace("</", "<\\/")


def changelog_script(path: Path) -> str:
    return f'<script id="fhClMd" type="application/json">{changelog_json(path)}</script>'


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;800&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">')

CSS = r"""
/* ===== Gemeinsame Kopfzeile (kopfzeile.py, in allen vier Tools identisch) ===== */
.fh,.fh-modal{--fh-ink:#e8edf4;--fh-muted:#8b97a8;--fh-line:#243040;--fh-panel:#121822;--fh-panel2:#0e131c;--fh-accent:#3fd0dd;--fh-accent2:#f0a94a;--fh-on:#0a0e14;--fh-disp:'Exo 2',system-ui,sans-serif;--fh-body:'Rajdhani',system-ui,sans-serif}
[data-theme="light"] .fh,[data-theme="light"] .fh-modal{--fh-ink:#141922;--fh-muted:#5a6472;--fh-line:#d5dbe3;--fh-panel:#ffffff;--fh-panel2:#eef1f5;--fh-accent:#0e7c86;--fh-accent2:#a8661a;--fh-on:#ffffff}
.fh-en{display:none}
html[lang="en"] .fh-en,html[data-lang="en"] .fh-en{display:inline}
html[lang="en"] .fh-de,html[data-lang="en"] .fh-de{display:none}
html[lang="en"] p.fh-en{display:block}
.fh{padding:22px 0 14px;color:var(--fh-ink);font-family:var(--fh-body)}
.fh .fh-eyebrow{font-family:var(--fh-disp);font-weight:600;letter-spacing:.24em;text-transform:uppercase;color:var(--fh-accent);font-size:11px;margin:0 0 4px}
.fh .fh-title{font-family:var(--fh-disp);font-weight:800;font-size:30px;line-height:1.15;margin:0;color:var(--fh-ink);letter-spacing:.01em}
.fh .fh-ver{font-family:var(--fh-body);font-weight:600;font-size:12px;letter-spacing:.06em;color:var(--fh-muted);border:1px solid var(--fh-line);border-radius:20px;padding:1px 8px;vertical-align:middle;white-space:nowrap}
.fh .fh-lede{margin:8px 0 0;color:var(--fh-muted);font-size:15.5px;line-height:1.4;max-width:900px}
.fh .fh-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:14px}
.fh .fh-btn{font-family:var(--fh-disp);font-weight:600;font-size:13px;letter-spacing:.04em;background:var(--fh-panel);color:var(--fh-ink);border:1px solid var(--fh-line);border-radius:8px;padding:8px 13px;min-height:36px;cursor:pointer;transition:.15s;text-decoration:none;display:inline-flex;align-items:center;gap:4px}
.fh .fh-btn:hover{border-color:var(--fh-accent);color:var(--fh-accent)}
.fh .fh-btn:focus-visible,.fh .fh-seg button:focus-visible,.fh .fh-nav a:focus-visible{outline:2px solid var(--fh-accent);outline-offset:2px}
.fh .fh-btn[disabled]{opacity:.5;cursor:progress}
.fh .fh-seg{display:inline-flex;border:1px solid var(--fh-line);border-radius:8px;overflow:hidden;min-height:36px}
.fh .fh-seg button{font-family:var(--fh-disp);font-weight:600;font-size:13px;letter-spacing:.04em;background:var(--fh-panel);color:var(--fh-muted);border:0;padding:0 13px;cursor:pointer;min-width:44px}
.fh .fh-seg button+button{border-left:1px solid var(--fh-line)}
.fh .fh-seg button[aria-pressed="true"],.fh .fh-seg button.on{background:var(--fh-accent);color:var(--fh-on);font-weight:800}
.fh .fh-nav{display:flex;flex-wrap:wrap;gap:2px 16px;align-items:center;margin-top:10px}
.fh .fh-navlbl{font-family:var(--fh-disp);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--fh-muted);margin-right:2px}
.fh .fh-nav a{font-family:var(--fh-disp);font-weight:600;font-size:13.5px;color:var(--fh-accent2);text-decoration:none;padding:6px 0;min-height:32px;display:inline-flex;align-items:center;gap:5px}
.fh .fh-nav a:hover{text-decoration:underline;text-underline-offset:3px}
.fh .fh-ext{font-size:11px;opacity:.75}
.fh .fh-data{margin:8px 0 0;color:var(--fh-muted);font-size:12.5px;min-height:1em}
.fh-modal{position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:16px}
.fh-modal[hidden]{display:none}
.fh-dlg{background:var(--fh-panel);color:var(--fh-ink);border:1px solid var(--fh-line);border-radius:12px;width:min(760px,96vw);max-height:86vh;display:flex;flex-direction:column;box-shadow:0 10px 40px rgba(0,0,0,.45);font-family:var(--fh-body);font-size:15px}
.fh-dhead{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px 12px 18px;border-bottom:1px solid var(--fh-line);font-family:var(--fh-disp);font-size:17px}
.fh-dhead .fh-ver{font-family:var(--fh-body);font-size:12px;color:var(--fh-muted);border:1px solid var(--fh-line);border-radius:20px;padding:1px 8px;margin-left:6px;font-weight:600}
.fh-x{background:none;border:1px solid var(--fh-line);color:var(--fh-ink);border-radius:8px;width:40px;height:40px;font-size:16px;cursor:pointer}
.fh-x:hover{border-color:var(--fh-accent);color:var(--fh-accent)}
.fh-x:focus-visible{outline:2px solid var(--fh-accent);outline-offset:2px}
.fh-ennote{margin:10px 18px 0;color:var(--fh-muted);font-size:13px}
.fh-dbody{padding:4px 18px 14px;overflow:auto;line-height:1.45}
.fh-dbody h3{font-family:var(--fh-disp);font-size:16px;margin:16px 0 4px;color:var(--fh-accent)}
.fh-dbody h3:first-child{margin-top:10px}
.fh-dbody h4{font-family:var(--fh-disp);font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--fh-muted);margin:10px 0 2px}
.fh-dbody ul{margin:2px 0 6px;padding-left:20px}
.fh-dbody li{margin:2px 0}
.fh-dbody p{margin:4px 0}
.fh-dbody code{font-size:.92em;background:var(--fh-panel2);border:1px solid var(--fh-line);border-radius:4px;padding:0 4px}
.fh-dbody a,.fh-dfoot a{color:var(--fh-accent2)}
.fh-dfoot{padding:10px 18px;border-top:1px solid var(--fh-line);text-align:right;font-size:13.5px}
@media(max-width:600px){.fh .fh-title{font-size:24px}.fh .fh-lede{font-size:14.5px}}
"""

JS = r"""
/* ===== Gemeinsame Kopfzeile (kopfzeile.py, in allen vier Tools identisch) ===== */
(function(){
  const root=document.documentElement;
  // Sprachumschalter: aktive Sprache sichtbar (aria-pressed), folgt <html lang|data-lang>
  function syncLang(){
    const l=(root.getAttribute('data-lang')||root.getAttribute('lang')||'de').slice(0,2);
    document.querySelectorAll('.fh-seg [data-lang]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.lang===l?'true':'false'));
  }
  new MutationObserver(syncLang).observe(root,{attributes:true,attributeFilter:['data-lang','lang']});
  syncLang();
  // „Was ist neu?“: eingebackenes CHANGELOG.md als kleines Markdown rendern.
  // Dialog und Changelog können im HTML hinter diesem Skript stehen -> erst nach dem Parsen verdrahten.
  const md=()=>{try{return JSON.parse(document.getElementById('fhClMd').textContent)||'';}catch(e){return '';}};
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function inline(s){
    let o=esc(s);
    o=o.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');
    o=o.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,(m,t,u)=>`<a href="${u}" target="_blank" rel="noopener">${t}</a>`);
    return o;
  }
  function render(src){
    let h='',ul=false,m,started=false; const close=()=>{if(ul){h+='</ul>';ul=false;}};
    for(const raw of String(src).split(/\r?\n/)){
      const line=raw.replace(/\s+$/,'');
      if(!started){if(/^##\s/.test(line))started=true;else continue;}   // Vorspann (Titel, Format-Hinweis) weglassen
      if(/^\[[^\]]+\]:\s*https?:/.test(line)) continue;
      if(!line.trim()){close();continue;}
      if(/^#\s+/.test(line)){close();continue;}
      if(m=line.match(/^##\s+(.*)/)){close();h+=`<h3>${inline(m[1])}</h3>`;}
      else if(m=line.match(/^###\s+(.*)/)){close();h+=`<h4>${inline(m[1])}</h4>`;}
      else if(m=line.match(/^[-*]\s+(.*)/)){if(!ul){h+='<ul>';ul=true;}h+=`<li>${inline(m[1])}</li>`;}
      else if(ul&&/^\s+\S/.test(raw)){h=h.replace(/<\/li>$/,' '+inline(line.trim())+'</li>');}
      else {close();h+=`<p>${inline(line)}</p>`;}
    }
    close(); return h;
  }
  function wire(){
    const dlg=document.getElementById('fhCl'), btn=document.getElementById('fhNews'), x=document.getElementById('fhClX');
    if(!dlg||!btn) return;
    function open(){document.getElementById('fhClBody').innerHTML=render(md())||'<p>—</p>';dlg.hidden=false;x.focus();}
    function close(){if(dlg.hidden)return;dlg.hidden=true;btn.focus();}
    btn.addEventListener('click',open);
    x.addEventListener('click',close);
    dlg.addEventListener('click',e=>{if(e.target===dlg)close();});
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!dlg.hidden){e.preventDefault();close();}});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',wire); else wire();
})();
"""
