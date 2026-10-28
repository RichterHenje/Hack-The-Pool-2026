/* Reise 1892–93: the enrichment bundle (data/ke_enrichment.js, built by enrichment/08_export_prototype.py)
   as the spine: 309 diary days, 18 hunting episodes with press, photos, objects, people and the live animals.
   Also reads data/ke_layers.js (officers aboard, by diary entry) and data/world.js (coastline). */
(function () {
  "use strict";
  const E = window.KEE;
  if (!E || !window.L) {
    document.getElementById("map").textContent = "Daten oder Karte konnten nicht geladen werden.";
    return;
  }
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // ANNO snippets carry <mark> around the search terms: keep those, escape the rest
  const marked = (s) => esc(s).replace(/&lt;(\/?)mark&gt;/g, "<$1mark>");
  const link = (url, text) => url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text)}</a>` : esc(text);
  const fmt = (iso) => {
    if (!iso) return "–";
    const [y, m, d] = iso.split("-").map(Number);
    return `${d}. ${["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"][m - 1]} ${y}`;
  };
  const span = (a, b) => a === b ? fmt(a) : `${fmt(a)} – ${fmt(b)}`;
  const ROUTE = "#0072B2", HUNT = "#D55E00", PRESS = "#009E73", PHOTO = "#CC79A7", OBJECT = "#E69F00", HERO = "#56B4E9";
  const METHOD = {
    heading: "eigener Eintrag im Tagebuch",
    aligned: "Teil eines mehrtägigen Eintrags, per Abgleich zugeordnet",
    no_entry: "kein eigener Eintrag im Tagebuch",
  };
  const COORDS = {
    camp: "Lager/Station eines Jagdorts", hunt: "Jagdort", heading: "Ortsverzeichnis (Überschrift des Tages)", site: "Ortsverzeichnis (gleicher Ort an anderem Tag)",
    wikidata: "Ort der Route", hand: "Ortsliste von Hand",
  };
  const BASIS = { wikidata: "Wikidata", geonames: "GeoNames", estimated: "geschätzt", hand: "von Hand, ungefähr" };
  // where a day's point comes from (coord_source of 08_export_prototype.py): method, basis, link, note
  const coordInfo = (d) => {
    const s = d.coord_source;
    if (!s) return esc(COORDS[d.coords] || d.coords);
    const basis = s.ref ? link(s.ref, BASIS[s.basis] || s.basis) : esc(BASIS[s.basis] || s.basis);
    return `${esc(COORDS[s.method] || s.method)}${s.name ? ` „${esc(s.name)}“` : ""} · ${basis}` +
      (s.note ? ` (${esc(s.note)})` : "");
  };
  const STATUS = {
    schoenbrunn: "nach Schönbrunn", vienna: "nach Wien", free: "entflogen / frei", died: "gestorben", unknown: "Verbleib unbekannt",
  };
  const EVIDENCE = { diary: "Tagebuch", press: "Presse", probable: "erschlossen", site: "Übersetzung (franzferdinandsworld.com)" };
  const SOURCE = { diary: "Tagebuch", weltmuseum_tms: "Weltmuseum", anno: "ANNO", kulturpool: "Kulturpool", europeana: "Europeana", commons: "Commons" };
  // Provenance: card items carry data-src="<key>", map paths and timeline cells the class src-<key>;
  // the "Herkunft" checkboxes write one CSS rule per unchecked source (hide, or dim).
  // key: [what the data is, where it comes from, short badge label, colour, how it was found]
  const SRC = {
    diary: ["Tagebuchtext und Jagdsätze", "Tagebuch Franz Ferdinands, OCR", "Tagebuch", "#8c6d46",
      "Texterkennung des Digitalisats; Jagdsätze per Stichwortregel (Verb des Tötens + Tiername)"],
    site: ["Fehlende Tagebuchseiten", "Übersetzung auf franzferdinandsworld.com", "ffworld", "#c4a574",
      "von Hand nachgeschlagen, Zitate per Skript gegen die Seite geprüft"],
    vault: ["Personen und Notizen", "Team-Vault", "Vault", "#6b6b6b",
      "von Hand erfasst; Namen per Stichwortsuche im Tagebuch gefunden"],
    rangliste: ["Offiziere an Bord", "Ranglisten 1892/93", "Rangliste", "#9467bd",
      "KI-Transkription der Scans, ungeprüft"],
    anno: ["Zeitungsberichte", "ANNO, ÖNB", "ANNO", "#009E73",
      "Stichwortsuche (ANNO-API, Wortabstand) im Zeitfenster je Jagd"],
    europeana: ["Fotos der Reisefotografen", "Europeana / Weltmuseum Wien", "Europeana", "#CC79A7",
      "Suche nach Fotograf (Europeana-API), gefiltert auf Reisebezug"],
    weltmuseum: ["Objekte der Sammlung Este", "Weltmuseum Wien", "Weltmuseum", "#E69F00",
      "Sammlungsexport; Bezug zur Reise über Ort + Stichwort im Tagebuch oder Inventarkarte"],
    hoefer: ["Aufenthalte und weitere Fotos", "Höfer 2010, Wikimedia Commons", "Höfer/Commons", "#b0889e",
      "Reiseübersicht von Hand übertragen; Commons per API-Suche, nach Aufnahmedatum"],
    kulturpool: ["Akten, Bücher, Namenstreffer", "Kulturpool", "Kulturpool", "#d62728",
      "Stichwortsuche, dann Ähnlichkeitssuche (Textvektoren), Treffer per Textprüfung bestätigt"],
    lod: ["Normdaten, Koordinaten der Jagd- und Routenorte", "Wikidata, GND", "Wikidata/GND", "#0072B2",
      "Wikidata-ID von Hand, Koordinaten per API; GND per lobid-Suche mit Namens- und Datenabgleich"],
    geonames: ["Koordinaten der übrigen Orte", "GeoNames", "GeoNames", "#56B4E9",
      "Ortsname des Tages per Abgleich mit dem GeoNames-Verzeichnis"],
    inferred: ["Schlussfolgerungen, ungefähre Orte", "Team, von Hand", "erschlossen", "#aaaaaa",
      "Schlussfolgerung oder Sichtprüfung des Teams, begründet in einer Notiz"],
  };
  const COORD_SRC = { camp: "lod", hunt: "lod", wikidata: "lod", heading: "geonames", site: "geonames", hand: "inferred" };
  // a day's point: the basis in coord_source (wikidata/geonames/estimated/hand) wins over the method
  const BASIS_SRC = { wikidata: "lod", geonames: "geonames", estimated: "inferred", hand: "inferred" };
  const coordSrc = (d) => (d.coord_source && BASIS_SRC[d.coord_source.basis]) || COORD_SRC[d.coords] || "inferred";
  const EVIDENCE_SRC = { diary: "diary", press: "anno", probable: "inferred", site: "site" };
  const PS_SRC = { diary: "diary", weltmuseum_tms: "weltmuseum", anno: "anno", kulturpool: "kulturpool", europeana: "europeana", commons: "hoefer" };
  const tag = (k) => `<span class="srcb" data-src="${k}" style="--c:${SRC[k][3]}" title="${esc(SRC[k][0])} – Quelle: ${esc(SRC[k][1])} – ermittelt: ${esc(SRC[k][4])}">${esc(SRC[k][2])}</span>`;
  const block = (k, html) => `<div data-src="${k}">${html}</div>`;
  // Section icons; the colour per kind (k-*) matches the map layers, see reise.css
  const ICONS = {
    diary: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
    hunt: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    animal: '<circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="20" cy="16" r="2"/><path d="M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-6.84 1.045Q6.52 17.48 4.46 16.84A3.5 3.5 0 0 1 5.5 10Z"/>',
    photo: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    object: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.3 7 12 12l8.7-5"/><path d="M12 22V12"/>',
    people: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    aboard: '<path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/><circle cx="12" cy="5" r="3"/>',
    press: '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8z"/>',
    archive: '<rect x="2" y="3" width="20" height="5" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
    route: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    days: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    sea: '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
  };
  const ico = (k) => `<svg class="ico k-${k}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[k]}</svg>`;
  const initial = (name) => esc((name || "?").trim().charAt(0).toUpperCase());

  const days = E.days, episodes = E.episodes, heroes = E.heroes;
  const epById = new Map(episodes.map((e) => [e.id, e]));
  const dayIndex = new Map(days.map((d, i) => [d.date, i]));
  const KL = window.KEL || { days: {} };

  // Longitudes are unwrapped along the route so the Pacific crossing (Yokohama → Vancouver)
  // runs east, not back across Asia; items off the route follow the same rule for the Americas.
  let prevLon = null;
  for (const d of days) {
    if (d.lat === null) continue;
    while (prevLon !== null && d.lon - prevLon > 180) d.lon -= 360;
    while (prevLon !== null && d.lon - prevLon < -180) d.lon += 360;
    prevLon = d.lon;
  }
  const wrap = (lon) => lon < -30 ? lon + 360 : lon;

  const map = L.map("map", { minZoom: 1, maxZoom: 9 });
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution("Orte: Wikidata, GeoNames (CC BY 4.0)");
  const landLayer = L.layerGroup();
  if (window.WORLD) {
    // Drawn twice (second copy shifted by 360°) so the unwrapped route east of Japan still has land under it.
    const landStyle = { color: "#b9c4c4", weight: 0.8, fillColor: "#f6f3ea", fillOpacity: 1 };
    L.geoJSON(window.WORLD, { interactive: false, style: landStyle, attribution: "Küsten: Natural Earth" }).addTo(landLayer);
    L.geoJSON(window.WORLD, { interactive: false, style: landStyle,
      coordsToLatLng: (c) => L.latLng(c[1], c[0] + 360) }).addTo(landLayer);
  }
  // Historic base map: "World On Mercator's Projection" (1872), georeferenced on Map Warper (map 98512).
  // Tiles repeat east and west, so the unwrapped Pacific crossing needs no second copy.
  // Source scan is 7716 px wide (≈ zoom 5); higher zooms are upscaled.
  // The georeferencing is uneven (Europe fits, India–Java lies too far north, Japan too far south),
  // so the map is not shifted: on it, places are drawn where the map shows them (data/ke_places_1872.js,
  // keyed by the GeoNames names of ke_diary.json). Every point moves like the nearest of those places
  // (within 4°; present-day coordinates from E.geonames, or `heute` in the file for places that are
  // not in the gazetteer, e.g. Port Kennedy, Ugi, Trieste). reise.html?kalibrieren makes them draggable.
  const historicLayer = L.tileLayer("https://mapwarper.net/maps/tile/98512/{z}/{x}/{y}.png", {
    maxNativeZoom: 6,
    attribution: 'Karte 1872: <a href="https://mapwarper.net/maps/98512" target="_blank" rel="noopener">Map Warper 98512</a>',
  });
  const H1872 = window.KE1872 || {};
  const TODAY = { ...E.geonames };
  for (const [name, h] of Object.entries(H1872)) if (h.heute) TODAY[name] = h.heute;
  const REF = Object.entries(TODAY);
  let historic = true;
  // Position on the current base map; lon may be unwrapped (> 180 east of the date line)
  const pos = (lat, lon) => {
    if (!historic) return [lat, lon];
    const raw = ((lon + 180) % 360 + 360) % 360 - 180;
    let best = null, bestD = 16;   // 4° squared
    for (const [name, [rlat, rlon]] of REF) {
      const dd = (rlat - lat) ** 2 + (rlon - raw) ** 2;
      if (H1872[name] && dd < bestD) { best = name; bestD = dd; }
    }
    if (!best) return [lat, lon];
    const [rlat, rlon] = TODAY[best];
    return [lat + H1872[best].lat - rlat, lon + H1872[best].lon - rlon];
  };

  const layers = {
    route: L.layerGroup().addTo(map), hunt: L.layerGroup().addTo(map), press: L.layerGroup().addTo(map),
    photo: L.layerGroup(), object: L.layerGroup(), heroes: L.layerGroup(),
  };
  const located = days.filter((d) => d.lat !== null);
  const heroLine = new Map();
  const pressOf = (id) => E.press.filter((p) => p.episode === id);
  let currentHero = null;
  let current = 0;
  let progress = null, ship = null;

  // Where the ship is on day i: the day's own place, else (at sea, place unknown) interpolated
  // between the nearest located days before and after – an estimate, drawn hollow. Interpolated
  // in projected map space between the drawn points, so the ship stays on the route line.
  const locIndex = days.map((d, i) => d.lat !== null ? i : -1).filter((i) => i >= 0);
  function shipAt(i) {
    const d = days[i];
    if (d.lat !== null) return { ll: pos(d.lat, d.lon), exact: true };
    const p = locIndex.filter((j) => j < i).pop(), q = locIndex.find((j) => j > i);
    if (p === undefined || q === undefined) {
      const a = days[p ?? q];
      return { ll: pos(a.lat, a.lon), exact: false };
    }
    const t = (i - p) / (q - p), crs = L.CRS.EPSG3857;
    const a = crs.project(L.latLng(pos(days[p].lat, days[p].lon))), b = crs.project(L.latLng(pos(days[q].lat, days[q].lon)));
    return { ll: crs.unproject(a.add(b.subtract(a).multiplyBy(t))), exact: false };
  }
  // Route travelled up to the current day, and the ship
  function updateProgress() {
    if (!progress) return;
    const d = days[current], s = shipAt(current);
    const done = located.filter((x) => x.date <= d.date).map((x) => pos(x.lat, x.lon));
    progress.setLatLngs(s.exact ? done : [...done, s.ll]);
    ship.setLatLng(s.ll).setStyle(s.exact ? { fillColor: "#1d1d1b", dashArray: null } : { fillColor: "#fff", dashArray: "3 2" });
    ship.setTooltipContent(`${esc(fmt(d.date))} · ${esc(d.place || "–")}${s.exact ? "" : " (Position geschätzt)"}`);
  }

  // Stays at one place: day indices → "20. Februar 1893 – 27. Februar 1893 (8 Tage)", one line per run
  const stays = (idx) => {
    const runs = [];
    for (const i of idx) {
      const last = runs[runs.length - 1];
      if (last && i === last[1] + 1) last[1] = i; else runs.push([i, i]);
    }
    return runs.map(([a, b]) => `${esc(span(days[a].date, days[b].date))}${b > a ? ` (${b - a + 1} Tage)` : ""}`).join("<br>");
  };

  // Popup at a place: what the sources ticked under "Herkunft" say about the days there.
  // The sidebar always shows everything; the checkboxes filter only the map, its popups and the timeline.
  // The map fills the window; the top bar, the story card and the timeline float over it.
  // view() is the padding that keeps fitted bounds, panned points and popups in the free part.
  const view = () => {
    const p = document.getElementById("panel").getBoundingClientRect();
    const t = document.getElementById("timeline").getBoundingClientRect();
    const top = document.getElementById("topbar").getBoundingClientRect().bottom + 16;
    const side = p.width < innerWidth * 0.6;   // card beside the map (desktop) or below it (phone)
    return { paddingTopLeft: [side ? p.right + 24 : 16, top], paddingBottomRight: [24, innerHeight - (side ? t.top : p.top) + 16] };
  };
  // Leaflet copies these when a popup is bound, i.e. on each draw()
  const POPUP = { maxWidth: 340, className: "place-pop",
    get autoPanPaddingTopLeft() { return view().paddingTopLeft; },
    get autoPanPaddingBottomRight() { return view().paddingBottomRight; } };
  const research = () => document.body.classList.contains("research");
  // Outside research mode every source counts as chosen: the map shows everything, without badges
  const sourcesOn = () => new Set(research() ? [...document.querySelectorAll("#sources input:checked")].map((b) => b.value) : Object.keys(SRC));
  function placePopup(idx, label) {
    const on = sourcesOn(), dim = research() && document.getElementById("src-dim").checked;
    const part = (k, html) => on.has(k) ? block(k, html) : dim ? `<div class="off">${html}</div>` : "";
    const ds = idx.map((i) => days[i]), d0 = ds.find((d) => d.lat !== null) || ds[0];
    const eps = [...new Set(ds.map((d) => d.episode).filter(Boolean))].map((id) => epById.get(id)).filter(Boolean);
    const hunting = ds.filter((d) => d.hunt);
    const animals = {};
    for (const d of hunting) for (const [a, n] of Object.entries(d.hunt.animals)) animals[a] = (animals[a] || 0) + n;
    const firstQuote = hunting.flatMap((d) => d.hunt.quotes)[0];
    const photos = [...new Set(ds.flatMap((d) => d.photos))].map((i) => E.photos[i]);
    const objects = [...new Set(ds.flatMap((d) => d.objects))].map((i) => E.objects[i]);
    const people = [...new Set(ds.flatMap((d) => d.people))].filter((id) => E.people[id]);
    const heroEvents = ds.flatMap((d) => d.heroes.map((h) => ({ ...h, date: d.date, hero: heroes.find((x) => x.id === h.id) })));
    const press = eps.flatMap((ep) => pressOf(ep.id));
    const kp = eps.flatMap((ep) => ep.kulturpool);
    const aboard = (KL.days[d0.entry] || {}).aboard || [];
    const ck = coordSrc(d0);
    const wd = eps.flatMap((ep) => ep.places.filter((p) => p.wikidata));
    const notes = eps.flatMap((ep) => ep.places.map((p) => p.coord_note).filter(Boolean));
    const parts = [
      part(ck, `<p class="note">Ort: ${coordInfo(d0)} ${tag(ck)}</p>`),
      wd.length ? part("lod", `<p class="note">${wd.map((p) => link(`https://www.wikidata.org/wiki/${p.wikidata}`, `${p.label} (${p.wikidata})`)).join(", ")} ${tag("lod")}</p>`) : "",
      notes.length ? part("inferred", `<p class="note">${esc(notes.join("; "))} ${tag("inferred")}</p>`) : "",
      part("diary", `<h4>${ico("diary")}Tagebuch ${tag("diary")}</h4><p>${ds.length} ${ds.length === 1 ? "Tag" : "Tage"}${hunting.length ? `, Jagdsätze an ${hunting.length}` : ""}${eps.length ? ` · Jagd: ${eps.map((ep) => huntButton(ep.id, ep.label)).join(", ")}` : ""}</p>
        ${hunting.length ? chips(animals) : ""}${firstQuote ? quote(firstQuote) : ""}`),
      ...heroEvents.map((h) => {
        const k = EVIDENCE_SRC[h.hero && h.hero.evidence] || "diary";
        return part(k, `<p>${heroButton(h.id, h.hero ? h.hero.name : h.id)}: ${esc(h.event)} ${tag(k)}</p>`);
      }),
      press.length ? part("anno", `<h4>${ico("press")}Zeitungen: ${press.length} ${tag("anno")}</h4><ul class="plain">${press.slice(0, 4).map((p) =>
        `<li>${link(p.url, p.newspaper)}, ${esc(fmt(p.date))}</li>`).join("")}${press.length > 4 ? `<li class="note">… und ${press.length - 4} weitere</li>` : ""}</ul>`) : "",
      photos.length ? part("europeana", `<h4>${ico("photo")}Fotos: ${photos.length} ${tag("europeana")}</h4>${photoGrid(photos.slice(0, 2))}`) : "",
      objects.length ? part("weltmuseum", `<h4>${ico("object")}Objekte der Sammlung Este: ${objects.length} ${tag("weltmuseum")}</h4><ul class="plain">${objects.slice(0, 4).map((o) =>
        `<li>${link(o.url, o.title || o.type)}${o.strength === "strong" ? " <span class='lic'>starker Beleg</span>" : ""}</li>`).join("")}${objects.length > 4 ? `<li class="note">… und ${objects.length - 4} weitere</li>` : ""}</ul>`) : "",
      people.length ? part("vault", `<h4>${ico("people")}Im Tagebuch genannt ${tag("vault")}</h4><p>${people.map((id) => personButton(id, E.people[id].name)).join(", ")}</p>`) : "",
      aboard.length ? part("rangliste", `<p class="note">${aboard.length} Offiziere an Bord laut Rangliste ${tag("rangliste")}</p>`) : "",
      eps.some((ep) => ep.hoefer && ep.hoefer.from) ? part("hoefer", `<p class="note">${eps.filter((ep) => ep.hoefer && ep.hoefer.from).map((ep) =>
        `Aufenthalt laut Höfer 2010: ${esc(span(ep.hoefer.from, ep.hoefer.to))}`).join("; ")} ${tag("hoefer")}</p>`) : "",
      kp.length ? part("kulturpool", `<h4>${ico("archive")}Kulturpool ${tag("kulturpool")}</h4><ul class="plain">${kp.slice(0, 3).map((r) => `<li>${link(r.url, r.title)}</li>`).join("")}</ul>`) : "",
    ].filter(Boolean).join("");
    return `<div class="pop card"><h3>${esc(label || d0.place)}</h3><div class="meta">${stays(idx)}</div>
      ${parts || "<p class='note'>Keine Daten aus den gewählten Quellen.</p>"}</div>`;
  }

  // All map points, redrawn when the base map changes
  function draw() {
    for (const g of Object.values(layers)) g.clearLayers();
    L.polyline(located.map((d) => pos(d.lat, d.lon)), { color: ROUTE, weight: 2, opacity: 0.35 }).addTo(layers.route);
    progress = L.polyline([], { color: ROUTE, weight: 3, opacity: 0.9, interactive: false }).addTo(layers.route);
    // One marker per place (several days often share one): the tooltip lists the stays,
    // a click picks the day there closest to the current one
    const byPlace = new Map();
    for (const d of located) {
      const k = `${d.place}|${d.lat.toFixed(3)}|${d.lon.toFixed(3)}`;
      if (!byPlace.has(k)) byPlace.set(k, []);
      byPlace.get(k).push(dayIndex.get(d.date));
    }
    for (const idx of byPlace.values()) {
      const d0 = days[idx[0]];
      L.circleMarker(pos(d0.lat, d0.lon), { radius: 3.5, color: "#fff", weight: 1, fillColor: ROUTE, fillOpacity: 0.9,
        className: `src-${coordSrc(d0)}` })
        .bindTooltip(`<b>${esc(d0.place)}</b><br>${stays(idx)}`)
        .bindPopup(() => placePopup(idx), POPUP)
        .on("click", () => selectDay(idx.reduce((best, i) => Math.abs(i - current) < Math.abs(best - current) ? i : best), false))
        .addTo(layers.route);
    }
    const placeOf = (d) => byPlace.get(`${d.place}|${d.lat.toFixed(3)}|${d.lon.toFixed(3)}`);
    // The current day's label sits on the ship, so exactly one label is open
    ship = L.circleMarker([0, 0], { radius: 7, color: "#1d1d1b", weight: 2.5, fillColor: "#1d1d1b", fillOpacity: 1, interactive: false })
      .bindTooltip("", { permanent: true, direction: "top", offset: [0, -6] }).addTo(layers.route);
    updateProgress();
    // Hunts: one marker per episode place, sized by kill sentences; press as a ring around it
    for (const ep of episodes) {
      for (const p of ep.places) {
        if (p.lat == null) continue;
        const ll = pos(p.lat, wrap(p.lon));
        L.circleMarker(ll, {
          radius: 4 + Math.min(9, Math.sqrt(ep.kill_sentences) * 1.6), color: "#fff", weight: 1.5, fillColor: HUNT, fillOpacity: 0.9,
          className: "src-diary",
        }).bindTooltip(`${esc(p.label)} · ${esc(span(ep.start, ep.end))}<br>${ep.kill_sentences} Sätze vom Erlegen/Schießen`)
          .bindPopup(() => placePopup(days.map((d, i) => d.date >= ep.start && d.date <= ep.end ? i : -1).filter((i) => i >= 0), p.label), POPUP)
          .on("click", () => selectHunt(ep.id, false)).addTo(layers.hunt);
        const n = ep.anno.issues_high;
        if (n) {
          L.circleMarker(ll, { radius: 11 + Math.min(12, n * 1.2), color: PRESS, weight: 1.5, opacity: 0.75, fill: false, className: "src-anno" })
            .bindTooltip(`${esc(p.label)} · ${n} Zeitungsausgaben (ANNO, hoch)`).on("click", () => selectHunt(ep.id, false)).addTo(layers.press);
        }
      }
    }
    // Photos and objects at the day they are dated to
    for (const d of located) {
      if (d.photos.length) {
        L.circleMarker(pos(d.lat, d.lon), { radius: 4 + Math.min(6, d.photos.length), color: "#fff", weight: 1.5, fillColor: PHOTO, fillOpacity: 0.9, className: "src-europeana" })
          .bindTooltip(`${esc(fmt(d.date))} · ${d.photos.length} Foto(s)`).bindPopup(() => placePopup(placeOf(d)), POPUP)
          .on("click", () => selectDay(dayIndex.get(d.date), false)).addTo(layers.photo);
      }
      if (d.objects.length) {
        L.circleMarker(pos(d.lat, d.lon), { radius: 4 + Math.min(6, d.objects.length / 2), color: "#fff", weight: 1.5, fillColor: OBJECT, fillOpacity: 0.9, className: "src-weltmuseum" })
          .bindTooltip(`${esc(fmt(d.date))} · ${d.objects.length} Objekt(e) der Sammlung Este`).bindPopup(() => placePopup(placeOf(d)), POPUP)
          .on("click", () => selectDay(dayIndex.get(d.date), false)).addTo(layers.object);
      }
    }
    // Live animals: the path of each animal (or group), from where it came aboard to where it ended
    // (straight lines between the stations, not the ships' tracks)
    heroLine.clear();
    for (const h of heroes) {
      const pts = h.route.filter((r) => r.lat != null).map((r) => pos(r.lat, wrap(r.lon)));
      if (!pts.length) continue;
      const className = `src-${EVIDENCE_SRC[h.evidence] || "diary"}`;
      const line = pts.length > 1
        ? L.polyline(pts, { color: HERO, weight: 2, opacity: 0.8, dashArray: "6 5", className })
          .bindTooltip(esc(h.name)).on("click", () => selectHero(h.id, false)).addTo(layers.heroes) : null;
      L.circleMarker(pts[0], { radius: 5, color: HERO, weight: 2, fillColor: "#fff", fillOpacity: 1, className })
        .bindTooltip(`${esc(h.name)} · ${esc(h.route[0].event)}`).on("click", () => selectHero(h.id, false)).addTo(layers.heroes);
      heroLine.set(h.id, { pts, line });
    }
    if (currentHero) highlightHero(currentHero);
    ship.bringToFront();
  }
  function highlightHero(id) {
    for (const [hid, { line }] of heroLine) {
      if (line) line.setStyle(hid === id ? { weight: 4, opacity: 1 } : { weight: 2, opacity: 0.25 });
      if (line && hid === id) line.bringToFront();
    }
  }
  const showHistoric = (on) => {
    historic = on;
    if (on) { map.removeLayer(landLayer); historicLayer.addTo(map); }
    else { map.removeLayer(historicLayer); landLayer.addTo(map); }
    draw();
  };
  showHistoric(true);
  map.fitBounds(located.map((d) => pos(d.lat, d.lon)), view());
  document.getElementById("lyr-historic").addEventListener("change", (e) => showHistoric(e.target.checked));

  // Calibration (reise.html?kalibrieren): one draggable marker per place of data/ke_places_1872.js;
  // the box shows the file with the new positions to copy into ke_places_1872.js and .json.
  if (new URLSearchParams(location.search).has("kalibrieren")) {
    const box = L.control({ position: "topright" });
    box.onAdd = () => {
      const t = L.DomUtil.create("textarea", "calib");
      t.style.cssText = "width:22em;height:14em;font:11px monospace";
      L.DomEvent.disableClickPropagation(t);
      return t;
    };
    box.addTo(map);
    const show = () => { box.getContainer().value = "window.KE1872 = " + JSON.stringify(H1872, null, 1) + ";\n"; };
    for (const place of Object.keys(H1872)) {
      const shift = wrap(H1872[place].lon) - H1872[place].lon;
      L.marker([H1872[place].lat, H1872[place].lon + shift], { draggable: true, title: place }).addTo(map).on("dragend", (e) => {
        const ll = e.target.getLatLng();
        H1872[place] = { ...H1872[place], lat: +ll.lat.toFixed(4), lon: +(ll.lng - shift).toFixed(4), quelle: "von Hand (Kalibrierung)" };
        show();
        if (historic) draw();
      });
    }
    show();
  }

  for (const [key, layer] of Object.entries(layers)) {
    document.getElementById(`lyr-${key}`).addEventListener("change", (e) => {
      if (e.target.checked) layer.addTo(map); else map.removeLayer(layer);
    });
  }
  const showLayer = (key) => {
    const box = document.getElementById(`lyr-${key}`);
    if (!box.checked) { box.checked = true; layers[key].addTo(map); }
  };

  // Provenance checkboxes: a collapsible box at the top right of the map
  const srcBox = L.control({ position: "topright" });
  srcBox.onAdd = () => {
    const div = L.DomUtil.create("div", "src-ctl");
    div.innerHTML = `<details><summary>Herkunft der Daten</summary>
      <p class="note">Gilt für die Karte: Punkte, Fenster beim Klick auf einen Ort, Zeitleiste. Die Seitenleiste zeigt immer alles.</p>
      <div id="sources">${Object.entries(SRC).map(([k, [what, from, , c, how]]) =>
        `<label><span class="dot" style="--c:${c}"></span><input type="checkbox" value="${k}" checked><span>${esc(what)}
          <span class="from">(${esc(from)})</span><span class="how">${esc(how)}</span></span></label>`).join("")}</div>
      <label class="src-mode"><input type="checkbox" id="src-dim"> abgewählte nur abblenden</label></details>`;
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);
    return div;
  };
  const layerBox = L.control({ position: "topright" });
  layerBox.onAdd = () => {
    const div = document.getElementById("layers-box");
    L.DomEvent.disableClickPropagation(div);
    return div;
  };
  layerBox.addTo(map);
  srcBox.addTo(map);
  const srcStyle = document.head.appendChild(document.createElement("style"));
  // Buttons in the popups (day, hunt, animal, person) work as in the sidebar. Leaflet stops clicks
  // from leaving a popup, so the handler sits on the popup element itself.
  const popupClick = (e) => {
    const b = e.target.closest("[data-day],[data-hunt],[data-hero],[data-person]");
    if (!b) return;
    if (b.dataset.day) { showTab("day"); selectDay(dayIndex.get(b.dataset.day), false); }
    if (b.dataset.hunt) selectHunt(b.dataset.hunt, false);
    if (b.dataset.hero) selectHero(b.dataset.hero, false);
    if (b.dataset.person) selectPerson(b.dataset.person);
  };
  const wired = new WeakSet();
  let openPopup = null;
  map.on("popupopen", (e) => {
    openPopup = e.popup;
    const el = e.popup.getElement();
    if (!wired.has(el)) { el.addEventListener("click", popupClick); wired.add(el); }
  });
  map.on("popupclose", () => { openPopup = null; });
  // Map markers and timeline cells by CSS; the open popup is rebuilt (placePopup reads the checkboxes)
  const applySources = () => {
    const rule = document.getElementById("src-dim").checked ? "opacity: 0.2" : "display: none";
    srcStyle.textContent = !research() ? "" : [...document.querySelectorAll("#sources input:not(:checked)")]
      .map((b) => `.src-${b.value} { ${rule} }`).join("\n");
    if (openPopup) openPopup.update();
  };
  document.getElementById("sources").addEventListener("change", applySources);
  document.getElementById("src-dim").addEventListener("change", applySources);
  // Research mode: badges, notes, scan links and the provenance filter; off = the story alone
  document.getElementById("research").addEventListener("change", (e) => {
    document.body.classList.toggle("research", e.target.checked);
    applySources();
  });

  // Stats
  const huntDays = days.filter((d) => d.hunt);
  document.getElementById("stats").innerHTML = [
    [days.length, `Tage, ${fmt(days[0].date)} bis ${fmt(days[days.length - 1].date)}; ${located.length} mit Ort auf der Karte`],
    [episodes.length, `Jagden mit ${episodes.reduce((n, e) => n + e.kill_sentences, 0)} Sätzen vom Erlegen oder Schießen (an ${huntDays.length} Tagen, ungeprüft)`],
    [E.press.length, "Zeitungsausgaben in ANNO zu den Jagden"],
    [E.photos.length, `Fotos der Reisefotografen (Europeana), ${E.photos.filter((p) => p.date).length} datiert`],
    [E.objects.length, "Objekte der Sammlung Este mit Beleg aus dem Tagebuch oder der Inventarkarte"],
    [heroes.length, "lebende Tiere oder Tiergruppen an Bord"],
  ].map(([n, t]) => `<dt>${esc(n)}</dt><dd>${esc(t)}</dd>`).join("");
  document.getElementById("kpis").innerHTML = [[days.length, "Tage unterwegs"], [episodes.length, "Jagden"], [E.press.length, "Zeitungsberichte"]]
    .map(([n, t]) => `<div><dt>${esc(n)}</dt><dd>${esc(t)}</dd></div>`).join("");
  const welcome = document.getElementById("welcome");
  const closeWelcome = () => { welcome.hidden = true; };
  document.getElementById("start").addEventListener("click", closeWelcome);
  document.getElementById("info").addEventListener("click", () => { welcome.hidden = false; document.getElementById("start").focus(); });
  welcome.addEventListener("click", (e) => { if (e.target === welcome) closeWelcome(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !welcome.hidden) closeWelcome(); });

  // Tabs
  const TABS = ["day", "hunt", "heroes", "people", "echo"];
  function showTab(name) {
    for (const t of TABS) {
      document.getElementById(`tab-${t}`).setAttribute("aria-selected", String(t === name));
      document.getElementById(`view-${t}`).hidden = t !== name;
    }
  }
  for (const t of TABS) document.getElementById(`tab-${t}`).addEventListener("click", () => showTab(t));

  // --- shared pieces --------------------------------------------------------------------
  const chips = (animals) => `<div class="chips">${Object.entries(animals)
    .map(([id, n]) => `<span class="chip">${esc(E.animals[id] || id)} ${n > 1 ? `<b>${n}</b>` : ""}</span>`).join("")}</div>`;
  const quote = (q, extra = "") => `<blockquote${q.first_person ? ' class="fp"' : ""}>${esc(q.text)}${extra}</blockquote>`;
  const scanUrl = (band, scan) => band && scan
    ? `https://archive.org/details/${band === 1 ? "tagebuchmeinerr01ferdgoog" : "tagebuchmeinerr00ferdgoog"}/page/n${scan - 1}/mode/1up` : null;
  const photoGrid = (list) => list.length ? `<ul class="thumbs" data-src="europeana">${list.map((p) => `<li>
      ${p.open && p.preview ? `<a href="${esc(p.url)}" target="_blank" rel="noopener"><img src="${esc(p.preview)}" alt="${esc(p.title)}" loading="lazy"></a>` : ""}
      <div>${link(p.url, p.title)}<div class="meta">${esc(p.creator)}${p.date ? " · " + esc(fmt(p.date)) : ""} ·
        <span class="lic">${p.open ? "CC BY-NC-SA 4.0" : "In Copyright"}</span> · ${link(p.europeana, "Europeana")}</div></div></li>`).join("")}</ul>` : "";
  const objectList = (list) => list.length ? `<ul class="records" data-src="weltmuseum">${list.map((o) => `<li class="noimg"><div>
      ${link(o.url, o.title || o.type)} <span class="lic">${o.strength === "strong" ? "starker Beleg" : "Beleg"}</span>
      <div class="meta">${esc(o.inventory)} · ${esc(o.type)} · ${esc(o.region || "")}</div>
      ${o.evidence ? `<div class="ev">${o.acquisition ? "Kauf/Geschenk: " : ""}„${esc(o.evidence)}“ ${link(o.page_url, "Scan")}</div>` : ""}
      ${o.card ? `<div class="meta">Inventarkarte: ${esc(o.card)}</div>` : ""}</div></li>`).join("")}</ul>` : "";
  const pressItem = (p) => `<li class="noimg" data-src="anno"><div><div class="press-head"><b>${link(p.url, p.newspaper)}</b>
      <span class="when">${esc(fmt(p.date))}</span><span class="rel rel-${esc(p.relevance)}" title="Relevanz">${p.relevance === "high" ? "hoch" : "mittel"}</span></div>
      ${p.snippets.map((s) => `<blockquote class="press">${marked(s.text)} ${link(s.url, `S. ${s.page || "?"}`)}</blockquote>`).join("")}</div></li>`;
  const dayButton = (date, text) => dayIndex.has(date)
    ? `<button type="button" class="linkish" data-day="${esc(date)}">${esc(text || fmt(date))}</button>` : esc(text || fmt(date));
  const huntButton = (id, text) => `<button type="button" class="linkish" data-hunt="${esc(id)}">${esc(text)}</button>`;
  const personButton = (id, text) => `<button type="button" class="linkish" data-person="${esc(id)}">${esc(text)}</button>`;
  const heroButton = (id, text) => `<button type="button" class="linkish" data-hero="${esc(id)}">${esc(text)}</button>`;
  document.getElementById("panel").addEventListener("click", (e) => {
    const b = e.target.closest("[data-day],[data-hunt],[data-hero]");
    if (!b) return;
    if (b.dataset.day) { showTab("day"); selectDay(dayIndex.get(b.dataset.day)); }
    if (b.dataset.hunt) selectHunt(b.dataset.hunt);
    if (b.dataset.hero) selectHero(b.dataset.hero);
  });

  // --- days -----------------------------------------------------------------------------
  const sel = document.getElementById("day");
  sel.innerHTML = days.map((d, i) =>
    `<option value="${i}">${esc(d.date)} · ${d.hunt ? "◆ " : ""}${esc(d.place)}</option>`).join("");

  function dayCard(d) {
    const ep = d.episode && epById.get(d.episode);
    const people = d.people.filter((id) => E.people[id]).map((id) => ({ id, ...E.people[id] }));
    const photos = d.photos.map((i) => E.photos[i]);
    const objects = d.objects.map((i) => E.objects[i]);
    const kl = KL.days[d.entry] || {};
    const i = dayIndex.get(d.date);
    const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
    const facts = [
      d.lat === null && d.coords === "sea" && ["sea", "auf See"],
      d.hunt && ["hunt", plural(d.hunt.n, "Jagdsatz", "Jagdsätze")],
      photos.length && ["photo", plural(photos.length, "Foto", "Fotos")],
      objects.length && ["object", plural(objects.length, "Objekt", "Objekte")],
      d.heroes.length && ["animal", plural(d.heroes.length, "Tier an Bord", "Tiere an Bord")],
      people.length && ["people", plural(people.length, "Person", "Personen")],
      (kl.aboard || []).length && ["aboard", plural(kl.aboard.length, "Offizier", "Offiziere")],
    ].filter(Boolean);
    const factStrip = facts.length ? `<div class="facts">${facts.map(([k, t]) => `<span class="fact f-${k}">${ico(k)}${esc(t)}</span>`).join("")}</div>` : "";
    const cover = photos.find((p) => p.open && p.preview);
    let html = `<p class="kicker">${esc(fmt(d.date))} · Tag ${i + 1} von ${days.length}</p>
      <h3>${esc(d.place || (d.coords === "sea" ? "Auf See" : "–"))}</h3>
      ${factStrip}
      ${cover ? `<figure class="cover"><a href="${esc(cover.url)}" target="_blank" rel="noopener"><img src="${esc(cover.preview)}" alt="${esc(cover.title)}"></a>
        <figcaption>${esc(cover.title)}${cover.creator ? " · " + esc(cover.creator) : ""}</figcaption></figure>` : ""}
      ${d.hunt && d.hunt.quotes[0] ? `<blockquote class="lead-quote">${esc(d.hunt.quotes[0].text)}</blockquote>` : ""}
      <div class="meta">Tagebuch ${link(d.page_url, `Bd. ${d.band}, S. ${d.scan}`)}
        ${d.site_url ? " · " + link(d.site_url, "Übersetzung") : ""}</div>
      <p class="note">${esc(METHOD[d.method] || d.method)} ${tag("diary")}${d.heading ? ` · Überschrift (OCR): „${esc(d.heading)}“` : ""}
        ${d.lat !== null ? ` · Ort: ${coordInfo(d)} ${tag(coordSrc(d))}` : d.coords === "sea" ? " · auf See" : " · ohne Ort auf der Karte"}</p>`;
    if (ep) {
      html += `<p class="banner">Teil der Jagd ${huntButton(ep.id, ep.label)} (${esc(span(ep.start, ep.end))})</p>`;
    }
    if (d.hunt) {
      html += block("diary", `<h4>${ico("hunt")}Jagd im Tagebuch: ${d.hunt.n} ${d.hunt.n === 1 ? "Satz" : "Sätze"}${d.hunt.first_person ? `, ${d.hunt.first_person} in der Ich-Form` : ""} ${tag("diary")}</h4>
        ${chips(d.hunt.animals)}${d.hunt.quotes.slice(1).map((q) => quote(q)).join("")}
        <p class="note">Wortlaut aus der Texterkennung, am Scan prüfen. Genannte Tiere sind nicht gleich getötete Tiere.</p>`);
    }
    if (d.heroes.length) {
      html += `<h4>${ico("animal")}Lebende Tiere</h4><ul class="who">${d.heroes.map((h) => {
        const hero = heroes.find((x) => x.id === h.id);
        const k = EVIDENCE_SRC[hero && hero.evidence] || "diary";
        return `<li data-src="${k}"><span class="av av-animal">${ico("animal")}</span><span>${heroButton(h.id, hero ? hero.name : h.id)}
          <span class="role">${esc(h.event)}</span> ${tag(k)}</span></li>`;
      }).join("")}</ul>`;
    }
    if (photos.length) html += block("europeana", `<h4>${ico("photo")}Fotos von diesem Tag: ${photos.length} ${tag("europeana")}</h4>${photoGrid(photos)}`);
    if (objects.length) html += block("weltmuseum", `<h4>${ico("object")}Objekte der Sammlung Este: ${objects.length} ${tag("weltmuseum")}</h4>${objectList(objects)}
      <p class="note">Vorschläge mit Beleg: das Tagebuch beschreibt Objekte dieser Art an diesem Ort; kein Nachweis für das einzelne Stück.</p>`);
    if (people.length) {
      html += block("vault", `<h4>${ico("people")}Im Tagebuch genannt ${tag("vault")}</h4><ul class="who">${people.map((p) =>
        `<li><span class="av">${initial(p.name)}</span><span>${personButton(p.id, p.name)}
          <span class="role">${esc(p.group)}${p.role ? " · " + esc(p.role) : ""}</span></span></li>`).join("")}</ul>`);
    }
    if ((kl.aboard || []).length) {
      const ranks = Object.entries(kl.aboard_by_rank || {}).map(([r, n]) => `${esc(n)} ${esc(r)}`).join(" · ");
      const medal = kl.aboard.filter((a) => a.medal_note).length;
      html += block("rangliste", `<h4>${ico("aboard")}An Bord: ${kl.aboard.length} Offiziere <span class="h4-sub">Rangliste vom ${esc(fmt(kl.aboard_issue))}</span> ${tag("rangliste")}</h4>
        <p class="note">${ranks}</p>
        <details><summary>Namen${medal ? ` (${medal} mit Seereise-Denkmünze 1892/93)` : ""}</summary><ul class="plain">${
          kl.aboard.map((a) => `<li>${esc(a.name)}, ${esc(a.rank)}${a.medal_note ? " ✓ Denkmünze" : ""}</li>`).join("")}</ul></details>
        <p class="note">Rangliste KI-gestützt transkribiert, ungeprüft; nennt den Stab, nicht die ganze Mannschaft.</p>`);
    }
    return html;
  }

  function selectDay(i, pan = true) {
    current = Math.max(0, Math.min(days.length - 1, i));
    const d = days[current];
    sel.value = String(current);
    document.getElementById("card").innerHTML = dayCard(d);
    updateProgress();
    updateTimeline();
    // Follow the ship, but only move the map when it leaves the view (smooth while scrubbing)
    const ll = shipAt(current).ll;
    if (pan) map.panInside(ll, view());
    history.replaceState(null, "", `#${d.date}`);
  }
  // Play: one day every 0.7 s from the current day; any other choice of day keeps it running
  const playBtn = document.getElementById("play");
  let playing = null;
  const stopPlay = () => {
    clearInterval(playing); playing = null;
    playBtn.textContent = "▶"; playBtn.setAttribute("aria-label", "Reise abspielen");
  };
  playBtn.addEventListener("click", () => {
    if (playing) return stopPlay();
    showTab("day");
    if (current >= days.length - 1) selectDay(0);
    playBtn.textContent = "❚❚"; playBtn.setAttribute("aria-label", "Anhalten");
    playing = setInterval(() => (current >= days.length - 1 ? stopPlay() : selectDay(current + 1)), 700);
  });
  sel.addEventListener("change", () => selectDay(Number(sel.value)));
  document.getElementById("prev").addEventListener("click", () => selectDay(current - 1));
  document.getElementById("next").addEventListener("click", () => selectDay(current + 1));
  document.addEventListener("keydown", (e) => {
    if (["SELECT", "INPUT"].includes(e.target.tagName) || document.getElementById("view-day").hidden) return;
    if (e.key === "ArrowRight") selectDay(current + 1);
    if (e.key === "ArrowLeft") selectDay(current - 1);
  });

  // --- timeline -------------------------------------------------------------------------
  // One column per day, one row per layer (colours as on the map). Press is placed at the
  // day the issue appeared, so the echo trails the hunts by weeks.
  const tlTrack = document.getElementById("tl-track");
  const tlSvg = document.getElementById("tl-svg");
  const tlHover = document.getElementById("tl-hover");
  const N = days.length, ROW = 12, LAND = "#7AA63A";   // yellow-green: apart from the sea blue and the press teal
  const pressByDay = new Map();
  let pressLater = 0;
  for (const p of E.press) {
    if (dayIndex.has(p.date)) pressByDay.set(p.date, (pressByDay.get(p.date) || 0) + 1);
    else if (p.date > days[N - 1].date) pressLater += 1;
  }
  const rect = (x, row, w, color, op, src) =>
    `<rect x="${x}" y="${row * ROW + 1}" width="${w}" height="${ROW - 2}" fill="${color}" fill-opacity="${op.toFixed(2)}"${src ? ` class="src-${src}"` : ""}/>`;
  const level = (n, full) => 0.3 + 0.7 * Math.min(1, n / full);
  let svg = "";
  days.forEach((d, i) => {
    svg += d.lat !== null ? rect(i, 0, 1.02, LAND, 0.85, coordSrc(d)) : rect(i, 0, 1.02, d.coords === "sea" ? "#a9c7d8" : "#d6d0c4", 0.6);
  });
  for (const ep of episodes) {
    const a = dayIndex.get(ep.start), b = dayIndex.get(ep.end);
    if (a !== undefined && b !== undefined) svg += rect(a, 1, b - a + 1, HUNT, 0.15, "diary");
  }
  days.forEach((d, i) => {
    if (d.hunt) svg += rect(i, 1, 1.02, HUNT, level(d.hunt.n, 8), "diary");
    if (pressByDay.has(d.date)) svg += rect(i, 2, 1.02, PRESS, level(pressByDay.get(d.date), 4), "anno");
    if (d.photos.length) svg += rect(i, 3, 1.02, PHOTO, level(d.photos.length, 6), "europeana");
    if (d.objects.length) svg += rect(i, 4, 1.02, OBJECT, level(d.objects.length, 6), "weltmuseum");
    if (d.heroes.length) {
      const hero = heroes.find((x) => x.id === d.heroes[0].id);
      svg += rect(i, 5, 1.02, HERO, level(d.heroes.length, 2), EVIDENCE_SRC[hero && hero.evidence] || "diary");
    }
  });
  tlSvg.setAttribute("viewBox", `0 0 ${N} ${6 * ROW}`);
  tlSvg.innerHTML = svg;
  // Month ticks
  document.getElementById("tl-months").innerHTML = days.map((d, i) => {
    if (i > 0 && !d.date.endsWith("-01")) return "";
    const [y, m] = d.date.split("-");
    const name = ["Jän", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"][m - 1];
    return `<span style="left:${(i / N) * 100}%">${name}${m === "01" || i === 0 ? " " + y : ""}</span>`;
  }).join("");
  const key = (c, op, t) => `<span class="key" style="background:${c};opacity:${op}"></span> ${t}`;
  document.getElementById("tl-note").innerHTML = `Ort: ${key(LAND, 0.85, "an Land")} ${key("#a9c7d8", 0.6, "auf See")}
    ${key("#d6d0c4", 0.6, "ohne Ort")} · Presse nach Erscheinungstag${pressLater ? ` (${pressLater} Ausgaben nach Reiseende nicht gezeigt)` : ""}
    · klicken oder ziehen, ← → Tag, Bild ↑↓ Woche`;

  const dayLabel = (d) => `${fmt(d.date)} · ${d.place || (d.coords === "sea" ? "auf See" : "–")}`;
  function updateTimeline() {
    const d = days[current];
    document.getElementById("tl-cursor").style.left = `${((current + 0.5) / N) * 100}%`;
    const extra = [d.hunt && `Jagd: ${d.hunt.n} ${d.hunt.n === 1 ? "Satz" : "Sätze"}`, pressByDay.get(d.date) && `${pressByDay.get(d.date)} Zeitung(en)`,
      d.photos.length && `${d.photos.length} Foto(s)`, d.objects.length && `${d.objects.length} Objekt(e)`, d.heroes.length && "Tiere"].filter(Boolean);
    document.getElementById("tl-readout").innerHTML = `<b>${esc(dayLabel(d))}</b>${extra.length ? " · " + esc(extra.join(" · ")) : ""}`;
    tlTrack.setAttribute("aria-valuemin", "0");
    tlTrack.setAttribute("aria-valuemax", String(N - 1));
    tlTrack.setAttribute("aria-valuenow", String(current));
    tlTrack.setAttribute("aria-valuetext", dayLabel(d));
  }
  const indexAt = (e) => {
    const r = tlSvg.getBoundingClientRect();
    return Math.max(0, Math.min(N - 1, Math.floor(((e.clientX - r.left) / r.width) * N)));
  };
  const pickDay = (i) => {
    if (document.getElementById("view-day").hidden) showTab("day");
    if (i !== current) selectDay(i);
  };
  tlTrack.addEventListener("pointerdown", (e) => {
    tlTrack.setPointerCapture(e.pointerId);
    tlTrack.focus();
    pickDay(indexAt(e));
  });
  tlTrack.addEventListener("pointermove", (e) => {
    const i = indexAt(e);
    if (tlTrack.hasPointerCapture(e.pointerId)) pickDay(i);
    tlHover.hidden = false;
    tlHover.style.left = `${((i + 0.5) / N) * 100}%`;
    tlHover.textContent = dayLabel(days[i]);
  });
  tlTrack.addEventListener("pointerleave", () => { tlHover.hidden = true; });
  tlTrack.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: -1, ArrowRight: 1, ArrowDown: -1, ArrowUp: 1, PageDown: -7, PageUp: 7 }[e.key];
    let i = null;
    if (step) i = current + step;
    if (e.key === "Home") i = 0;
    if (e.key === "End") i = N - 1;
    if (i === null) return;
    e.preventDefault();
    e.stopPropagation();   // the document handler would step a second time
    pickDay(Math.max(0, Math.min(N - 1, i)));
  });

  // --- hunts ----------------------------------------------------------------------------
  document.getElementById("hunt-list").innerHTML = episodes.map((ep) => `<li><button type="button" data-hunt="${esc(ep.id)}">
      <span class="pick-title">${ico("hunt")}${esc(ep.label)}</span>
      <span class="pick-meta">${esc(span(ep.start, ep.end))} · ${ep.kill_sentences} Sätze · ${ep.anno.issues_high} Zeitungen</span></button></li>`).join("");

  function huntCard(ep) {
    const press = pressOf(ep.id);
    const photos = E.photos.filter((p) => p.hunt === ep.id);
    const epDays = days.filter((d) => d.date >= ep.start && d.date <= ep.end);
    const objects = [...new Set(epDays.flatMap((d) => d.objects))].map((i) => E.objects[i]);
    const h = ep.hoefer || {};
    const animals = Object.fromEntries(ep.animals.map((a) => [a.id, a.mentions]));
    return `<p class="kicker">Jagd · ${esc(span(ep.start, ep.end))}</p><h3>${esc(ep.label)}</h3>
      <div class="meta">${esc(span(ep.start, ep.end))} · ${ep.kill_sentences} Sätze vom Erlegen/Schießen ${tag("diary")}
        ${ep.places.map((p) => p.wikidata ? `<span data-src="lod"> · ${link(`https://www.wikidata.org/wiki/${p.wikidata}`, p.wikidata)} ${tag("lod")}</span>` : "").join("")}</div>
      ${ep.places.some((p) => p.coord_note) ? `<p class="note" data-src="inferred">${esc(ep.places.map((p) => p.coord_note).filter(Boolean).join("; "))} ${tag("inferred")}</p>` : ""}
      ${h.from ? `<p class="note" data-src="hoefer">Aufenthalt laut Höfer 2010: ${esc(span(h.from, h.to))}${(h.stays || []).length ? ` (${esc(h.stays.map((s) => s.stay).join(", "))})` : ""}${h.days_without_hunting_entry ? `; ${h.days_without_hunting_entry} Tage davon ohne Jagdsatz im Tagebuch` : ""}. ${tag("hoefer")}</p>` : ""}
      <h4>${ico("days")}Tage der Jagd</h4>
      <p class="pills">${epDays.map((d) => `<span class="pill${d.hunt ? " hd" : ""}" title="${d.hunt ? "Jagdsätze im Tagebuch" : "ohne Jagdsatz"}">${
        dayButton(d.date, d.date.slice(5).split("-").reverse().join("."))}</span>`).join("")}</p>
      ${block("diary", `<h4>${ico("hunt")}Tiere in den Sätzen (Erwähnungen) ${tag("diary")}</h4>${chips(animals)}
      ${ep.people.length ? `<h4>${ico("people")}Mitjagende im Tagebuch genannt</h4><ul class="who">${ep.people.map((p) =>
        `<li><span class="av">${initial(p.name)}</span><span>${E.people[p.id] ? personButton(p.id, p.name) : esc(p.name)}
          <span class="role">${esc(p.group)} · ${p.kill_sentences} ${p.kill_sentences === 1 ? "Jagdsatz" : "Jagdsätze"}</span></span></li>`).join("")}</ul>` : ""}
      <h4>${ico("diary")}Im Tagebuch ${tag("diary")}</h4>${ep.quotes.map((q) => quote(q, `<br><span class="note">${dayButton(q.date)} · ${link(scanUrl(q.band, q.scan), "Scan")}${q.first_person ? " · Ich-Form" : ""}</span>`)).join("")}`)}
      ${block("anno", `<h4>${ico("press")}Presse (ANNO): ${ep.anno.issues_found} Ausgaben gefunden, ${ep.anno.issues_high} mit hoher Relevanz ${tag("anno")}</h4>
      <p class="note">Suchfenster ${esc(span(ep.anno.window[0], ep.anno.window[1]))}. Die Presse erschien meist Wochen später und stützte sich auf Telegramme.</p>
      ${press.length ? `<ul class="records">${press.map(pressItem).join("")}</ul>` : "<p class='note'>Keine Ausgabe mit einem passenden Ausschnitt.</p>"}`)}
      ${photos.length ? block("europeana", `<h4>${ico("photo")}Fotos der Reisefotografen: ${photos.length} ${tag("europeana")}</h4>${photoGrid(photos)}`) : ""}
      ${ep.photos_hoefer.length ? block("hoefer", `<h4>${ico("photo")}Weitere Fotos (Höfer 2010, Commons) ${tag("hoefer")}</h4><ul class="records">${ep.photos_hoefer.map((p) => `<li class="${p.image ? "" : "noimg"}">
        ${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : ""}<div>${link(p.url, p.title)}
        <div class="meta">${esc(p.source)}${p.vf_id ? " · " + esc(p.vf_id) : ""} · ${esc(fmt(p.date))}${p.rights ? ` <span class="lic">${esc(p.rights)}</span>` : ""}</div></div></li>`).join("")}</ul>`) : ""}
      ${objects.length ? block("weltmuseum", `<h4>${ico("object")}Objekte der Sammlung Este an diesen Tagen: ${objects.length} ${tag("weltmuseum")}</h4>${objectList(objects)}`) : ""}
      ${ep.kulturpool.length ? block("kulturpool", `<h4>${ico("archive")}Kulturpool ${tag("kulturpool")}</h4><ul class="records">${ep.kulturpool.map((r) => `<li class="noimg"><div>${link(r.url, r.title)}
        <div class="meta">${esc(r.provider)} <span class="lic">${esc(r.rights || "")}</span> ${r.direct ? "· zur Reise" : "· nur der Ort, nicht die Reise"}</div></div></li>`).join("")}</ul>`) : ""}`;
  }

  // move = false for clicks on the map itself: the map stays where the user put it
  function selectHunt(id, move = true) {
    const ep = epById.get(id);
    if (!ep) return;
    // the timeline and the ship follow to the first day of the hunt
    if (dayIndex.has(ep.start)) selectDay(dayIndex.get(ep.start), false);
    showTab("hunt");
    for (const b of document.querySelectorAll("#hunt-list button")) b.setAttribute("aria-current", String(b.dataset.hunt === id));
    document.getElementById("hunt-card").innerHTML = huntCard(ep);
    document.getElementById("hunt-card").scrollIntoView({ block: "nearest" });
    const pts = ep.places.filter((p) => p.lat != null).map((p) => pos(p.lat, wrap(p.lon)));
    if (move && pts.length) map.flyToBounds(pts, { maxZoom: 6, duration: 0.6, ...view() });
    history.replaceState(null, "", `#${id}`);
  }

  // --- live animals ---------------------------------------------------------------------
  document.getElementById("hero-list").innerHTML = heroes.map((h) => `<li><button type="button" data-hero="${esc(h.id)}">
      <span class="pick-title">${ico("animal")}${esc(h.name)}</span>
      <span class="pick-meta"><span class="status s-${esc(h.status)}">${esc(STATUS[h.status] || h.status)}</span> · ${esc(EVIDENCE[h.evidence] || h.evidence)}</span></button></li>`).join("");

  function heroCard(h) {
    const cite = (x) => `<blockquote>${esc(x.quote)}<br><span class="note">${x.newspaper
      ? `${esc(x.newspaper)}, ${esc(fmt(x.date))} · ${link(x.url, `ANNO S. ${x.page}`)}`
      : x.day ? `${dayButton(x.day)} · ${link(x.url, "franzferdinandsworld.com")}`
        : `${dayButton(x.date)} · ${link(x.page_url, "Scan")}`}</span></blockquote>`;
    const ek = EVIDENCE_SRC[h.evidence] || "diary";
    return `<h3>${esc(h.name)}</h3>
      <div class="meta">${esc(h.species_de)} · <span class="status s-${esc(h.status)}">${esc(STATUS[h.status] || h.status)}</span> · Beleg: ${esc(EVIDENCE[h.evidence] || h.evidence)} ${tag(ek)}</div>
      <h4>${ico("route")}Weg</h4><ol class="plain">${h.route.map((r) => {
        const k = EVIDENCE_SRC[r.evidence] || ek;
        return `<li data-src="${k}">${r.date ? dayButton(r.date) : "<span class='note'>ohne Datum</span>"} · ${esc(r.label)}: ${esc(r.event)} ${tag(k)}</li>`;
      }).join("")}</ol>
      ${h.note ? `<p class="note" data-src="inferred">${esc(h.note)} ${tag("inferred")}</p>` : ""}
      ${(h.diary || []).length ? block("diary", `<h4>${ico("diary")}Tagebuch ${tag("diary")}</h4>${h.diary.map(cite).join("")}`) : ""}
      ${(h.site || []).length ? block("site", `<h4>${ico("diary")}Übersetzung (fehlende Seiten der OCR) ${tag("site")}</h4>${h.site.map(cite).join("")}`) : ""}
      ${(h.press || []).length ? block("anno", `<h4>${ico("press")}Presse ${tag("anno")}</h4>${h.press.map(cite).join("")}`) : ""}`;
  }

  function selectHero(id, move = true) {
    const h = heroes.find((x) => x.id === id);
    if (!h) return;
    showTab("heroes");
    showLayer("heroes");
    for (const b of document.querySelectorAll("#hero-list button")) b.setAttribute("aria-current", String(b.dataset.hero === id));
    document.getElementById("hero-card").innerHTML = heroCard(h);
    document.getElementById("hero-card").scrollIntoView({ block: "nearest" });
    currentHero = id;
    highlightHero(id);
    const hl = heroLine.get(id);
    if (move && hl) map.flyToBounds(hl.pts, { maxZoom: 5, duration: 0.6, ...view() });
    history.replaceState(null, "", `#${id}`);
  }
  const keepers = E.heroes_people.map((p) => `<li><b>${esc(p.name)}</b>: ${esc(p.role)}</li>`).join("");
  if (keepers) {
    document.getElementById("hero-list").insertAdjacentHTML("afterend",
      `<details class="keepers"><summary>Wer die Tiere versorgte</summary><ul class="plain">${keepers}</ul></details>`);
  }

  // --- people ---------------------------------------------------------------------------
  // All people of the voyage (enrichment/data/people.json ← normalization/json/personen.json + Ranglisten),
  // grouped by their part in the voyage; the diary names fewer than half of them.
  const GROUPS = ["Begleitung", "Wissenschaft", "Diener", "Besatzung", "Gastgeber", "Kontakt"];
  const GND = {
    none: "nicht in der GND gefunden", undated: "GND-Treffer ohne Lebensdaten, nicht verknüpft",
    implausible: "GND-Treffer passt nicht zur Person, nicht verknüpft", unconfirmed: "GND-Treffer nicht bestätigt",
    not_searched: "GND nicht gesucht (kein vollständiger Name)",
  };
  const personIds = Object.keys(E.people);
  const people = personIds.map((id) => ({ id, ...E.people[id] }))
    .sort((a, b) => GROUPS.indexOf(a.group) - GROUPS.indexOf(b.group) || b.days - a.days || a.name.localeCompare(b.name, "de"));
  const ps = E.person_sources;

  function personDetail(p) {
    const ids = [p.gnd && link(p.gnd, "GND"), p.wikidata && link(`https://www.wikidata.org/wiki/${p.wikidata}`, "Wikidata")].filter(Boolean)
      .map((x) => `<span data-src="lod">${x}</span>`);
    return `<details class="person" id="person-${esc(p.id)}"><summary><span class="av">${initial(p.name)}</span><b>${esc(p.name)}</b>
        ${p.days ? `<span class="badge" title="Tage im Tagebuch">${p.days} T.</span>` : ""}${p.kill_sentences ? `<span class="badge hunt" title="Sätze vom Erlegen, die die Person nennen">${p.kill_sentences} J.</span>` : ""}
        <span class="note">${esc([p.role, ...p.ranks].filter(Boolean).join(" · ") || p.group)}</span></summary>
      <div class="meta">${esc(p.group)}${p.life ? " · " + esc(p.life) : ""}${p.professions ? " · " + esc(p.professions.join(", ")) : ""}
        ${ids.length ? " · " + ids.join(" · ") + " " + tag("lod") : ""}</div>
      ${p.wikidata_description ? `<p class="note" data-src="lod">Wikidata: ${esc(p.wikidata_description)} ${tag("lod")}</p>` : ""}
      ${!p.gnd && GND[p.gnd_status] ? `<p class="note">${esc(GND[p.gnd_status])}</p>` : ""}
      ${p.gnd_note ? `<p class="note">${esc(p.gnd_note)}</p>` : ""}
      ${p.possible_duplicate ? `<p class="note">Vielleicht dieselbe Person wie: ${esc([].concat(p.possible_duplicate).join(", "))}</p>` : ""}
      ${p.vault_note ? `<p class="note" data-src="vault">Vault: <code>${esc(p.vault_note)}</code> ${tag("vault")}</p>` : `<p class="note">Keine Notiz im Vault (aus Rangliste oder Tagebuch).</p>`}
      ${block("diary", `${p.days ? `<h4>${ico("diary")}Im Tagebuch an ${p.days} ${p.days === 1 ? "Tag" : "Tagen"} ${tag("diary")}</h4><p class="days">${p.dates.map((d) => dayButton(d, d.slice(5).split("-").reverse().join(".") + "." + d.slice(2, 4))).join(" ")}</p>`
        : `<p class="note">Das Tagebuch nennt diese Person nicht beim Namen.</p>`}
      ${p.hunts.length ? `<p class="note">Jagden: ${p.hunts.map((id) => huntButton(id, (epById.get(id) || { label: id }).label)).join(", ")}</p>` : ""}
      ${p.kill_quotes.map((q) => `<blockquote>${esc(q.text)}<br><span class="note">${dayButton(q.date)}</span></blockquote>`).join("")}`)}
      ${p.anno_total ? block("anno", `<h4>${ico("press")}ANNO: ${p.anno_total} Ausgaben (Name + Erzherzog + Reise) ${tag("anno")}</h4>
        <p class="note">Automatische Suche, ungeprüft: trifft auch Namensvettern.</p>
        ${p.anno.map((x) => `<blockquote class="press">${marked(x.snippet)}<br><span class="note">${link(x.url, x.title)}</span></blockquote>`).join("")}`) : ""}
      ${p.kulturpool.length ? block("kulturpool", `<h4>${ico("archive")}Kulturpool: ${p.kulturpool_found} Treffer zum Namen ${tag("kulturpool")}</h4><ul class="records">${p.kulturpool.map((r) =>
        `<li class="noimg"><div>${link(r.url, r.title)}<div class="meta">${esc(r.provider)}${r.date ? " · " + esc(r.date) : ""}</div></div></li>`).join("")}</ul>`) : ""}
    </details>`;
  }

  function renderPeople(group, namedOnly) {
    const list = people.filter((p) => (group === "Alle" || p.group === group) && (!namedOnly || p.days));
    document.getElementById("people-list").innerHTML = GROUPS.filter((g) => list.some((p) => p.group === g)).map((g) => {
      const inGroup = list.filter((p) => p.group === g);
      return `<h4>${ico("people")}${esc(g)} (${inGroup.length})</h4>${inGroup.map(personDetail).join("")}`;
    }).join("") || "<p class='note'>Niemand in dieser Auswahl.</p>";
  }
  function selectPerson(id) {
    showTab("people");
    const p = E.people[id];
    if (!p) return;
    document.getElementById("people-group").value = "Alle";
    document.getElementById("people-named").checked = false;
    renderPeople("Alle", false);
    const el = document.getElementById(`person-${id}`);
    el.open = true;
    el.scrollIntoView({ block: "start" });
    history.replaceState(null, "", `#${id}`);
  }
  document.getElementById("panel").addEventListener("click", (e) => {
    const b = e.target.closest("[data-person]");
    if (b) selectPerson(b.dataset.person);
  });

  const named = people.filter((p) => p.days).length;
  document.getElementById("people").innerHTML = `<p class="note">${people.length} Menschen der Reise aus dem Vault
      (<code>normalization/json/personen.json</code>) und den Ranglisten; das Tagebuch nennt ${named} von ihnen.</p>
    <div class="filters">
      <label>Gruppe <select id="people-group">${["Alle", ...GROUPS].map((g) =>
        `<option>${esc(g)}</option>`).join("")}</select></label>
      <label><input type="checkbox" id="people-named"> nur im Tagebuch genannt</label>
    </div>
    <div id="people-list"></div>
    <h4>${ico("people")}Gezielt gesucht: Jäger, Kapitän, Fotografen, Ärzte</h4>
    <p class="note">Treffer in allen Quellen; behalten nur, wenn die Person mit ihrer Rolle oder der Reise genannt ist (gefunden / behalten).</p>
    ${ps.map((p) => `<details><summary><b>${esc(p.name)}</b> · ${esc(p.role)}</summary>
      <p class="note">${Object.entries(p.sources).map(([s, v]) => `${esc(SOURCE[s] || s)} ${v.raw}/${v.kept}`).join(" · ")}</p>
      ${Object.entries(p.sources).flatMap(([s, v]) => v.items.map((it) => `<blockquote data-src="${PS_SRC[s] || "inferred"}">${esc(it.text || it.snippet || it.title || "")}<br>
        <span class="note">${tag(PS_SRC[s] || "inferred")}${it.date ? " · " + (s === "diary" ? dayButton(it.date) : esc(fmt(it.date))) : ""}
        ${link(it.page_url || it.url, "Quelle")}</span></blockquote>`)).join("")}</details>`).join("")}`;
  const peopleFilter = () => renderPeople(document.getElementById("people-group").value, document.getElementById("people-named").checked);
  document.getElementById("people-group").addEventListener("change", peopleFilter);
  document.getElementById("people-named").addEventListener("change", peopleFilter);
  peopleFilter();

  // --- echo: press over time, topics, Kulturpool, photographers -------------------------
  const cov = E.anno_coverage;
  const max = Math.max(...cov.map((m) => m.issues_ff));
  document.getElementById("echo").innerHTML = `<div data-src="anno"><h4>${ico("press")}Franz Ferdinand in ANNO, Ausgaben pro Monat ${tag("anno")}</h4>
    <div class="bars" role="img" aria-label="Ausgaben pro Monat, die Franz Ferdinand nennen, und davon mit Jagd">${cov.map((m) => `
      <div class="bar" title="${esc(m.month)}: ${m.issues_ff} Ausgaben, ${m.issues_ff_hunting} mit Jagd">
        <span class="all" style="height:${(m.issues_ff / max) * 100}%"><span class="hunt" style="height:${m.issues_ff ? (m.issues_ff_hunting / m.issues_ff) * 100 : 0}%"></span></span>
        <span class="lbl">${esc(m.month.slice(5))}</span></div>`).join("")}</div>
    <p class="note"><span class="key all"></span> nennt Franz Ferdinand oder den Thronfolger · <span class="key hunt"></span> davon mit Jagd, Tiger, Elefant …
      (Dezember 1892 bis Dezember 1893; Abfragen in <code>enrichment/02_anno.py</code>)</p>
    ${E.anno_topics.map((t) => `<h4>${ico("press")}${esc(t.label)} (${esc(span(t.start, t.end))}): ${t.total} Ausgaben</h4>
      <ul class="records">${t.documents.map((x) => `<li class="noimg"><div>${link(x.url, x.title)}
        ${x.snippet ? `<blockquote class="press">${marked(x.snippet)}</blockquote>` : ""}</div></li>`).join("")}</ul>`).join("")}</div>
    <div data-src="kulturpool"><h4>${ico("archive")}Kulturpool: Akten und Bücher zur Reise ${tag("kulturpool")}</h4>
    <p class="note">Die Objekte selbst liegen großteils im Weltmuseum Wien und im Naturhistorischen Museum;
      das Weltmuseum liefert nicht an den Kulturpool.</p>
    <ul class="records">${E.kulturpool.map((r) => `<li class="${r.image ? "" : "noimg"}">${r.image ? `<img src="${esc(r.image)}" alt="" loading="lazy">` : ""}<div>
      ${link(r.url, r.title)}<div class="meta">${esc(r.provider)}${r.year ? " · " + esc(r.year) : ""} <span class="lic">${esc(r.rights || "")}</span>
      ${r.tier === "modern" ? " · heutige Aufarbeitung" : ""}</div></div></li>`).join("")}</ul></div>
    <div data-src="europeana"><h4>${ico("photo")}Fotografen der Reise in Europeana ${tag("europeana")}</h4>
    <ul class="plain">${E.photographers.map((p) => `<li>${esc(p.name)}: ${esc(p.role)} · ${p.kept} Fotos</li>`).join("")}</ul>
    <details><summary>Alle ${E.photos.length} Fotos</summary>${photoGrid(E.photos)}</details></div>`;

  // Start from the URL hash: a day (#1893-02-24), a hunt (#hunt-1893-02-20-alwar), an animal (#fips-mucki)
  // or a person (#ke-person-a49d32e030)
  const fromHash = decodeURIComponent(location.hash.slice(1));
  selectDay(dayIndex.has(fromHash) ? dayIndex.get(fromHash) : 0, dayIndex.has(fromHash));
  if (epById.has(fromHash)) selectHunt(fromHash);
  else if (heroes.some((h) => h.id === fromHash)) selectHero(fromHash);
  else if (E.people[fromHash]) selectPerson(fromHash);
  // The welcome sheet greets a plain visit; deep links go straight to their content
  if (!fromHash) { welcome.hidden = false; document.getElementById("start").focus(); }
})();
