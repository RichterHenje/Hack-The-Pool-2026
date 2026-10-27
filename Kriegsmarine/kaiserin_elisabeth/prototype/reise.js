/* Reise 1892–93: the diary as the route spine (data/ke_diary.js, built by scripts/ke_diary.py).
   Also reads data/ke_data.js (Kulturpool records per place) and data/world.js (coastline). */
(function () {
  "use strict";
  const D = window.KED, KE = window.KE;
  if (!D || !window.L) {
    document.getElementById("map").textContent = "Daten oder Karte konnten nicht geladen werden.";
    return;
  }
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const KIND = { stay: "Aufenthalt", transfer: "Ortswechsel", at_sea: "auf See", unknown: "Ort fehlt" };
  const ROUTE = "#0072B2", HUNT = "#D55E00", PRESS = "#009E73", KP = "#CC79A7";
  const days = D.days;
  const presse = D.presse || [];

  const map = L.map("map", { minZoom: 1, maxZoom: 8 });
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution("Küsten: Natural Earth · Orte: GeoNames (CC BY 4.0)");
  if (window.WORLD) {
    // Drawn twice (second copy shifted by 360°) so the unwrapped route east of Japan
    // (North America at longitudes > 180) still has land under it.
    const landStyle = { color: "#b9c4c4", weight: 0.8, fillColor: "#f6f3ea", fillOpacity: 1 };
    L.geoJSON(window.WORLD, { interactive: false, style: landStyle }).addTo(map);
    L.geoJSON(window.WORLD, { interactive: false, style: landStyle,
      coordsToLatLng: (c) => L.latLng(c[1], c[0] + 360) }).addTo(map);
  }

  const routeLayer = L.layerGroup().addTo(map);
  const huntLayer = L.layerGroup().addTo(map);
  const pressLayer = L.layerGroup().addTo(map);
  const kpLayer = L.layerGroup();

  // Route: located days in date order. Longitudes are unwrapped so the Pacific crossing
  // (Yokohama → Vancouver) runs east across the Pacific, not back across Asia and Europe.
  const located = days.filter((d) => d.lat !== null);
  let prevLon = null;
  for (const d of located) {
    let lon = d.lon;
    while (prevLon !== null && lon - prevLon > 180) lon -= 360;
    while (prevLon !== null && lon - prevLon < -180) lon += 360;
    d.lon = lon;
    prevLon = lon;
  }
  L.polyline(located.map((d) => [d.lat, d.lon]), { color: ROUTE, weight: 2.5, opacity: 0.7 }).addTo(routeLayer);
  const markerOf = new Map();
  for (const d of located) {
    const m = L.circleMarker([d.lat, d.lon], { radius: 4, color: "#fff", weight: 1, fillColor: ROUTE, fillOpacity: 0.9 });
    m.bindTooltip(`${esc(d.date)} · ${esc(d.place_as_printed)}`);
    m.on("click", () => select(days.indexOf(d)));
    m.addTo(routeLayer);
    markerOf.set(d, m);
  }
  // Hunting: days with kill sentences, sized by count
  for (const d of located.filter((x) => x.kill_sentences > 0)) {
    L.circleMarker([d.lat, d.lon], {
      radius: 5 + Math.min(10, d.kill_sentences * 1.5), color: HUNT, weight: 1.5, fillColor: HUNT, fillOpacity: 0.35,
    }).bindTooltip(`${esc(d.date)} · ${d.kill_sentences} Sätze vom Erlegen/Schießen`)
      .on("click", () => select(days.indexOf(d))).addTo(huntLayer);
  }
  // Kulturpool records per place (from the ship prototype, voyage window ±2 years)
  const kpByPlace = new Map();
  for (const s of (KE ? KE.stops : [])) {
    if (s.segment !== "weltreise_1892_93" || !s.kp_records.length) continue;
    kpByPlace.set(s.geo_name, s);
    L.circleMarker([Number(s.latitude), Number(s.longitude)], { radius: 6, color: KP, weight: 2, fill: false })
      .bindTooltip(`${esc(s.place_note)}: ${s.kp_found} Kulturpool-Treffer`).addTo(kpLayer);
  }
  // Press: clippings placed at the diary day they report on (event_date, set by
  // enrichment/05_export_presse.py), else at the diary location of the publication date
  for (const p of presse) {
    const key = p.event_date || p.date;
    const day = days.find((d) => d.date === key && d.lat !== null) ||
      located.filter((d) => d.date <= key).pop();
    if (!day) continue;
    L.circleMarker([day.lat, day.lon], { radius: 7, color: PRESS, weight: 2, fillColor: PRESS, fillOpacity: 0.2 })
      .bindTooltip(`${esc(p.date)} · ${esc(p.newspaper)}`).on("click", () => select(days.indexOf(day))).addTo(pressLayer);
  }
  map.fitBounds(located.map((d) => [d.lat, d.lon]), { padding: [20, 20] });

  const toggle = (id, layer) => document.getElementById(id).addEventListener("change", (e) => {
    if (e.target.checked) layer.addTo(map); else map.removeLayer(layer);
  });
  toggle("lyr-route", routeLayer); toggle("lyr-hunt", huntLayer); toggle("lyr-kp", kpLayer); toggle("lyr-press", pressLayer);

  // Stats
  const huntDays = days.filter((d) => d.kill_sentences > 0);
  document.getElementById("stats").innerHTML = [
    [days.length, `Tagebuchtage, ${days[0].date} bis ${days[days.length - 1].date}`],
    [located.length, "davon auf der Karte (Ort im Ortsverzeichnis)"],
    [huntDays.length, "Tage mit Sätzen vom Erlegen oder Schießen"],
    [days.reduce((n, d) => n + d.kill_sentences, 0), "solche Sätze (ungeprüft)"],
    [presse.length, "Pressestimmen aus ANNO"],
  ].map(([n, t]) => `<dt>${esc(n)}</dt><dd>${esc(t)}</dd>`).join("");

  // Day selector
  const sel = document.getElementById("day");
  sel.innerHTML = days.map((d, i) =>
    `<option value="${i}">${esc(d.date)} · ${esc(d.heading || "–")}</option>`).join("");
  let current = 0;

  function weekPress(date) {
    const t = Date.parse(date);
    return presse.filter((p) => !p.event_date && Math.abs(Date.parse(p.date) - t) <= 3.5 * 864e5);
  }
  const aboutPress = (date) => presse.filter((p) => p.event_date === date);
  const pressQuote = (p) => `<blockquote>${esc(p.quote)}<br><span class="note">${esc(p.newspaper)}, ${esc(p.date)} · <a href="${esc(p.page_url)}" target="_blank" rel="noopener">ANNO</a></span></blockquote>`;

  function card(d) {
    const quotes = d.kill_quotes.map((q) => `<blockquote>${esc(q)}</blockquote>`).join("");
    const animals = d.animals_in_kill_sentences.map((a) => `<span class="chip">${esc(a)}</span>`).join("");
    const kp = kpByPlace.get(d.place);
    const kpHtml = kp ? `<h4>Kulturpool ${esc(kp.window)}: ${esc(kp.kp_found)} Treffer</h4><ul class="records">${
      kp.kp_records.slice(0, 4).map((r) => `<li class="noimg"><div><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
        <div class="meta">${esc(r.provider)}${r.date ? " · " + esc(r.date) : ""} <span class="lic">${r.open ? "offen" : esc(r.licence)}</span></div></div></li>`).join("")}</ul>
      <p class="note">Datensätze nennen den Ort in diesen Jahren; sie stammen nicht von der Reise.</p>` : "";
    const ab = aboutPress(d.date), pr = weekPress(d.date);
    const prHtml = (ab.length ? `<h4>Presse (ANNO) über diesen Tag: ${ab.length}</h4>${ab.map(pressQuote).join("")}
        <p class="note">Automatisch gefunden (ANNO-Suche, Ausschnitt nennt den Erzherzog); erschienen meist Wochen später.</p>` : "") +
      (pr.length ? `<h4>Presse (ANNO), ± 3 Tage</h4>${pr.map(pressQuote).join("")}` : "");
    return `<h3>${esc(d.place_as_printed || d.heading || "–")}</h3>
      <div class="meta">${esc(d.date)} · <span class="kind">${esc(KIND[d.kind] || d.kind)}</span>
        ${d.place && d.place !== d.place_as_printed ? " · heute " + esc(d.place) : ""}
        · Bd. ${esc(d.band)}, <a href="${esc(d.page_url)}" target="_blank" rel="noopener">Scan ${esc(d.scan)}</a></div>
      <p class="note">Überschrift im Druck: „${esc(d.heading || "–")}“</p>
      ${d.kill_sentences ? `<h4>Jagd im Tagebuch: ${d.kill_sentences} ${d.kill_sentences === 1 ? "Satz" : "Sätze"}</h4>
        <div class="chips">${animals}</div>${quotes}
        <p class="note">Wortlaut aus der Texterkennung, am Scan prüfen. Genannte Tiere sind nicht gleich getötete Tiere.</p>` : ""}
      ${kpHtml}${prHtml}`;
  }

  function select(i) {
    current = Math.max(0, Math.min(days.length - 1, i));
    const d = days[current];
    sel.value = String(current);
    document.getElementById("card").innerHTML = card(d);
    const m = markerOf.get(d);
    if (m) { map.panTo(m.getLatLng()); m.openTooltip(); }
  }
  sel.addEventListener("change", () => select(Number(sel.value)));
  document.getElementById("prev").addEventListener("click", () => select(current - 1));
  document.getElementById("next").addEventListener("click", () => select(current + 1));
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "SELECT") return;
    if (e.key === "ArrowRight") select(current + 1);
    if (e.key === "ArrowLeft") select(current - 1);
  });
  const fromHash = decodeURIComponent(location.hash.slice(1));
  const start = days.findIndex((d) => d.date === fromHash);
  select(start >= 0 ? start : 0);
})();
