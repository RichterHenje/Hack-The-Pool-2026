"""
Hinweis: Die maßgebliche Auswahl erzeugt filter_voyage_ff.py (andere Personenauswahl, schreibt
json/*.json). Dieses Skript ist dessen Basis-Modul; direkt aufgerufen schreibt es die ältere
Personenauswahl in dieselben Dateien.

Filtert aus dem Obsidian-Vault "Archive_Indien_Schiffreisen" alle Einträge, die mit der
"Weltreise Erzherzog Franz Ferdinand von Österreich-Este (1892-1893)" auf dem
Kreuzer "Kaiserin Elisabeth" verbunden sind, und schreibt sie als JSON-Dateien,
deren Objektstruktur den 0_Muster_*-Dateien des Vaults folgt.

Auswahlkriterien
- Ortschaften: Links unter "#Route" im Weltreise-Eintrag, bis
  "Ab Hier mit einem anderen Passagierschiff" (danach anderes Schiff).
- Personen: "Seereise-Denkmünze" im *Wert* des Feldes "Auszeichnung"
  (der Vorlagen-Hinweis "Auszeichnung (z. B. Seereise-Denkmünze ...)" zählt nicht),
  sowie die im Weltreise-Eintrag namentlich genannte Besatzung (Kapitän, Fotograf, ...),
  sowie Personen, deren Feld "Schiff" die "Kaiserin Elisabeth" verlinkt, ohne dass dort
  (Wert oder Unterpunkte wie "Rolle") ein Datum steht: datierte Einträge stammen aus den
  Ranglisten nach der Reise, undatierte Einträge bezeichnen Personen an Bord der Weltreise.
  Notizen ohne Feld "Schiff" zählen ebenso, wenn eine Zeile ohne Jahr das Schiff verlinkt.
- Schiff: "Kaiserin Elisabeth, Kreuzer" (nur die Reise der Weltreise).
- Sammlungen: Einträge, die auf die Weltreise, eine Routen-Ortschaft oder
  eine Weltreise-Person verlinken.
- Firmen/Dienstleister/Institutionen werden nicht berücksichtigt: ein Link auf eine
  Routen-Ortschaft belegt keinen Bezug zu genau dieser Reise.

Werte, die im jeweiligen Eintrag nicht vorhanden sind, erhalten "NA".

Aufruf:  python filter_voyage.py [--vault PFAD] [--out PFAD]
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

NA = "NA"

HERE = Path(__file__).resolve().parent
DEFAULT_VAULT = HERE.parent / "Vault" / "Archive_Indien_Schiffreisen"
DEFAULT_OUT = HERE / "json"

VOYAGE_TITLE = "Weltreise Erzherzog Franz Ferdinand von Österreich-Este (1892-1893)"
SHIP_TITLE = "Kaiserin Elisabeth, Kreuzer"
ROUTE_START = "#Route"
ROUTE_END = "Ab Hier mit einem anderen Passagierschiff"
MEDAL = "Seereise-Denkmünze"

FOLDERS = {
    "person": "Personen",
    "place": "Ortschaften",
    "ship": "Schiffe",
    "organisation": "Firmen_Dienstleister_Institutionen",
    "collection": "Sammlungen_Projekte",
}

WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")
URL_RE = re.compile(r"https?://[^\s\)\]>]+")
TAG_RE = re.compile(r"(?<![\w/&])#([^\s#\[\],:]+)")
BULLET_RE = re.compile(r"^(?P<indent>\s*)-\s?(?P<text>.*)$")


# --------------------------------------------------------------------------- helpers

def norm(name):
    """Normalisierter Schlüssel für Link-Ziele / Dateinamen."""
    name = unicodedata.normalize("NFC", name)
    return re.sub(r"\s+", " ", name).strip().casefold()


def link_target(raw):
    """[[Ziel#Abschnitt|Alias]] -> Ziel"""
    return re.split(r"[|#]", raw, maxsplit=1)[0].strip()


def links_in(text):
    return [link_target(m) for m in WIKILINK_RE.findall(text)]


def strip_links(text):
    """Wikilinks im Fließtext durch ihren Anzeigetext ersetzen."""
    def repl(m):
        parts = m.group(1).split("|", 1)
        return (parts[1] if len(parts) == 2 else parts[0]).strip()
    return WIKILINK_RE.sub(repl, text).strip()


def unique(seq):
    seen, out = set(), []
    for x in seq:
        k = norm(x) if isinstance(x, str) else json.dumps(x, sort_keys=True)
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


def na(value):
    """Leere Werte -> "NA" (rekursiv für Listen/Dicts)."""
    if isinstance(value, dict):
        return {k: na(v) for k, v in value.items()}
    if isinstance(value, list):
        value = [na(v) for v in value if v not in (None, "", [], {})]
        return value if value else NA
    if value is None or (isinstance(value, str) and not value.strip()):
        return NA
    return value


# --------------------------------------------------------------------------- vault

class Note:
    def __init__(self, path, vault):
        self.path = path
        self.rel = path.relative_to(vault).as_posix()
        self.title = unicodedata.normalize("NFC", path.stem)
        self.folder = path.parent.name if path.parent != vault else ""
        text = path.read_text(encoding="utf-8-sig")
        self.meta, self.body = parse_frontmatter(text)
        self.lines = self.body.splitlines()
        self.links = links_in(self.body)


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta, key = {}, None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[i + 1:])
        item = re.match(r"^\s+-\s*(.*)$", line)
        if item and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(item.group(1).strip().strip('"'))
            continue
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            meta[key] = {"true": True, "false": False}.get(val, val)
    return {}, text


class Vault:
    def __init__(self, root):
        self.root = root
        self.notes = [Note(p, root) for p in sorted(root.rglob("*.md"))
                      if ".obsidian" not in p.parts and not p.name.startswith("0_Muster")]
        self.by_name = {norm(n.title): n for n in self.notes}

    def get(self, name):
        return self.by_name.get(norm(name))

    def folder_of(self, name):
        n = self.get(name)
        return n.folder if n else None


# --------------------------------------------------------------------------- body parsing

def parse_fields(note):
    """
    Zerlegt den Body in Feld-Blöcke:
      [{"label": str|None, "value": str, "children": [{"label","value"}...], "raw": str}]
    "- Label: Wert" -> label/value; "- Label (Hinweis)" ohne Doppelpunkt -> label, value "";
    Zeilen ohne Aufzählungszeichen -> eigener Block ohne Label (Freitext);
    eingerückte Unterpunkte und Fortsetzungszeilen hängen am vorherigen Block.
    """
    blocks = []
    for line in note.lines:
        if not line.strip():
            continue
        m = BULLET_RE.match(line)
        indented = bool(re.match(r"^\s+", line))
        if m and not indented:
            label, value = split_label(m.group("text"))
            blocks.append({"label": label, "value": value, "children": [], "raw": m.group("text")})
        elif indented and blocks:
            text = m.group("text") if m else line.strip()
            text = re.sub(r"^-\s*", "", text.strip())  # "- - Rolle"
            label, value = split_label(text)
            blocks[-1]["children"].append({"label": label, "value": value, "raw": text})
        else:
            blocks.append({"label": None, "value": line.strip(), "children": [], "raw": line.strip()})
    return blocks


def split_label(text):
    """Trennt "Label (Hinweis): Wert" in (Label, Wert). Ohne Label -> (None, text)."""
    text = text.strip()
    m = re.match(r"^([A-Za-zÄÖÜäöüß/ .\-]+?)\s*(\([^)]*\))?\s*:\s*(.*)$", text)
    if m and not m.group(1).lower().startswith("http") and len(m.group(1)) <= 60:
        return m.group(1).strip(), m.group(3).strip()
    m = re.match(r"^([A-Za-zÄÖÜäöüß/ ,.\-]+?)\s*(\([^)]*\))?\s*$", text)
    if m and "[[" not in text:
        return m.group(1).strip(), ""
    return None, text


def find(blocks, *prefixes):
    """Alle Blöcke, deren Label mit einem der Präfixe beginnt (case-insensitive)."""
    pre = [p.lower() for p in prefixes]
    return [b for b in blocks if b["label"] and any(b["label"].lower().startswith(p) for p in pre)]


def first_value(blocks, *prefixes):
    for b in find(blocks, *prefixes):
        if b["value"]:
            return strip_links(b["value"])
    return NA


def all_values(blocks, *prefixes):
    return [strip_links(b["value"]) for b in find(blocks, *prefixes) if b["value"]]


def classify_links(vault, links):
    out = {k: [] for k in FOLDERS}
    out["unresolved"] = []
    for l in links:
        if norm(l) == norm(VOYAGE_TITLE):  # liegt unter Personen/, ist aber keine Person
            continue
        folder = vault.folder_of(l)
        kind = next((k for k, f in FOLDERS.items() if f == folder), None)
        out[kind or "unresolved"].append(l)
    return {k: unique(v) for k, v in out.items()}


def urls_in(text):
    return [u.rstrip(".,;") for u in URL_RE.findall(text)]


def url_kind(url):
    u = url.lower()
    if "geonames.org" in u:
        return "geonames"
    if "d-nb.info/gnd" in u or "/gnd/" in u:
        return "gnd"
    if "viaf.org" in u:
        return "viaf"
    if "goobi" in u:
        return "goobi"
    if "wikidata.org" in u:
        return "wikidata"
    return "other"


def ids_from(texts, kind):
    return unique([u for t in texts for u in urls_in(t) if url_kind(u) == kind])


def only_links(text):
    """True, wenn die Zeile nur aus Wikilinks/URLs (und Trennzeichen) besteht."""
    rest = URL_RE.sub("", WIKILINK_RE.sub("", text))
    return not re.sub(r"[\s,;\-–()]+", "", rest)


def free_text(blocks, known_labels):
    """
    Unbeschriftete Zeilen und unbekannte Labels mit Inhalt -> Freitext.
    Reine Link-/URL-Zeilen werden übersprungen, da sie bereits in den Link-Feldern stehen.
    """
    known = [k.lower() for k in known_labels]
    out = []
    for b in blocks:
        if b["label"] is None or not any(b["label"].lower().startswith(k) for k in known):
            if b["label"] is None or b["value"]:
                out.append(b["raw"])
            out += [c["raw"] for c in b["children"]]
    return [strip_links(t) for t in out if t and not only_links(t)]


def meta_of(note, reasons):
    m = note.meta
    return {
        "datei": note.rel,
        "id": m.get("id", NA),
        "typ": m.get("type", NA),
        "created_by": m.get("created_by", NA),
        "checked": m.get("checked", NA),
        "review": m.get("review", NA),
        "auswahlgrund": reasons,
    }


# --------------------------------------------------------------------------- voyage

def parse_voyage(vault):
    note = vault.get(VOYAGE_TITLE)
    if note is None:
        raise SystemExit(f"Weltreise-Eintrag nicht gefunden: {VOYAGE_TITLE}")
    body = note.body
    start = body.find(ROUTE_START)
    end = body.find(ROUTE_END)
    if start < 0 or end < 0:
        raise SystemExit("Route-Markierungen im Weltreise-Eintrag nicht gefunden.")
    route = links_in(body[start:end])
    other_ship_route = links_in(body[end:].split("\n\n")[0])

    # Besatzung aus dem Kopfteil: "Rolle: [[Name]]"
    crew = []
    for line in body[:start].splitlines():
        m = re.match(r"^\s*([^:\[]+?)\s*:\s*(.*\[\[.*)$", line)
        if m:
            for name in links_in(m.group(2)):
                crew.append({"name": name, "rolle": m.group(1).strip()})

    intro = [l.strip() for l in body[:start].splitlines() if l.strip() and "[[" not in l]
    return note, route, other_ship_route, crew, intro


# --------------------------------------------------------------------------- builders

PERSON_LABELS = ["Nachname", "Titel", "Lebensdaten", "Beruf", "Auszeichnung", "GND", "VIAF",
                 "Wikidata", "Lexikon", "Schiff", "Ortschaft", "Länderbezug", "Archivalien",
                 "Goobi", "Weitere Informationen", "Links zu Bezugspersonen", "Literatur", "Quelle"]


def has_medal(note):
    return any(MEDAL in b["value"] for b in find(parse_fields(note), "Auszeichnung"))


def undated_ship(note):
    """Feld "Schiff" verlinkt die Kaiserin Elisabeth, weder Wert noch Unterpunkte nennen ein Jahr."""
    for b in find(parse_fields(note), "Schiff"):
        if any(norm(l) == norm(SHIP_TITLE) for l in links_in(b["value"])):
            texts = [b["value"]] + [c["raw"] for c in b["children"]]
            if not any(re.search(r"\b1[89]\d\d\b", t) for t in texts):
                return True
    return False


def undated_ship_link(note):
    """Ohne Feld "Schiff": eine Zeile verlinkt die Kaiserin Elisabeth und nennt kein Jahr."""
    if any(norm(l) == norm(SHIP_TITLE) for b in find(parse_fields(note), "Schiff") for l in links_in(b["value"])):
        return False
    return any(not re.search(r"\b1[89]\d\d\b", line) for line in note.lines
               if any(norm(l) == norm(SHIP_TITLE) for l in links_in(line)))


def build_person(vault, note, reasons, voyage_roles=None, name=None):
    if note is None:  # Person ohne eigenen Eintrag im Vault
        obj = {k: NA for k in ["Nachname, Vorname", "Titel", "Lebensdaten", "Beruf/Funktionen",
                               "Auszeichnung", "GND", "VIAF", "Lexikonbeitrag", "Schiff",
                               "Ortschaft", "Länderbezug", "Archivalien mit Signatur",
                               "Goobi-Link zu den Archivalien",
                               "Weitere Informationen mit Sammlungsbezug",
                               "Links zu Bezugspersonen", "Literatur", "Quellen", "Freitext"]}
        obj["Nachname, Vorname"] = name
        obj["Rolle auf der Weltreise"] = na(voyage_roles)
        obj["_meta"] = {"datei": NA, "id": NA, "typ": NA, "created_by": NA, "checked": NA,
                        "review": NA, "auswahlgrund": reasons}
        return obj

    blocks = parse_fields(note)
    links = classify_links(vault, note.links)
    all_text = [note.body]

    # Auszeichnungen + Quellen
    medals, sources = [], []
    for b in find(blocks, "Auszeichnung"):
        if b["value"]:
            medals += [m.strip() for m in strip_links(b["value"]).split(",") if m.strip()]
        sources += [c["value"] for c in b["children"] if (c["label"] or "").lower() == "quelle"]
    for b in find(blocks, "Quelle"):
        sources += [b["value"]] + [c["raw"] for c in b["children"]]
    sources = unique([s for s in sources if s])

    # Schiffe mit Rollen
    ships = []
    for b in find(blocks, "Schiff"):
        ship_links = links_in(b["value"]) or ([strip_links(b["value"])] if b["value"] else [])
        roles = [strip_links(c["value"]) for c in b["children"]
                 if (c["label"] or "").lower().startswith(("rolle", "kapitän")) and c["value"]]
        for s in ship_links:
            ships.append({"name": s, "rollen": roles})
    for s in links["ship"]:
        if not any(norm(s) == norm(x["name"]) for x in ships):
            ships.append({"name": s, "rollen": []})

    places = all_values(blocks, "Ortschaft")
    places = unique(places + [p for p in links["place"]])
    related = unique(all_values(blocks, "Links zu Bezugspersonen") + links["person"])

    obj = {
        "Nachname, Vorname": first_value(blocks, "Nachname") if find(blocks, "Nachname") and
                             first_value(blocks, "Nachname") != NA else note.title,
        "Titel": first_value(blocks, "Titel"),
        "Lebensdaten": first_value(blocks, "Lebensdaten"),
        "Beruf/Funktionen": first_value(blocks, "Beruf"),
        "Auszeichnung": medals,
        "GND": ids_from(all_text, "gnd"),
        "VIAF": ids_from(all_text, "viaf"),
        "Lexikonbeitrag": all_values(blocks, "Lexikon"),
        "Schiff": ships,
        "Ortschaft": places,
        "Länderbezug": unique(all_values(blocks, "Länderbezug") + TAG_RE.findall(note.body)),
        "Archivalien mit Signatur": all_values(blocks, "Archivalien"),
        "Goobi-Link zu den Archivalien": unique(all_values(blocks, "Goobi") + ids_from(all_text, "goobi")),
        "Weitere Informationen mit Sammlungsbezug": all_values(blocks, "Weitere Informationen"),
        "Links zu Bezugspersonen": related,
        "Literatur": all_values(blocks, "Literatur"),
        "Quellen": sources,
        "Freitext": free_text(blocks, PERSON_LABELS),
        "Rolle auf der Weltreise": voyage_roles,
    }
    obj = na(obj)
    obj["_meta"] = meta_of(note, reasons)
    return obj


def build_place(vault, note, route_positions):
    blocks = parse_fields(note)
    links = classify_links(vault, note.links)
    obj = na({
        "Ort": note.title,
        "Region und Land": unique(links["place"] + TAG_RE.findall(note.body)),
        "Geonames": ids_from([note.body], "geonames"),
        "GND Geographisches Schlagwort": ids_from([note.body], "gnd"),
        "Schiff": links["ship"],
        "Personen (Link)": links["person"],
        "Weitere Verknüpfungen": links["organisation"] + links["collection"] + links["unresolved"],
        "Freitext": free_text(blocks, ["Ort", "Region", "Geonames", "GND", "Schiff"]),
    })
    obj["Position auf der Route"] = route_positions
    obj["_meta"] = meta_of(note, ["Route der Weltreise (Kaiserin Elisabeth)"])
    return obj


def build_collection(vault, note, reasons):
    blocks = parse_fields(note)
    links = classify_links(vault, note.links)
    urls = [u for u in urls_in(note.body) if url_kind(u) == "other"]
    contacts = [re.sub(r"^#Kontakt:?\s*", "", l.strip()) for l in note.lines
                if l.strip().lower().startswith("#kontakt")]
    obj = na({
        "Institution oder Projekttitel": note.title,
        "Website-Link zur Projektbeschreibung": urls[:1],
        "Kontakt": contacts + all_values(blocks, "Kontakt"),
        "Informationen zu den Beständen": all_values(blocks, "Informationen", "Bestände"),
        "Schiffe": links["ship"],
        "Personen": links["person"],
        "Weitere Links": urls[1:],
        "Freitext": [t for t in free_text(blocks, ["Institution", "Website", "Kontakt",
                                                   "Informationen", "Schiffe", "Personen"])
                     if not t.lower().startswith("#kontakt")],
    })
    obj["_meta"] = meta_of(note, reasons)
    return obj


def build_ship(vault, note, voyage_note, route, crew):
    links = classify_links(vault, note.links)
    voyage_line = next((l for l in note.lines if VOYAGE_TITLE in unicodedata.normalize("NFC", l)), "")
    years = re.search(r"\d{1,2}\.\d{1,2}\.\d{4}\s*-\s*\d{1,2}\.\d{1,2}\.\d{4}", voyage_line)
    captains = [c["name"] for c in crew if "kapitän" in c["rolle"].lower()]
    objects = [strip_links(l.strip(" -")) for l in note.lines if "Objekte" in l]
    obj = na({
        "Bezeichnung des Schiffes": note.title,
        "GND": ids_from([note.body], "gnd"),
        "Reise": {
            "Ziel der Reise": VOYAGE_TITLE,
            "Jahr": years.group(0) if years else "1892-1893",
            "Route": route,
            "Kapitän": captains,
        },
        "Projekte": links["collection"],
        "Objekte in der Sammlung": objects,
        "Archivbestände": [],
    })
    obj["_meta"] = meta_of(note, ["Schiff der Weltreise"])
    return obj


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    vault = Vault(args.vault)
    voyage_note, route, other_route, crew, intro = parse_voyage(vault)

    # --- Ortschaften der Route (in Reihenfolge, Duplikate zusammengeführt)
    positions = {}
    for i, name in enumerate(route, start=1):
        positions.setdefault(norm(name), []).append(i)
    places, missing_places = [], []
    for name in unique(route):
        note = vault.get(name)
        if note:
            places.append(build_place(vault, note, positions[norm(name)]))
        else:
            missing_places.append(name)
    route_keys = set(positions)

    # --- Personen
    persons, person_keys = {}, set()
    crew_roles = {}
    for c in crew:
        crew_roles.setdefault(norm(c["name"]), []).append(c["rolle"])
    for note in vault.notes:
        if note.folder != FOLDERS["person"] or note.title == VOYAGE_TITLE:
            continue
        reasons = []
        if has_medal(note):
            reasons.append(f"Auszeichnung: {MEDAL} 1892/1893")
        if norm(note.title) in crew_roles:
            reasons.append("Im Weltreise-Eintrag genannt")
        if undated_ship(note):
            reasons.append(f"Schiff: {SHIP_TITLE} ohne Datum (an Bord während der Weltreise)")
        if undated_ship_link(note):
            reasons.append(f"Verlinkt {SHIP_TITLE} ohne Datum (an Bord während der Weltreise)")
        if reasons:
            persons[norm(note.title)] = build_person(vault, note, reasons, crew_roles.get(norm(note.title)))
    for key, roles in crew_roles.items():
        if key not in persons:
            name = next(c["name"] for c in crew if norm(c["name"]) == key)
            persons[key] = build_person(vault, vault.get(name), ["Im Weltreise-Eintrag genannt"], roles, name)
    person_keys = set(persons)

    # --- Sammlungen über Verlinkungen
    def reasons_for(note):
        r = []
        keys = {norm(l) for l in note.links}
        if norm(VOYAGE_TITLE) in keys:
            r.append("Verlinkt die Weltreise")
        r += [f"Verlinkt Routen-Ortschaft: {l}" for l in unique(note.links) if norm(l) in route_keys]
        r += [f"Verlinkt Weltreise-Person: {l}" for l in unique(note.links) if norm(l) in person_keys]
        return r

    collections = [build_collection(vault, note, r) for note in vault.notes
                   if note.folder == FOLDERS["collection"] and (r := reasons_for(note))]

    # --- Schiff
    ship_note = vault.get(SHIP_TITLE)
    ships = [build_ship(vault, ship_note, voyage_note, route, crew)] if ship_note else []

    # --- Weltreise selbst
    voyage = na({
        "Titel": VOYAGE_TITLE,
        "Beschreibung": intro,
        "Schiff": SHIP_TITLE,
        "Besatzung (laut Eintrag)": crew,
        "Route": route,
        "Route mit anderem Passagierschiff (nicht berücksichtigt)": other_route,
        "Anzahl Personen": len(persons),
        "Anzahl Ortschaften": len(places),
        "Ortschaften ohne Eintrag": missing_places,
    })
    voyage["_meta"] = meta_of(voyage_note, ["Haupteintrag"])

    args.out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "weltreise.json": voyage,
        "schiffe.json": ships,
        "ortschaften.json": places,
        "personen.json": sorted(persons.values(), key=lambda p: norm(p["Nachname, Vorname"])),
        "sammlungen_projekte.json": collections,
    }
    for fname, data in outputs.items():
        (args.out / fname).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        n = len(data) if isinstance(data, list) else 1
        print(f"{fname:45s} {n:4d} Einträge")
    if missing_places:
        print("Routen-Ortschaften ohne Eintrag:", ", ".join(missing_places))


if __name__ == "__main__":
    main()
