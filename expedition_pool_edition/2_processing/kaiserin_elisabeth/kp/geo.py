"""Places → coordinates → GeoJSON / CSV for ArcGIS Online, QGIS or Leaflet.

Vendor-neutral on purpose: GeoJSON (RFC 7946, WGS84, [lon, lat]) and CSV with
`latitude`/`longitude` columns import into ArcGIS Online Map Viewer, QGIS and Leaflet.

Three geocoding routes (docs/07_gis.md has their reach):
  1. coordinates already in the Kulturpool graph (GeoNames, Pleiades): chos_with_coords
  2. GND place IRIs via lobid-gnd: gnd_coords
  3. place names via the GeoNames AT dump (offline, deterministic): GeoNamesAT.lookup
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path

import requests

from kp import kulturpool as kpa

WIEN_WFS = "https://data.wien.gv.at/daten/geo"
GEONAMES_AT = "https://download.geonames.org/export/dump/AT.zip"
LOBID = "https://lobid.org/gnd/{id}.json"
ATTRIBUTION = {
    "kulturpool": "Kulturpool (metadata; image rights per record)",
    "wien": "Datenquelle: Stadt Wien – data.wien.gv.at (CC BY 4.0)",
    "geonames": "GeoNames (CC BY 4.0)",
    "gnd": "GND via lobid-gnd (CC0)",
    "pleiades": "Pleiades (CC BY)",
}


# --- GeoJSON basics -------------------------------------------------------------------


def feature(lat: float, lon: float, **props) -> dict:
    """A GeoJSON Point. Takes lat, lon (reading order) and writes [lon, lat] (GeoJSON order)."""
    lat, lon = float(lat), float(lon)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError(f"not WGS84 lat/lon: {lat}, {lon}")
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def collection(features: list[dict], attribution: str = "") -> dict:
    fc = {"type": "FeatureCollection", "features": features}
    if attribution:
        fc["attribution"] = attribution
    return fc


def write_geojson(features: list[dict], path: str | Path, attribution: str = "") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(collection(features, attribution), ensure_ascii=False), encoding="utf-8"
    )
    return path


def write_csv_latlon(features: list[dict], path: str | Path) -> Path:
    """CSV with latitude/longitude columns (ArcGIS Online detects them on upload)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for f in features for k in f["properties"]})
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["latitude", "longitude", *keys])
        for f in features:
            lon, lat = f["geometry"]["coordinates"]
            w.writerow([lat, lon, *(f["properties"].get(k, "") for k in keys)])
    return path


def parse_wkt_point(wkt: str) -> tuple[float, float]:
    """'Point ( +016.371690 +048.208199 )' → (lat, lon). WKT order is x y = lon lat."""
    m = re.search(
        r"Point\s*\(\s*([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s*\)", wkt, re.IGNORECASE
    )
    if not m:
        raise ValueError(f"not a WKT point: {wkt!r}")
    lon, lat = float(m.group(1)), float(m.group(2))
    return lat, lon


# --- Route 1: coordinates already in Kulturpool ---------------------------------------

_PLACES_Q = """
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX wgs84: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX edm: <http://www.europeana.eu/schemas/edm/>
SELECT ?pl (SAMPLE(?label) AS ?name) (SAMPLE(?lat) AS ?la) (SAMPLE(?long) AS ?lo)
       (COUNT(DISTINCT ?cho) AS ?objects) (SAMPLE(?cho) AS ?example)
WHERE {
  %s
  ?cho dcterms:spatial ?pl .
  ?pl wgs84:lat ?lat ; wgs84:long ?long .
  OPTIONAL { ?pl skos:prefLabel ?label }
  %s
}
GROUP BY ?pl ORDER BY DESC(?objects) LIMIT %d
"""


def places_with_coords(dataset: str | None = None, limit: int = 2000) -> list[dict]:
    """One feature per place (not per object): name, object count, one example CHO.
    dataset = a dataset graph name such as "oenb-abo" (see queries/02_one_dataset.rq).
    """
    if dataset:
        head = f"GRAPH <https://id.kulturpool.at/dataset/{dataset}#graph> {{"
        tail = "}"
    else:
        head = tail = ""
    rows = kpa.sparql(_PLACES_Q % (head, tail, limit))
    return [
        feature(
            r["la"],
            r["lo"],
            place=r["pl"],
            name=r.get("name", ""),
            objects=int(r["objects"]),
            example=r["example"],
        )
        for r in rows
    ]


# --- Route 2: GND places via lobid ----------------------------------------------------


def gnd_id(iri_or_id: str) -> str:
    """'http(s)://d-nb.info/gnd/4066009-6' or '4066009-6' → '4066009-6'."""
    return iri_or_id.rstrip("/").rsplit("/", 1)[-1]


def gnd_coords(iri_or_id: str) -> tuple[float, float] | None:
    """(lat, lon) of a GND place from lobid-gnd, or None if it has no geometry."""
    r = requests.get(LOBID.format(id=gnd_id(iri_or_id)), timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    for g in r.json().get("hasGeometry", []):
        for wkt in g.get("asWKT", []):
            return parse_wkt_point(wkt)
    return None


# --- Route 3: place names via the GeoNames AT dump ------------------------------------


def norm(name: str) -> str:
    """Case-, accent- and whitespace-insensitive key. 'Wien ' and 'wien' match; ß stays ß→ss."""
    s = unicodedata.normalize("NFKD", name.casefold().replace("ß", "ss"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()


GEONAMES_WORLD = "https://download.geonames.org/export/dump/cities15000.zip"

# Values that mean "no place". Seen in Kulturpool 2026-10-27: "o.O." (33,448), "unbekannt" (6,385).
PLACEHOLDERS = {
    "o.o.",
    "o. o.",
    "o.o",
    "s.l.",
    "s. l.",
    "ohne ort",
    "unbekannt",
    "unknown",
    "n.a.",
    "n/a",
    "k.a.",
    "-",
    "?",
    "",
}


def is_placeholder(name: str) -> bool:
    return norm(name.strip("[]() ")) in PLACEHOLDERS


def name_parts(name: str) -> list[str]:
    """Candidate strings to look up, most literal first: the cleaned whole, then its parts.

    '[Wien]' → ['Wien']; 'Wien, Künstlerhaus' → [whole, 'Wien', 'Künstlerhaus'];
    'AUT / BL Oberösterreich / PB Linz' → [whole, 'PB Linz', 'BL Oberösterreich', 'AUT']
    (slash hierarchies run broad → narrow, so their parts are tried narrowest first).
    Historic names with a stated modern name try the modern one first:
    'Batavia (heut. Jakarta, Indonesien)' → ['Jakarta', 'Batavia', …]
    ("Batavia" alone would also match Batavia, New York).
    """
    modern = [
        m.strip() for m in re.findall(r"\bheut(?:e|ig|\.)?\s+([^,;()\]]+)", name, re.IGNORECASE)
    ]
    base = re.split(r"[(\[]", name, maxsplit=1)[0].strip(" ,")
    s = re.sub(r"[\[\]()?]", "", name).strip()
    out = [*modern, base, s] if (modern or base != s) else [s]
    if base != s:
        out += [p.strip() for p in base.split(",")]
        for inner in re.findall(r"\(([^)]*)\)", name):
            out += [p.strip() for p in inner.split(",")]
    if "/" in s:
        out += [p.strip() for p in reversed(s.split("/"))]
    for sep in (",", "|", ";"):
        if sep in s:
            out += [p.strip() for p in s.split(sep)]
    return [p for i, p in enumerate(out) if p and p not in out[:i]]


def historic_names(name: str) -> list[str]:
    """Period names stated in a place string: 'Qingdao (hist. Tsingtau)' → ['Tsingtau'];
    'Batavia (heut. Jakarta, …)' → ['Batavia'] (the name before a stated modern one)."""
    out = [m.strip() for m in re.findall(r"\bhist\.\s*([^,;()\]]+)", name, re.IGNORECASE)]
    if re.search(r"\bheut", name, re.IGNORECASE):
        out.append(re.split(r"[(\[,]", name, maxsplit=1)[0].strip())
    return [n for n in dict.fromkeys(out) if n]


# Country names (German, English, historic) → ISO code, for country hints in place strings.
COUNTRIES = {
    "osterreich": "AT",
    "austria": "AT",
    "deutschland": "DE",
    "germany": "DE",
    "italien": "IT",
    "italy": "IT",
    "schweiz": "CH",
    "frankreich": "FR",
    "france": "FR",
    "england": "GB",
    "grossbritannien": "GB",
    "kroatien": "HR",
    "istrien": "HR",
    "slowenien": "SI",
    "ungarn": "HU",
    "tschechien": "CZ",
    "bohmen": "CZ",
    "polen": "PL",
    "indien": "IN",
    "india": "IN",
    "british raj": "IN",
    "sri lanka": "LK",
    "ceylon": "LK",
    "nepal": "NP",
    "jemen": "YE",
    "yemen": "YE",
    "indonesien": "ID",
    "indonesia": "ID",
    "japan": "JP",
    "china": "CN",
    "agypten": "EG",
    "egypt": "EG",
    "usa": "US",
    "vereinigte staaten": "US",
    "kanada": "CA",
    "canada": "CA",
    "australien": "AU",
    "australia": "AU",
    "singapur": "SG",
    "singapore": "SG",
    "hong kong": "HK",
    "hongkong": "HK",
    "macau": "MO",
    "thailand": "TH",
    "siam": "TH",
    "birma": "MM",
    "burma": "MM",
    "myanmar": "MM",
    "pakistan": "PK",
    "turkei": "TR",
    "griechenland": "GR",
    "brasilien": "BR",
    "brazil": "BR",
    "mexiko": "MX",
    "russland": "RU",
    "neuseeland": "NZ",
}


def country_hints(name: str) -> set[str]:
    """ISO codes of countries named anywhere in a place string."""
    s = norm(name)
    return {iso for c, iso in COUNTRIES.items() if re.search(rf"\b{re.escape(c)}\b", s)}


class Gazetteer:
    """Offline gazetteer from GeoNames dumps (CC BY 4.0): Austria in full (AT.zip, ~53k
    names) plus world cities over 15,000 inhabitants (cities15000.zip) for places abroad.

    lookup() prefers, in order: populated places (class P) over admin areas (class A),
    Austrian over foreign, larger over smaller. Ambiguity is reported, not hidden.
    """

    def __init__(self, cache_dir: str | Path = "data/geonames", world: bool = True):
        self.index: dict[str, list[dict]] = {}
        urls = [GEONAMES_AT] + ([GEONAMES_WORLD] if world else [])
        for url in urls:
            path = Path(cache_dir) / url.rsplit("/", 1)[-1]
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                r = requests.get(url, timeout=180)
                r.raise_for_status()
                path.write_bytes(r.content)
            self._load(path)

    def _load(self, path: Path) -> None:
        with zipfile.ZipFile(path) as z, z.open(path.stem + ".txt") as fh:
            for line in io.TextIOWrapper(fh, encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                if len(c) < 15 or c[6] not in ("P", "A"):
                    continue
                rec = {
                    "geonameid": c[0],
                    "name": c[1],
                    "lat": float(c[4]),
                    "lon": float(c[5]),
                    "fclass": c[6],
                    "fcode": c[7],
                    "country": c[8],
                    "population": int(c[14] or 0),
                }
                for n in {c[1], c[2], *c[3].split(",")}:
                    if n:
                        self.index.setdefault(norm(n), []).append(rec)

    def lookup(self, name: str, countries: set[str] | None = None) -> dict | None:
        """Best match for a place string, or None (also for placeholders).

        Adds: 'matched' (the part that matched), 'candidates' (distinct places with that
        name), 'ambiguous' (more than one), 'geonames' (IRI, comparable with Kulturpool's).
        If the string names a country ('Beli, Nepal'), only places in that country count:
        better no match than Bury, England. `countries` does the same from context the
        caller knows (e.g. the stretch of an itinerary a dated entry belongs to).
        """
        if is_placeholder(name):
            return None
        hints = country_hints(name) or set(countries or ())
        for part in name_parts(name):
            cands = {c["geonameid"]: c for c in self.index.get(norm(part), [])}.values()
            if norm(part) in COUNTRIES:
                # A country name is not a point, except for city-states (Singapur,
                # Hong Kong): keep only the capital of that same country.
                iso = COUNTRIES[norm(part)]
                cands = [c for c in cands if c["fcode"] == "PPLC" and c["country"] == iso]
            elif hints:
                cands = [c for c in cands if c["country"] in hints]
            if cands:
                best = max(
                    cands, key=lambda c: (c["fclass"] == "P", c["country"] == "AT", c["population"])
                )
                return {
                    **best,
                    "matched": part,
                    "candidates": len(cands),
                    "ambiguous": len(cands) > 1,
                    "geonames": f"https://sws.geonames.org/{best['geonameid']}/",
                }
        return None


GeoNamesAT = Gazetteer  # earlier name


# --- Other layers ---------------------------------------------------------------------


def institutions() -> list[dict]:
    """Kulturpool institutions that carry a location (MultiPoint; first point used)."""
    out = []
    data = requests.get(f"{kpa.API}/institutions", timeout=60).json()
    for i in data.get("data", []) if isinstance(data, dict) else data:
        loc = i.get("location") or {}
        pts = loc.get("coordinates") or []
        if pts:
            lon, lat = pts[0]
            out.append(
                feature(lat, lon, id=i.get("id"), name=i.get("name") or i.get("title") or "")
            )
    return out


def wien_wfs(layer: str, count: int = 1000) -> list[dict]:
    """GeoJSON features of a Stadt Wien WFS layer (e.g. KULTURWIKIOGD, KUNSTWERKOGD,
    MUSEUMOGD) in WGS84. The service's native CRS is not WGS84, hence srsName.
    """
    params = {
        "service": "WFS",
        "request": "GetFeature",
        "version": "1.1.0",
        "typeName": f"ogdwien:{layer}",
        "srsName": "EPSG:4326",
        "outputFormat": "json",
        "maxFeatures": count,
    }
    r = requests.get(WIEN_WFS, params=params, timeout=120)
    r.raise_for_status()
    return r.json()["features"]
