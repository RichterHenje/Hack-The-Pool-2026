import json, collections, os, html

SRC = "C:/Users/ErdoeR/Documents/GitHub/Hack-The-Pool-2026/Kriegsmarine/kaiserin_elisabeth/prototype/data/ke_diary.json"
d = json.load(open(SRC, encoding="utf-8"))

FIX = {"K\ufffdnguru": "Känguru", "B\ufffdffel": "Büffel", "B\ufffdr": "Bär", "Schakal/Hy\ufffdne": "Schakal/Hyäne"}
fix = lambda s: FIX.get(s, s)

MONTHS = ["1892-12", "1893-01", "1893-02", "1893-03", "1893-04", "1893-05", "1893-06", "1893-07", "1893-08", "1893-09", "1893-10"]
MLAB = ["Dez", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt"]
kill = collections.Counter()
sp_m = collections.defaultdict(collections.Counter)
sp_tot = collections.Counter()
kill_days = 0
for x in d:
    m = x["date"][:7]
    kill[m] += x["kill_sentences"]
    kill_days += 1 if x["kill_sentences"] else 0
    for a in x["animals_in_kill_sentences"]:
        a = fix(a)
        sp_m[a][m] += 1
        sp_tot[a] += 1
species = [s for s, _ in sorted(sp_tot.items(), key=lambda t: (-t[1], t[0]))]
total_sent = sum(kill.values())
total_ment = sum(sp_tot.values())
print("sentences", total_sent, "days", kill_days, "mentions", total_ment, "species", len(species))

# ---- chart 1: horizontal bars
LW, RH, TOP = 140, 26, 8
W1 = 640
mx = max(sp_tot.values())
sx = (W1 - LW - 50) / mx
h1 = TOP + RH * len(species) + 8
c1 = [f'<svg viewBox="0 0 {W1} {h1}" role="img" aria-label="Genannte Tierarten in Jagdsätzen, nach Häufigkeit">']
for i, s in enumerate(species):
    y = TOP + i * RH
    w = sp_tot[s] * sx
    c1.append(f'<g><title>{html.escape(s)}: {sp_tot[s]} Nennungen</title>'
              f'<text class="lab" x="{LW-10}" y="{y+16}" text-anchor="end">{html.escape(s)}</text>'
              f'<rect class="bar" x="{LW}" y="{y+4}" width="{w:.1f}" height="16" rx="3" />'
              f'<text class="val" x="{LW+w+8:.1f}" y="{y+16}">{sp_tot[s]}</text></g>')
c1.append("</svg>")

# ---- chart 2: columns per month
W2, H2, L2, B2, T2 = 640, 250, 36, 36, 16
ymax = 50
plot_h = H2 - B2 - T2
step = (W2 - L2 - 8) / len(MONTHS)
bw = 30
c2 = [f'<svg viewBox="0 0 {W2} {H2}" role="img" aria-label="Jagdsätze pro Monat, Dezember 1892 bis Oktober 1893">']
for v in (0, 10, 20, 30, 40, 50):
    y = T2 + plot_h - v / ymax * plot_h
    cls = "axis" if v == 0 else "grid"
    c2.append(f'<line class="{cls}" x1="{L2}" x2="{W2-8}" y1="{y:.1f}" y2="{y:.1f}" />'
              f'<text class="tick" x="{L2-6}" y="{y+4:.1f}" text-anchor="end">{v}</text>')
for i, m in enumerate(MONTHS):
    v = kill[m]
    cx = L2 + step * i + step / 2
    h = v / ymax * plot_h
    y = T2 + plot_h - h
    if v:
        c2.append(f'<g><title>{MLAB[i]} {m[:4]}: {v} Sätze</title><rect class="bar" x="{cx-bw/2:.1f}" y="{y:.1f}" width="{bw}" height="{h:.1f}" rx="3" /></g>')
    c2.append(f'<text class="val" x="{cx:.1f}" y="{y-6:.1f}" text-anchor="middle">{v}</text>')
    c2.append(f'<text class="tick" x="{cx:.1f}" y="{H2-14}" text-anchor="middle">{MLAB[i]}</text>')
c2.append("</svg>")

# ---- chart 3: heatmap species x month
CW, CH, GAP = 40, 24, 2
L3, T3 = 140, 26
W3 = L3 + len(MONTHS) * (CW + GAP) + 4
H3 = T3 + len(species) * (CH + GAP) + 4
cmax = max(max(c.values()) for c in sp_m.values())
c3 = [f'<svg viewBox="0 0 {W3} {H3}" role="img" aria-label="Genannte Tierarten pro Monat">']
for i, lab in enumerate(MLAB):
    c3.append(f'<text class="tick" x="{L3+i*(CW+GAP)+CW/2}" y="{T3-10}" text-anchor="middle">{lab}</text>')
for r, s in enumerate(species):
    y = T3 + r * (CH + GAP)
    c3.append(f'<text class="lab" x="{L3-10}" y="{y+16}" text-anchor="end">{html.escape(s)}</text>')
    for i, m in enumerate(MONTHS):
        v = sp_m[s][m]
        x = L3 + i * (CW + GAP)
        if v:
            op = 0.14 + 0.86 * v / cmax
            tcls = "cellon" if op > 0.55 else "cell"
            c3.append(f'<g><title>{html.escape(s)}, {MLAB[i]} {m[:4]}: {v}</title>'
                      f'<rect class="data" x="{x}" y="{y}" width="{CW}" height="{CH}" rx="3" fill-opacity="{op:.2f}" />'
                      f'<text class="{tcls}" x="{x+CW/2}" y="{y+16}" text-anchor="middle">{v}</text></g>')
        else:
            c3.append(f'<rect class="empty" x="{x}" y="{y}" width="{CW}" height="{CH}" rx="3" />')
c3.append("</svg>")

page = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiere_tpl.html"), encoding="utf-8").read()
page = (page.replace("<!--C1-->", "\n".join(c1)).replace("<!--C2-->", "\n".join(c2)).replace("<!--C3-->", "\n".join(c3))
        .replace("{{SENT}}", str(total_sent)).replace("{{DAYS}}", str(kill_days)).replace("{{MENT}}", str(total_ment))
        .replace("{{NSP}}", str(len(species))).replace("{{TOP}}", str(sp_tot[species[0]])))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiere.html"), "w", encoding="utf-8").write(page)
