"""
Filtert aus json/bilder.json alle Bilder der Weltreise, auf denen Tiere zu sehen sind
(Feld "Tiere" == true), und schreibt sie reduziert auf die relevanten Felder nach
json/bilder_tiere.json.

Übernommene Felder
- Titel, Inventarnummer (zur Identifikation)
- Bild-Link, Datierung, Geografie, Geografie-Pfad, Weltmuseum-Link
- Tierarten: die bereits vorhandene, aus der Bildbeschreibung abgeleitete Angabe.
  Fälschlich am Komma getrennte Einträge wie ["Kuh (Darstellung", "vermutet)"]
  werden wieder zusammengefügt.
- depicted_animals: alle Tiere, die in der "Bildbeschreibung" genannt werden (Wortliste
  DESCRIPTION_ANIMALS, auch Plural- und Komposita-Formen wie "Kamelen", "Reitelefanten",
  "Ochsenkarren"; "berittene" zählt als Pferd, "Reiter" nicht, da auch auf Kamelen
  und Elefanten). Nicht gezählt werden Jagd-Komposita ("Tigerjagd" nennt nur die Jagd),
  Tierprodukte (Federn, Fell, Leder) und Namen in Anführungszeichen (Wasserfall „Drachenkopf“).
  Darstellungen sind gekennzeichnet, z. B. "Vogel (Darstellung)"; "Tier (unbestimmt)" nur,
  wenn sonst kein Tier genannt ist.
- photographer: in den Metadaten des Objekts (Feld "_meta", z. B. Auswahlgrund
  "Fotograf/Sammler Eduard Hodek jun.", sowie ein evtl. vorhandenes Feld "Fotograf")
  verknüpfte Fotograf:innen; "NA", wenn keine gefunden werden.

Optional (--classify): Bildanalyse mit CLIP (Zero-Shot-Klassifikation). Jedes Bild wird
heruntergeladen (Cache: .cache/bilder/) und gegen eine feste Liste von Tierarten
verglichen; Treffer über --threshold landen im Feld "Tierarten (Bild-KI)".
Benötigt:  pip install torch transformers pillow requests

Aufruf:  python animal_pictures.py [--src PFAD] [--out PFAD]
                                  [--classify] [--model NAME] [--threshold 0.15] [--top 3]
"""

import argparse
import json
import re
from pathlib import Path

NA = "NA"

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = HERE / "json" / "bilder.json"
DEFAULT_OUT = HERE / "json" / "bilder_tiere.json"
CACHE_DIR = HERE / ".cache" / "bilder"

FIELDS = [
    "Titel",
    "Inventarnummer",
    "Bild-Link",
    "Datierung",
    "Geografie",
    "Geografie-Pfad",
    "Weltmuseum-Link",
    "Tierarten",
]

# Deutsches Label -> englischer Begriff für den CLIP-Prompt.
# Auswahl orientiert sich an der Route (Indien, Ceylon, Südostasien, Australien, Japan ...)
# und an den bereits vorhandenen Tierarten-Angaben.
ANIMAL_LABELS = {
    "Pferd": "horse",
    "Elefant": "elephant",
    "Kamel": "camel",
    "Rind": "cow or ox",
    "Wasserbüffel": "water buffalo",
    "Esel/Maultier": "donkey or mule",
    "Ziege": "goat",
    "Schaf": "sheep",
    "Hund": "dog",
    "Katze": "cat",
    "Affe": "monkey",
    "Tiger": "tiger",
    "Leopard/Gepard": "leopard or cheetah",
    "Löwe": "lion",
    "Bär": "bear",
    "Hirsch": "deer",
    "Nashorn": "rhinoceros",
    "Känguru": "kangaroo",
    "Krokodil": "crocodile",
    "Schlange": "snake",
    "Vogel": "bird",
    "Pfau": "peacock",
    "Huhn": "chicken",
    "Fisch": "fish",
    "Schildkröte": "turtle",
    "Drache (Darstellung)": "dragon sculpture",
    "Tierfigur (Darstellung)": "animal statue",
    "Tierfell/Jagdtrophäe": "animal skin or hunting trophy",
}
# Wortform in der Bildbeschreibung (kleingeschrieben, ganzes Wort) -> Tier.
# Reihenfolge zählt: Ausschlüsse (None) und Darstellungen vor den einfachen Tiernamen.
DESCRIPTION_ANIMALS = [
    (r"\w*jagd\w*|vogelperspektive", None),
    (r"vogel(figur|bild)\w*", "Vogel (Darstellung)"),
    (r"fabelvogel\w*", "Fabelvogel (Darstellung)"),
    (r"drache\w*", "Drache (Darstellung)"),
    (r"tierfigur\w*", "Tierfigur (Darstellung)"),
    (r"\w*pferde?\w*|schimmel|beritten\w*", "Pferd"),
    (r"\w*elefant\w*", "Elefant"),
    (r"kamel\w*", "Kamel"),
    (r"rind(er|ern|es)?", "Rind"),
    (r"\w*ochse\w*", "Ochse"),
    (r"\w*büffel\w*", "Büffel"),
    (r"gepard\w*", "Gepard"),
    (r"tiger\w*", "Tiger"),
    (r"löwe\w*", "Löwe"),
    (r"hirsch\w*", "Hirsch"),
    (r"hund(e|en|es)?", "Hund"),
    (r"schaf(e|en)?", "Schaf"),
    (r"ziege(n)?", "Ziege"),
    (r"affe(n)?", "Affe"),
    (r"katze(n)?", "Katze"),
    (r"vogel|vögel(n)?", "Vogel"),
    (r"(zug)?tier(e|en|es)?", "Tier (unbestimmt)"),
]
GENERIC_ANIMAL = "Tier (unbestimmt)"
QUOTED_RE = re.compile(r"„[^“]*“|\"[^\"]*\"")
WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")
# "Fotograf/Sammler Eduard Hodek jun.", "Fotografin: ...", "Photographer ..." -> Name
PHOTOGRAPHER_RE = re.compile(r"\b(?:fotograf|photograph)(?:in|er)?(?:/\w+)*\s*:?\s*(.+)", re.I)
PHOTOGRAPHER_KEYS = {"fotograf", "fotografin", "fotograf/sammler", "photographer"}

NO_ANIMAL = "kein Tier"
NO_ANIMAL_PROMPT = "a photograph of people and buildings without any animals"
PROMPT = "an old black-and-white photograph of a {}"


# --------------------------------------------------------------------------- helpers

def repair_species(value):
    """["Kuh (Darstellung", "vermutet)"] -> ["Kuh (Darstellung, vermutet)"]"""
    if not isinstance(value, list):
        return value
    repaired, buf = [], ""
    for part in value:
        buf = f"{buf}, {part}" if buf else part
        if buf.count("(") <= buf.count(")"):
            repaired.append(buf)
            buf = ""
    if buf:
        repaired.append(buf)
    return repaired


def first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return None if value == NA else value


def animals_in_description(text):
    """Alle in der Bildbeschreibung genannten Tiere, in Reihenfolge der ersten Nennung."""
    if not isinstance(text, str) or text == NA:
        return NA
    found = []
    for word in WORD_RE.findall(QUOTED_RE.sub(" ", text)):
        for pattern, animal in DESCRIPTION_ANIMALS:
            if re.fullmatch(pattern, word.lower()):
                if animal and animal not in found:
                    found.append(animal)
                break
    if len(found) > 1 and GENERIC_ANIMAL in found:
        found.remove(GENERIC_ANIMAL)
    return found or NA


def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from strings_in(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings_in(v)


def photographer(entry):
    """Mit dem Objekt verknüpfte Fotograf:innen aus den Metadaten, sonst "NA"."""
    found = []
    for key, value in entry.items():
        if key.lower() in PHOTOGRAPHER_KEYS:
            found += [v for v in strings_in(value) if v != NA]
    for text in strings_in(entry.get("_meta", {})):
        m = PHOTOGRAPHER_RE.search(text)
        if m:
            found.append(m.group(1).strip())
    found = list(dict.fromkeys(found))
    if not found:
        return NA
    return found[0] if len(found) == 1 else found


def reduce(entry):
    out = {f: entry.get(f, NA) for f in FIELDS}
    out["Tierarten"] = repair_species(out["Tierarten"])
    out["depicted_animals"] = animals_in_description(entry.get("Bildbeschreibung"))
    out["photographer"] = photographer(entry)
    out["_meta"] = {"id": entry.get("_meta", {}).get("id", NA), "datei": entry.get("Datei", NA)}
    return out


# --------------------------------------------------------------------------- Bildanalyse

def load_image(url):
    import io

    import requests
    from PIL import Image

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / url.rsplit("/", 1)[-1]
    if not path.exists():
        resp = requests.get(url, timeout=60, headers={"User-Agent": "Hack-The-Pool-2026"})
        resp.raise_for_status()
        path.write_bytes(resp.content)
    return Image.open(io.BytesIO(path.read_bytes())).convert("RGB")


def normalized(features):
    """transformers >= 5 liefert ein Output-Objekt (Projektion in pooler_output), ältere Versionen den Tensor."""
    emb = getattr(features, "pooler_output", features)
    return emb / emb.norm(dim=-1, keepdim=True)


def classify(entries, model_name, threshold, top):
    import torch
    from transformers import CLIPModel, CLIPProcessor

    model = CLIPModel.from_pretrained(model_name).eval()
    processor = CLIPProcessor.from_pretrained(model_name)

    labels = list(ANIMAL_LABELS) + [NO_ANIMAL]
    prompts = [PROMPT.format(en) for en in ANIMAL_LABELS.values()] + [NO_ANIMAL_PROMPT]
    with torch.no_grad():
        text = processor(text=prompts, return_tensors="pt", padding=True)
        text_emb = normalized(model.get_text_features(**text))

    for i, entry in enumerate(entries, 1):
        url = first(entry["Bild-Link"])
        if not url:
            entry["Tierarten (Bild-KI)"] = NA
            continue
        try:
            image = load_image(url)
        except Exception as exc:  # noqa: BLE001 - Download-Fehler sollen den Lauf nicht abbrechen
            print(f"  [{i}/{len(entries)}] {url}: {exc}")
            entry["Tierarten (Bild-KI)"] = NA
            continue

        with torch.no_grad():
            img = processor(images=image, return_tensors="pt")
            img_emb = normalized(model.get_image_features(**img))
            probs = (model.logit_scale.exp() * img_emb @ text_emb.T).softmax(dim=-1)[0]

        ranked = sorted(zip(labels, probs.tolist()), key=lambda x: x[1], reverse=True)
        hits = [
            {"Tier": label, "Score": round(p, 3)}
            for label, p in ranked[:top]
            if p >= threshold and label != NO_ANIMAL
        ]
        entry["Tierarten (Bild-KI)"] = hits or NA
        print(f"  [{i}/{len(entries)}] {entry['Titel'][:50]:50} -> "
              + ", ".join(f"{h['Tier']} {h['Score']:.2f}" for h in hits))


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--classify", action="store_true", help="Tierarten zusätzlich per CLIP aus dem Bild bestimmen")
    ap.add_argument("--model", default="openai/clip-vit-large-patch14")
    ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args()

    entries = json.loads(args.src.read_text(encoding="utf-8"))
    animals = [reduce(e) for e in entries if e.get("Tiere") is True]
    print(f"{len(animals)} von {len(entries)} Bildern zeigen Tiere")

    if args.classify:
        classify(animals, args.model, args.threshold, args.top)

    args.out.write_text(json.dumps(animals, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
