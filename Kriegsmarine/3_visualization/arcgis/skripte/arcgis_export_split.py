"""Split the ArcGIS export bundle (scripts/arcgis/ke_export.js) into files in the repo.

    uv run python -m scripts.arcgis_export_split <bundle.json> [out_dir]

Writes one GeoJSON per hosted layer, the web map JSON, the item texts and the layer schemas,
plus MANIFEST.md with feature counts and SHA-256. Refuses a bundle that contains a token or a
truncated layer.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_NAME = re.compile(r"/services/([^/]+)/FeatureServer/")


def split(bundle: dict, out: Path) -> list[tuple[str, int | str, str]]:
    text = json.dumps(bundle)
    if re.search(r"[?&]token=", text):
        raise ValueError("bundle contains a token")
    truncated = [k for k, v in bundle["layers"].items() if v.get("exceededTransferLimit")]
    if truncated:
        raise ValueError(f"truncated layers: {truncated}")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, int | str, str]] = []

    def write(name: str, obj, n: int | str) -> None:
        data = json.dumps(obj, ensure_ascii=False, indent=None if name.endswith(".geojson") else 1)
        (out / name).write_text(data + "\n", encoding="utf-8", newline="\n")
        rows.append((name, n, hashlib.sha256((data + "\n").encode("utf-8")).hexdigest()))

    schemas, items = {}, {"webmap": bundle["webmap"]["item"]}
    for lid, lay in bundle["layers"].items():
        service = SERVICE_NAME.search(lay["url"]).group(1)
        if "same_as" in lay:
            schemas[lid] = {"service": service, "map_filter": lay["definitionExpression"]}
            continue
        gj = lay["geojson"]
        if len(gj["features"]) != lay["count"]:
            raise ValueError(f"{lid}: count mismatch")
        write(f"{service}.geojson", gj, lay["count"])
        items[service] = lay["item"]
        schemas[lid] = {
            "service": service,
            "map_filter": lay["definitionExpression"],
            "fields": lay["fields"],
            "timeInfo": lay["timeInfo"],
        }
    write(
        "webmap.json", bundle["webmap"]["data"], len(bundle["webmap"]["data"]["operationalLayers"])
    )
    write("items.json", items, len(items))
    write("layers.json", schemas, len(schemas))
    lines = [
        f"# ArcGIS export {bundle['exported_utc'][:10]}",
        "",
        (
            f"Snapshot of the private web map 977298da4e1a47c380c77a9041e11908 and its hosted layers, exported "
            f"{bundle['exported_utc']} by `scripts/arcgis/ke_export.js`, split by `scripts/arcgis_export_split.py`. "
            "Read-only copy; the live map stays the working version. Provenance per layer: `items.json` (description, "
            "credits, licence info) and `docs/21_data_provenance.md`."
        ),
        "",
        (
            "Rights: the GeoJSON holds links to Weltmuseum images (licence per record; 'Lizenz nicht geprüft' where "
            "unchecked), short OCR quotations from the 1895 diary and from ANNO newspapers, and team data. Private "
            "repository; check rights before anything here is published."
        ),
        "",
        "| file | features / entries | sha256 |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| `{n}` | {c} | `{h[:16]}…` |" for n, c, h in rows]
    (out / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return rows


def main() -> None:
    bundle = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else ROOT / "prototype" / "arcgis" / f"export_{bundle['exported_utc'][:10]}"
    )
    for name, n, _ in split(bundle, out):
        print(f"{name}: {n}")


if __name__ == "__main__":
    main()
