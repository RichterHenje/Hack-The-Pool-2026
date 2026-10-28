import os, re, shutil, zipfile

D = os.path.dirname(os.path.abspath(__file__))
OUT = "C:/Users/ErdoeR/Documents/GitHub/Hack-The-Pool-2026/Kriegsmarine/presentation"
rd = lambda p: open(os.path.join(D, p), encoding="utf-8").read()

CSS = """
  text { font-family: "IBM Plex Sans", "Segoe UI", Arial, sans-serif; }
  .col { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; fill: #586b7c; }
  .src { fill: none; stroke: #9db0bf; stroke-width: 1.5; }
  .step { fill: #dfe9f0; stroke: none; }
  .sep { stroke: #9db0bf; stroke-width: 1; }
  .out { fill: #14283b; }
  .review { fill: none; stroke: #a8680f; stroke-width: 1.5; stroke-dasharray: 6 4; }
  .t { font-size: 13px; font-weight: 600; fill: #14283b; }
  .s { font-size: 11px; font-weight: 400; fill: #586b7c; }
  .t-out { font-size: 13px; font-weight: 600; fill: #f2f5f7; }
  .s-out { font-size: 11px; font-weight: 400; fill: #f2f5f7; opacity: 0.8; }
  .t-rev { font-size: 12px; font-weight: 600; fill: #a8680f; }
  .flow { fill: none; stroke: #14283b; stroke-width: 1.4; }
  .sea { fill: #f2f5f7; }
  .land { fill: #c4d3de; stroke: none; }
  .route { fill: none; stroke: #a8680f; stroke-width: 1.6; stroke-linejoin: round; }
  .dot circle { fill: #14283b; }
  .frame { fill: none; stroke: #14283b; stroke-width: 1.5; }
  .lab { font-size: 13px; fill: #14283b; }
  .val { font-size: 12px; font-weight: 600; fill: #14283b; }
  .tick { font-size: 11px; fill: #586b7c; }
  .bar, .data { fill: #1f5c8a; }
  .empty { fill: #e6edf2; }
  .grid { stroke: #d3dde5; stroke-width: 1; }
  .axis { stroke: #586b7c; stroke-width: 1; }
  .cell { font-size: 12px; font-weight: 600; fill: #14283b; }
  .cellon { font-size: 12px; font-weight: 600; fill: #f2f5f7; }
"""


def wrap(title, w, h, inner, shift=44):
    inner = inner.replace('style="color: var(--ink)"', 'style="color:#14283b"')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h + shift}" width="{w}" height="{h + shift}" role="img">\n'
            f'<title>{title}</title>\n<style>{CSS}</style>\n'
            f'<rect width="{w}" height="{h + shift}" fill="#f2f5f7" />\n'
            f'<text x="20" y="30" style="font-family:Georgia,serif;font-size:20px;font-weight:600;fill:#14283b">{title}</text>\n'
            f'<g transform="translate(0 {shift})">{inner}</g>\n</svg>\n')


def svg_blocks(html):
    return re.findall(r'<svg viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>(.*?)</svg>', html, re.S)


def full_html(src, lang):
    t = src.replace("<main>", '</head>\n<body>\n<main>', 1)
    t = '<!doctype html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<style>body { margin: 0; }</style>\n' % lang + t + "\n</body>\n</html>\n"
    return t


shutil.rmtree(OUT, ignore_errors=True)
for sub in ("html", "svg", "scripts"):
    os.makedirs(os.path.join(OUT, sub))
w = lambda rel, s: open(os.path.join(OUT, rel), "w", encoding="utf-8", newline="\n").write(s)

pages = [
    ("workflow_data-cleaning-and-enrichment", "datenfluss.html", "en", "Workflow: Data Cleaning and Enrichment"),
    ("workflow_interface-team", "interface.html", "en", "Workflow: Interface Team"),
    ("jagdsaetze_tiere", "tiere.html", "de", "Jagdsätze im Tagebuch"),
]
for name, src, lang, title in pages:
    html = rd(src)
    w(f"html/{name}.html", full_html(html, lang))
    blocks = svg_blocks(html)
    if name == "jagdsaetze_tiere":
        parts = [("jagdsaetze_1_tierarten", "Tiernennungen in Jagdsätzen nach Tierart"),
                 ("jagdsaetze_2_zeitverlauf", "Jagdsätze pro Monat"),
                 ("jagdsaetze_3_tierarten_je_monat", "Tiernennungen in Jagdsätzen nach Art und Monat")]
        for (bw, bh, inner), (fn, t) in zip(blocks, parts):
            w(f"svg/{fn}.svg", wrap(t, int(float(bw)), int(float(bh)), inner, shift=48))
    else:
        bw, bh, inner = blocks[0]
        w(f"svg/{name}.svg", wrap(title, int(float(bw)), int(float(bh)), inner))

for f in ("mapgen.py", "tiere.py", "tiere_tpl.html", "build.py", "tpl.html", "make_presentation.py"):
    shutil.copy(os.path.join(D, f), os.path.join(OUT, "scripts", f))
shutil.copy(os.path.join(D, "zip_tokens.css"), os.path.join(OUT, "tokens.css"))
shutil.copy(os.path.join(D, "presentation_readme.md"), os.path.join(OUT, "README.md"))

zp = os.path.join(OUT, "visualisierungen_kaiserin_elisabeth.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for f in files:
            full = os.path.join(root, f)
            if full == zp:
                continue
            z.write(full, os.path.relpath(full, OUT).replace("\\", "/"))
    print(sorted(i.filename for i in z.infolist()))
