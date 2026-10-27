"""Kulturpool REST API (v2) and SPARQL endpoint. No authentication needed.

Reference: https://api.kulturpool.at/reference/
Verified 2026-10-27: /v2/search, /v2/similar (on=image|metadata), SPARQL /query.
v2 field types: title is a string; creator, subject, edmRights* are lists.
"""

from __future__ import annotations

import requests

API = "https://api.kulturpool.at"
SPARQL = "https://sparql.kulturpool.at/query"
TIMEOUT = 60

_session = requests.Session()
_session.headers["User-Agent"] = "hack-the-pool-2026 team script"


def _get(url: str, params: dict | None = None, **kwargs) -> requests.Response:
    r = _session.get(url, params=params, timeout=TIMEOUT, **kwargs)
    r.raise_for_status()
    return r


def search(q: str = "*", per_page: int = 20, page: int = 1, **params) -> dict:
    """Full-text search. Extra params pass through, e.g.
    filter_by="dataProvider:=Albertina", facet_by="dataProvider".
    Returns the raw response: found, hits[].document, facet_counts.
    """
    if not 1 <= per_page <= 250:
        raise ValueError("per_page must be 1..250")
    return _get(f"{API}/v2/search", {"q": q, "per_page": per_page, "page": page, **params}).json()


def docs(response: dict) -> list[dict]:
    """The documents from a search or similar response."""
    return [h["document"] for h in response.get("hits", [])]


def similar(id: str, on: str = "image", per_page: int = 10, **params) -> dict:
    """Nearest neighbours of one object. on="image" (CLIP, 512d) or "metadata" (e5, 384d).
    The id is hits[].document.id from a search. Each hit carries hits[].vector_distance
    (0..2, smaller = closer). Extra params: threshold, filter_by.
    """
    if on not in ("image", "metadata"):
        raise ValueError('on must be "image" or "metadata"')
    return _get(f"{API}/v2/similar", {"id": id, "on": on, "per_page": per_page, **params}).json()


def neighbours(
    id: str, on: str = "image", per_page: int = 10, **params
) -> list[tuple[float, dict]]:
    """(vector_distance, document) pairs, closest first."""
    hits = similar(id, on, per_page, **params).get("hits", [])
    return [(h.get("vector_distance"), h["document"]) for h in hits]


def obj(id: str) -> dict:
    """One object by id (GET /v2/object). Full spec: reference/api/openapi.json."""
    return _get(f"{API}/v2/object", {"id": id}).json()


def sparql(query: str) -> list[dict]:
    """Run a SPARQL SELECT; returns bindings as plain {var: value} dicts.
    The data is EDM; see queries/*.rq for working examples.
    """
    r = _session.post(
        SPARQL,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return [{k: v["value"] for k, v in b.items()} for b in r.json()["results"]["bindings"]]


def lod_uri(document: dict, part: str = "aggregation") -> str:
    """LOD URI of a search hit: https://id.kulturpool.at/<id>/aggregation (or /cho)."""
    return f"https://id.kulturpool.at/{document['id']}/{part}"
