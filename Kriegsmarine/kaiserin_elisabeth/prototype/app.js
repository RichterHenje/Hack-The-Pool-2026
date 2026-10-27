/* SMS Kaiserin Elisabeth prototype: reads window.KE from data/ke_data.js
   (built by scripts/ke_itinerary.py, ke_places_lpf.py, ke_stop_records.py). */
(function () {
  "use strict";
  const KE = window.KE;
  if (!KE || !window.L) {
    document.getElementById("map").textContent = "Daten oder Karte konnten nicht geladen werden.";
    return;
  }

  // Okabe-Ito palette (colour-blind safe)
  const COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#000000"];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // Segments in itinerary order
  const segOrder = [];
  const segInfo = {};
  for (const s of KE.stops) {
    if (!segInfo[s.segment]) {
      segOrder.push(s.segment);
      segInfo[s.segment] = { label: s.label, years: s.years, onShip: String(s.on_ship) === "True", stops: 0, withRecords: 0 };
    }
    segInfo[s.segment].stops += 1;
    if (s.kp_found > 0) segInfo[s.segment].withRecords += 1;
  }
  segOrder.forEach((seg, i) => { segInfo[seg].color = COLORS[i % COLORS.length]; });

  // Basemap: bundled Natural Earth coastline (data/world.js), no tile server. OpenStreetMap
  // tiles refuse requests without a referer, which a page opened from disk does not send.
  const map = L.map("map", { zoomControl: true, minZoom: 1, maxZoom: 8 });
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution("Küsten: Natural Earth · Orte: GeoNames (CC BY 4.0)");
  if (window.WORLD) {
    L.geoJSON(window.WORLD, {
      interactive: false,
      style: { color: "#b9c4c4", weight: 0.8, fillColor: "#f6f3ea", fillOpacity: 1 },
    }).addTo(map);
  }

  const groups = {};
  segOrder.forEach((seg) => { groups[seg] = L.layerGroup().addTo(map); });

  // Route lines
  for (const f of KE.routes.features) {
    const seg = f.properties.segment;
    if (!groups[seg]) continue;
    const latlngs = f.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
    L.polyline(latlngs, {
      color: segInfo[seg].color,
      weight: 3,
      opacity: 0.8,
      dashArray: segInfo[seg].onShip ? null : "6 6",
    }).bindTooltip(`${esc(segInfo[seg].label)} (${esc(segInfo[seg].years)})`, { sticky: true })
      .addTo(groups[seg]);
  }

  // Stops
  const allBounds = [];
  const markers = [];
  for (const s of KE.stops) {
    const lat = Number(s.latitude), lon = Number(s.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
    allBounds.push([lat, lon]);
    const m = L.circleMarker([lat, lon], {
      radius: s.kp_found > 0 ? 7 : 5,
      color: "#fff",
      weight: 1.5,
      fillColor: segInfo[s.segment].color,
      fillOpacity: s.kp_found > 0 ? 0.95 : 0.6,
    });
    m.bindTooltip(`${s.seq}. ${esc(s.place_note)}`);
    m.bindPopup(() => popup(s), { maxWidth: 320 });
    m.addTo(groups[s.segment]);
    markers.push([s, m]);
  }
  if (allBounds.length) map.fitBounds(allBounds, { padding: [24, 24] });

  // Deep link: #stop=Colombo opens the first stop whose note title starts with that text
  function openFromHash() {
    const m = decodeURIComponent(location.hash).match(/^#stop=(.+)$/);
    if (!m) return;
    const want = m[1].toLowerCase();
    const hit = markers.find(([s]) => s.place_note.toLowerCase().startsWith(want));
    if (hit) { map.setView(hit[1].getLatLng(), 5); hit[1].openPopup(); }
  }
  window.addEventListener("hashchange", openFromHash);

  function recordItem(r) {
    const img = r.open && r.image
      ? `<img src="${esc(r.image)}" alt="" loading="lazy">` : "";
    return `<li class="${img ? "" : "noimg"}">${img}<div>
      <a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title) || "(ohne Titel)"}</a>
      <div class="meta">${esc(r.provider)}${r.date ? " · " + esc(r.date) : ""}
        <span class="lic">${r.open ? "offen" : esc(r.licence)}</span></div></div></li>`;
  }

  function popup(s) {
    const info = KE.places[s.place_note] || { names: [], links: [] };
    const names = info.names.map((n) => {
      const span = n.from || n.to ? ` ${esc(n.from)}–${esc(n.to)}` : "";
      const lang = n.lang ? ` <small>${esc(n.lang)}</small>` : "";
      const title = n.kind === "attested"
        ? "im Vault für diese Reise verwendet"
        : `${n.kind}${span ? ", gültig" + span : ""}`;
      return `<span class="name ${esc(n.kind)}" title="${esc(title)}">${esc(n.name)}${lang}${n.kind === "attested" ? "" : span}</span>`;
    }).join("");
    const links = info.links.map((u) => {
      const label = u.includes("wikidata") ? "Wikidata" : u.includes("geonames") ? "GeoNames" : "Link";
      return `<a href="${esc(u)}" target="_blank" rel="noopener">${label}</a>`;
    }).join("");
    const recs = s.kp_records.length
      ? `<ul class="records">${s.kp_records.map(recordItem).join("")}</ul>`
      : `<p class="caveat">Keine Kulturpool-Datensätze mit diesen Namen im Zeitfenster.</p>`;
    return `<div class="pop">
      <h3>${esc(s.place_note)}</h3>
      <div class="where">${esc(segInfo[s.segment].label)} · Station ${esc(s.seq)} · ${esc(s.years)}</div>
      <h4>Namen</h4><div class="names">${names || "<span class='name'>" + esc(s.geo_name) + "</span>"}</div>
      <div class="links">${links}</div>
      <h4>Kulturpool ${esc(s.window)}: ${s.kp_found} Treffer</h4>
      ${recs}
      <p class="caveat">Gesucht: ${s.query_names.map(esc).join(", ")}. Treffer nennen den Ort, sie stammen nicht von der Reise.</p>
    </div>`;
  }

  // Panel: segment toggles
  const ul = document.getElementById("segments");
  for (const seg of segOrder) {
    const i = segInfo[seg];
    const li = document.createElement("li");
    li.innerHTML = `<button type="button" aria-pressed="true">
      <span class="swatch ${i.onShip ? "" : "dashed"}" style="background:${i.color};color:${i.color}"></span>
      <span class="seg-label">${esc(i.label)}<small>${esc(i.years)}${i.onShip ? "" : " · ohne das Schiff"}</small></span>
      <span class="seg-meta">${i.stops} Orte · ${i.withRecords} mit Treffern</span></button>`;
    const btn = li.querySelector("button");
    btn.addEventListener("click", () => {
      const on = btn.getAttribute("aria-pressed") === "true";
      btn.setAttribute("aria-pressed", String(!on));
      if (on) map.removeLayer(groups[seg]); else groups[seg].addTo(map);
    });
    ul.appendChild(li);
  }

  // Panel: stats
  const mapped = KE.stops.length;
  const withRec = KE.stops.filter((s) => s.kp_found > 0).length;
  const stats = [
    [KE.n_itinerary_stops, "Stationen im Vault (Reihenfolge wie notiert)"],
    [mapped, "davon auf der Karte"],
    [withRec, "Stationen mit Kulturpool-Treffern im Zeitfenster"],
    [KE.ship_records.length, "Kulturpool-Datensätze, die das Schiff nennen"],
    [Object.keys(KE.places).length, "Orte mit Namensgeschichte (Linked Places)"],
  ];
  document.getElementById("stats").innerHTML = stats
    .map(([n, t]) => `<dt>${esc(n)}</dt><dd>${esc(t)}</dd>`).join("");

  document.getElementById("ship-records").innerHTML = KE.ship_records.length
    ? KE.ship_records.map(recordItem).join("")
    : "<li class='noimg'>Keine Treffer.</li>";

  document.getElementById("unmapped-summary").textContent =
    `Stationen ohne Koordinaten (${KE.unmapped.length})`;
  document.getElementById("unmapped").innerHTML = KE.unmapped.map((u) => `<li>${esc(u)}</li>`).join("");
  document.getElementById("generated").textContent = `Datenstand ${KE.generated}. ${KE.attribution}.`;
  openFromHash();
})();
