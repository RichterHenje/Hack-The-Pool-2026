"""
Wie filter_voyage.py (Code und Objektstruktur von dort, das Skript bleibt unverändert),
aber mit anderer Personenauswahl. Ausgabe: json/*_final.json

Personen werden aufgenommen, wenn
- im Feld "Auszeichnung" die Seereise-Denkmünze steht, oder
- die Notiz den Kreuzer "Kaiserin Elisabeth" verlinkt und an diesem Link (Zeile samt
  Unterpunkten wie "Rolle") entweder kein Jahr oder nur Jahre der Reise (1892-1893) stehen.
  Hat eine Notiz mehrere Links auf das Schiff, genügt einer, der diese Bedingung erfüllt.

Die Nennung im Weltreise-Eintrag allein reicht nicht mehr; sie steht aber weiterhin im Feld
"Rolle auf der Weltreise". Ortschaften, Schiff und Weltreise werden wie in filter_voyage.py
ausgewählt; Sammlungen hängen über die verlinkten Personen von der neuen Auswahl ab.

Aufruf:  python filter_voyage_ff.py [--vault PFAD] [--out PFAD]
"""

import argparse
import json
import re
from pathlib import Path

import filter_voyage as fv
from filter_voyage import FOLDERS, MEDAL, SHIP_TITLE, VOYAGE_TITLE, norm, unique

VOYAGE_YEARS = (1892, 1893)
YEAR_RE = re.compile(r"\b1[89]\d\d\b")
SUFFIX = "_final.json"


def ship_link_dates(note):
    """Für jeden Link auf die Kaiserin Elisabeth: die Jahre in der Zeile und ihren Unterpunkten."""
    out = []
    for b in fv.parse_fields(note):
        if any(norm(l) == norm(SHIP_TITLE) for l in fv.links_in(b["raw"])):
            texts = [b["raw"]] + [c["raw"] for c in b["children"]]
            out.append(sorted({int(y) for t in texts for y in YEAR_RE.findall(t)}))
    return out


def ship_reason(note):
    """Auswahlgrund über den Schiffs-Link, oder None, wenn nur Links mit anderen Jahren existieren."""
    dates = ship_link_dates(note)
    if any(not years for years in dates):
        return f"Verlinkt {SHIP_TITLE} ohne Datum"
    for years in dates:
        if all(VOYAGE_YEARS[0] <= y <= VOYAGE_YEARS[1] for y in years):
            return f"Verlinkt {SHIP_TITLE} mit Datum der Reise ({', '.join(map(str, years))})"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, default=fv.DEFAULT_VAULT)
    ap.add_argument("--out", type=Path, default=fv.DEFAULT_OUT)
    args = ap.parse_args()

    vault = fv.Vault(args.vault)
    voyage_note, route, other_route, crew, intro = fv.parse_voyage(vault)

    # --- Ortschaften der Route (wie filter_voyage.py)
    positions = {}
    for i, name in enumerate(route, start=1):
        positions.setdefault(norm(name), []).append(i)
    places, missing_places = [], []
    for name in unique(route):
        note = vault.get(name)
        if note:
            places.append(fv.build_place(vault, note, positions[norm(name)]))
        else:
            missing_places.append(name)
    route_keys = set(positions)

    # --- Personen: Denkmünze oder Schiffs-Link ohne Datum / mit Datum 1892-1893
    crew_roles = {}
    for c in crew:
        crew_roles.setdefault(norm(c["name"]), []).append(c["rolle"])
    persons = {}
    for note in vault.notes:
        if note.folder != FOLDERS["person"] or note.title == VOYAGE_TITLE:
            continue
        reasons = []
        if fv.has_medal(note):
            reasons.append(f"Auszeichnung: {MEDAL} 1892/1893")
        if r := ship_reason(note):
            reasons.append(r)
        if reasons:
            persons[norm(note.title)] = fv.build_person(vault, note, reasons, crew_roles.get(norm(note.title)))
    person_keys = set(persons)

    # --- Sammlungen über Verlinkungen (wie filter_voyage.py)
    def reasons_for(note):
        r = []
        keys = {norm(l) for l in note.links}
        if norm(VOYAGE_TITLE) in keys:
            r.append("Verlinkt die Weltreise")
        r += [f"Verlinkt Routen-Ortschaft: {l}" for l in unique(note.links) if norm(l) in route_keys]
        r += [f"Verlinkt Weltreise-Person: {l}" for l in unique(note.links) if norm(l) in person_keys]
        return r

    collections = [fv.build_collection(vault, note, r) for note in vault.notes
                   if note.folder == FOLDERS["collection"] and (r := reasons_for(note))]

    # --- Schiff
    ship_note = vault.get(SHIP_TITLE)
    ships = [fv.build_ship(vault, ship_note, voyage_note, route, crew)] if ship_note else []

    # --- Weltreise selbst
    voyage = fv.na({
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
    voyage["_meta"] = fv.meta_of(voyage_note, ["Haupteintrag"])

    args.out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "weltreise": voyage,
        "schiffe": ships,
        "ortschaften": places,
        "personen": sorted(persons.values(), key=lambda p: norm(p["Nachname, Vorname"])),
        "sammlungen_projekte": collections,
    }
    for name, data in outputs.items():
        fname = name + SUFFIX
        (args.out / fname).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        n = len(data) if isinstance(data, list) else 1
        print(f"{fname:45s} {n:4d} Einträge")
    if missing_places:
        print("Routen-Ortschaften ohne Eintrag:", ", ".join(missing_places))
    dropped = [c["name"] for c in crew if norm(c["name"]) not in persons]
    if dropped:
        print("Im Weltreise-Eintrag genannt, aber nicht ausgewählt:", ", ".join(unique(dropped)))


if __name__ == "__main__":
    main()
