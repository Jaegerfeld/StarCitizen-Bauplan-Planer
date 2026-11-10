# =============================================================================
# Autor:          Robert Seebauer
# Repository:     https://github.com/Jaegerfeld (identisch in StarCitizen-Bauplan-Planer,
#                 -Wikelo-Planer, -Handels-Planer, -Schiffskauf-Planer und -Screenshot-Auswerter)
# KI-Unterstützung: Erstellt mit Unterstützung von Claude (Anthropic)
# Erstellt:       01.11.2026
# Geändert:       10.11.2026
# Lizenz:         BSD-3-Clause (siehe LICENSE)
#
# Fachliche Funktion:
#   Gemeinsames Design der fünf Star-Citizen-Tools: Farben für Hell und Dunkel,
#   Schriften (Rajdhani für Überschriften, Exo 2 für Text), Grundbausteine
#   (Knöpfe inkl. Haupt- und Löschknopf, Eingabefelder, Fokusrahmen), die
#   Regeln für Touch-Geräte und Handys sowie der Panel-Umschalter, der auf
#   schmalen Bildschirmen Spalten durch Reiter ersetzt.
#
#   Die Datei liegt byte-gleich in allen fünf Repos, genau wie kopfzeile.py;
#   Änderungen immer in alle fünf kopieren (md5 vergleichen). Jedes Tool setzt
#   das CSS als letztes in sein <style>, damit es gegen ältere Tool-Regeln
#   gewinnt, und das JS ans Ende seines Haupt-Skripts. Tool-eigene Farben
#   werden aus diesen Tokens abgeleitet, nicht neu erfunden (Wikelo: --w-*).
#
#   Der Desktop bleibt das Hauptgerät: Unter 920 px Breite erscheinen Reiter,
#   Touch-Regeln hängen am Zeigertyp (pointer: coarse) statt an der Breite,
#   damit auch Tablets 44-px-Treffflächen bekommen. Helles Amber ist auf
#   #96591a abgedunkelt, damit Text auf Hellgrau mindestens 4,5:1 erreicht.
# =============================================================================
"""Shared design tokens, base components, responsive rules and the narrow-screen panel switcher."""
from __future__ import annotations

#: Version of this shared design kit; bump it on every change and copy to all five repos.
DESIGN_VERSION = "2"
#: Breakpoint in px: below it, multi-column tools show tabs instead of columns (phone, tablet portrait).
NARROW = 920

#: Google Fonts link for the shared fonts; replaces each tool's own font link.
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800'
         '&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">')

#: Shared stylesheet; injected last so it wins over older tool rules.
CSS = r"""
/* ===== Shared design (sc_design.py, identical in all five tools) ===== */
/* Colour tokens: :root is the light theme, [data-theme="dark"] the dark one. */
:root{
  --bg:#f4f6f8; --panel:#ffffff; --panel2:#eef1f5; --ink:#141922; --muted:#5a6472;
  --line:#d5dbe3; --accent:#0e7c86; --accent2:#96591a; --ok:#2e8b57; --bad:#b3452f;
  --okbg:#e3f4ea; --oktx:#1d6b42; --okbd:#9fd3b5; --badbg:#fbe9e6; --badtx:#9b3523; --badbd:#e6b0a5;
  --warnbg:rgba(201,130,42,.14); --hover:#e8eef3; --onaccent:#ffffff;
  --glow:rgba(14,124,134,.12); --shadow:0 2px 12px rgba(20,30,40,.08);
  --disp:'Rajdhani',system-ui,sans-serif; --body:'Exo 2',system-ui,sans-serif;
  color-scheme:light;
}
:root[data-theme="dark"]{
  --bg:#0a0e14; --panel:#121822; --panel2:#0e131c; --ink:#e8edf4; --muted:#8b97a8;
  --line:#243040; --accent:#3fd0dd; --accent2:#f0a94a; --ok:#57c98a; --bad:#e8785c;
  --okbg:#123a2d; --oktx:#bff3dd; --okbd:#2b6b52; --badbg:#3a1c1f; --badtx:#ffd0d0; --badbd:#6b2f34;
  --warnbg:rgba(240,169,74,.14); --hover:#17222f; --onaccent:#0a0e14;
  --glow:rgba(63,208,221,.12); --shadow:0 4px 22px rgba(0,0,0,.5);
  color-scheme:dark;
}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.45;-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%}
body{overflow-x:hidden}
.hazard{height:5px;background:repeating-linear-gradient(45deg,var(--accent2) 0 14px,transparent 14px 28px);opacity:.9}
.btn{font-family:var(--disp);font-weight:600;font-size:14px;letter-spacing:.04em;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 14px;min-height:36px;cursor:pointer;transition:.15s}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.pri,.btn.primary,.btn.prim{background:var(--accent);color:var(--onaccent);border-color:var(--accent);font-weight:700}
.btn.pri:hover,.btn.primary:hover,.btn.prim:hover{filter:brightness(1.08);color:var(--onaccent)}
.btn.danger{background:transparent;color:var(--bad);border-color:var(--bad)}
.btn.danger:hover{background:var(--badbg);color:var(--badtx);border-color:var(--bad)}
.btn[disabled]{opacity:.5;cursor:not-allowed}
input[type=text],input[type=search],input[type=number],select{font-family:var(--body);font-size:14px;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 10px;min-height:36px}
input[type=checkbox],input[type=radio]{accent-color:var(--accent);width:16px;height:16px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}

/* Panel switcher: only visible on narrow screens */
.sc-ptabs{display:none}
@media (max-width:919px){
  .sc-ptabs{display:flex;position:sticky;top:0;z-index:30;gap:0;margin:10px 0 12px;background:var(--bg);border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:var(--shadow)}
  .sc-ptabs button{flex:1 1 0;font-family:var(--disp);font-weight:700;font-size:15px;letter-spacing:.03em;background:var(--panel);color:var(--muted);border:0;padding:10px 6px;min-height:46px;cursor:pointer}
  .sc-ptabs button+button{border-left:1px solid var(--line)}
  .sc-ptabs button[aria-selected="true"]{background:var(--accent);color:var(--onaccent)}
  .sc-ptabs .n{display:inline-block;min-width:20px;margin-left:6px;padding:0 6px;border-radius:10px;font-size:12px;background:var(--panel2);color:var(--ink)}
  .sc-ptabs button[aria-selected="true"] .n{background:var(--onaccent);color:var(--accent)}
  .sc-phide{display:none!important}
}

/* Phone: compact header so the content comes first */
@media (max-width:600px){
  .fh{padding:16px 0 8px}
  .fh .fh-lede{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:14px}
  .fh .fh-actions{gap:6px;margin-top:10px}
  .fh .fh-btn{padding:8px 10px}
  .fh .fh-data{font-size:12px}
}
/* "More tools": always open on wide screens with the toggle hidden; collapsible on phones */
.fh .fh-navd>summary{display:none}
@media (max-width:600px){
  .fh .fh-navd>summary{display:inline-flex;align-items:center;gap:6px;list-style:none;cursor:pointer;font-family:var(--fh-disp);font-weight:600;font-size:13px;letter-spacing:.04em;color:var(--fh-accent2);min-height:40px;margin-top:6px}
  .fh .fh-navd>summary::-webkit-details-marker{display:none}
  .fh .fh-navd>summary::after{content:'▾';font-size:12px}
  .fh .fh-navd[open]>summary::after{content:'▴'}
  .fh .fh-navd .fh-nav{margin-top:0}
  .fh .fh-navd .fh-navlbl{display:none}
}

/* Touch devices (phone and tablet): hit targets of at least 44 px */
@media (pointer:coarse){
  .btn,.fh .fh-btn,.fh .fh-seg,.fh .fh-seg button,select,input[type=text],input[type=search],input[type=number]{min-height:44px}
  .fh .fh-nav a,.fh .fh-navd>summary{min-height:44px}
  input[type=checkbox],input[type=radio]{width:22px;height:22px}
  label:has(>input[type=checkbox]),label:has(>input[type=radio]){min-height:44px;display:inline-flex;align-items:center;gap:8px}
  .fh-x{width:44px;height:44px}
}
"""

#: Shared behaviour: the panel switcher and the collapsed "More tools" row on phones.
JS = r"""
/* ===== Shared design (sc_design.py, identical in all five tools) ===== */
// Panel switcher for narrow screens. items: [{key, label (HTML), els:[elements]}], first: key shown first.
// Panels are only hidden by class, never removed from the DOM (tool handlers are bound by id).
// Returns {set(key), count(key, n)} to switch panels and show a badge count on a tab.
function scPanels(bar, items, first){
  if(!bar) return {set(){}, count(){}};
  let cur=first||items[0].key;
  bar.setAttribute('role','tablist');
  bar.innerHTML=items.map(it=>`<button type="button" role="tab" data-k="${it.key}">${it.label}<span class="n" hidden></span></button>`).join('');
  function show(k){
    cur=k;
    items.forEach(it=>it.els.forEach(el=>el&&el.classList.toggle('sc-phide',it.key!==k)));
    bar.querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected',b.dataset.k===k?'true':'false'));
  }
  bar.addEventListener('click',e=>{const b=e.target.closest('button[data-k]'); if(b&&b.dataset.k!==cur){show(b.dataset.k); window.scrollTo({top:bar.offsetTop-4,behavior:'smooth'});}});
  show(cur);
  return {set:show, count(k,n){const s=bar.querySelector(`button[data-k="${k}"] .n`); if(s){s.hidden=!n; s.textContent=n||'';}}};
}
// Start with "More tools" collapsed on phones.
(function(){const d=document.querySelector('.fh-navd'); if(d&&window.matchMedia('(max-width:600px)').matches) d.removeAttribute('open');})();
"""
