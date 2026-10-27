"""Shared helpers: paths, cached HTTP GET, JSON IO."""
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT.parent / "Sources"
DATA = ROOT / "data"
CACHE = ROOT / ".cache"
DATA.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

UA = "HackThePool2026-Kriegsmarine-enrichment/0.1"


def get_json(url, params=None, retries=3):
    """GET a JSON resource, cached on disk by full URL (re-runs are free and offline-safe)."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    path = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            path.write_text(json.dumps(data, ensure_ascii=False))
            return data
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def get_text(url, retries=3):
    """GET an HTML/text resource, cached on disk by URL (same cache as get_json)."""
    path = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    if path.exists():
        return path.read_text()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("utf-8", "ignore")
            path.write_text(text)
            time.sleep(0.5)
            return text
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def load(name):
    return json.loads((DATA / name).read_text())


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    print(f"wrote data/{name}")
