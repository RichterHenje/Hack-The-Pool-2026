"""Shared helpers: paths, cached HTTP GET, JSON IO."""
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# expedition_pool_edition/ is split into 1_sources (imported, read-only), 2_processing (this folder and its siblings
# normalization/, analyses/) and 3_visualization (the web pages in web/, which read web/data/)
KM = ROOT.parents[1]
SOURCES = KM / "1_sources" / "Sources"
ANALYSES = ROOT.parent / "analyses"
WEB_DATA = KM / "3_visualization" / "web" / "data"
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
            if isinstance(data, dict) and "error" in data and "servedby" in data:   # MediaWiki error: retry, never cache
                raise ValueError(data["error"].get("info", "MediaWiki API error"))
            path.write_text(json.dumps(data, ensure_ascii=False))
            return data
        except urllib.error.HTTPError as e:
            if attempt == retries - 1:
                raise
            # 429 Too Many Requests (Wikidata): honour Retry-After, else back off generously
            wait = int(e.headers.get("Retry-After") or 0) if e.code == 429 else 0
            time.sleep(max(wait, 15 * (attempt + 1) if e.code == 429 else 2 * (attempt + 1)))
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


def env(name):
    """Secret from the environment or the repo's .env (never written to data/ or logs)."""
    import os
    if os.environ.get(name):
        return os.environ[name]
    path = KM.parent / ".env"
    for line in (path.read_text().splitlines() if path.exists() else []):
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    raise SystemExit(f"{name} missing: set it in the environment or in {path}")


def load(name):
    return json.loads((DATA / name).read_text())


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    print(f"wrote data/{name}")
