import json, sys
P = "C:/Users/ErdoeR/Documents/GitHub/Hack-The-Pool-2026/Kriegsmarine/kaiserin_elisabeth/prototype/"
LON0, LON1, LAT0, LAT1 = 8, 170, -38, 50
W = 300.0
H = W * (LAT1 - LAT0) / (LON1 - LON0)
def px(lon, lat): return ((lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H)

world = json.loads(open(P + "data/world.js", encoding="utf-8").read().split("=", 1)[1].strip().rstrip(";"))
def rings(g):
    if g["type"] == "Polygon": yield from g["coordinates"]
    elif g["type"] == "MultiPolygon":
        for poly in g["coordinates"]: yield from poly
d = []
for f in world["features"]:
    for r in rings(f["geometry"]):
        lons = [p[0] for p in r]; lats = [p[1] for p in r]
        if max(lons) < LON0 or min(lons) > LON1 or max(lats) < LAT0 or min(lats) > LAT1: continue
        pts = []
        for lon, lat in r:
            x, y = px(lon, lat)
            if not pts or abs(x - pts[-1][0]) + abs(y - pts[-1][1]) > 0.7: pts.append((x, y))
        if len(pts) < 3: continue
        d.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
routes = json.load(open(P + "arcgis/ke_routes.geojson", encoding="utf-8"))["features"]
route = next(f for f in routes if f["properties"]["segment"] == "weltreise_1892_93")
rp = " ".join(f"{x:.1f},{y:.1f}" for x, y in (px(*c) for c in route["geometry"]["coordinates"]))
stops = json.load(open(P + "arcgis/ke_stops.geojson", encoding="utf-8"))["features"]
dots = []
for f in stops:
    if f["properties"]["voyage"].startswith("Weltreise Franz Ferdinand"):
        lon, lat = f["geometry"]["coordinates"]
        if LON0 <= lon <= LON1 and LAT0 <= lat <= LAT1:
            x, y = px(lon, lat); dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" />')
MX, MY = 950, 140
svg = (f'<g transform="translate({MX} {MY})"><clipPath id="mapclip"><rect width="{W:.0f}" height="{H:.1f}" /></clipPath>'
       f'<rect class="sea" width="{W:.0f}" height="{H:.1f}" /><g clip-path="url(#mapclip)"><path class="land" d="{"".join(d)}" />'
       f'<polyline class="route" points="{rp}" /><g class="dot">{"".join(dots)}</g></g>'
       f'<rect class="frame" width="{W:.0f}" height="{H:.1f}" /></g>')
open(sys.argv[1], "w", encoding="utf-8").write(svg)
print(len(svg), H, len(dots))
