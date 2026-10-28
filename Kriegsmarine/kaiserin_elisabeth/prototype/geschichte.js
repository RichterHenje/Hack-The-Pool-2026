/* Jagdreise 1892–93: the voyage told in chapters, from data/ke_enrichment.js (enrichment/08_export_prototype.py).
   Chapters: the 18 hunting episodes, the stretches of the voyage between them, and an epilogue for the days
   after Yokohama (25.8.1893), when Franz Ferdinand travelled on without S.M.S. Kaiserin Elisabeth (day.ship false).
   Scrolling sets the current chapter; map and the one-row timeline follow. Deep link: geschichte.html#<chapter id>. */
(function () {
  "use strict";
  const E = window.KEE;
  if (!E || !window.L) {
    document.getElementById("chapters").textContent = "Daten oder Karte konnten nicht geladen werden.";
    return;
  }
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const marked = (s) => esc(s).replace(/&lt;(\/?)mark&gt;/g, "<$1mark>");   // ANNO snippets keep <mark>
  const link = (url, text) => url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text)}</a>` : esc(text);
  const MONTHS = ["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
  const fmt = (iso, year = true) => {
    const [y, m, d] = iso.split("-").map(Number);
    return `${d}. ${MONTHS[m - 1]}${year ? " " + y : ""}`;
  };
  const span = (a, b) => a === b ? fmt(a) : `${fmt(a, a.slice(0, 4) !== b.slice(0, 4))} – ${fmt(b)}`;
  const nextDay = (iso) => new Date(Date.parse(iso) + 864e5).toISOString().slice(0, 10);
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  // 'Kandy to Kalawewa, Ceylon' → 'Kalawewa'; days at sea → null
  const shortPlace = (s) => {
    if (!s || /\b(at sea|ocean|red sea|gulf of)\b/i.test(s)) return null;
    s = s.replace(/\(.*?\)|\s+–\s+in \d{4}:.*/g, "").split(";").pop().split(",")[0];
    return s.split(/\s+to\s+|\s+–\s+|\s+—\s+/).pop().trim() || null;
  };
  // A snippet is about Franz Ferdinand if it names him or the heir, or says "Erzherzog" without naming another
  // archduke (his father Karl Ludwig, Otto, Eugen … are in the same papers); same rule as enrichment/02_anno.py
  const OTHER_ARCHDUKE = /Erzherzog(?:s|e|en)?\s+(?:Karl|Carl|Otto|Ludwig|Eugen|Rainer|Albrecht|Wilhelm|Friedrich|Jo[sh]e?ph|Leopold|Johann|Rudolf|Ste[fp]h?an|Ernst|Heinrich|Sigismund|Franz Salvator|Max|Maximilian|Peter)\b|Erzherzogin/i;
  const namesFF = (t) => /Franz\s*Ferdinand|Thronfolger/i.test(t) || (/Erzherzog/i.test(t) && !OTHER_ARCHDUKE.test(t));
  const plain = (t) => t.replace(/<\/?mark>/g, "");
  // ANNO marks only the exact search terms; mark the inflected forms too ("des Erzherzogs"), outside existing marks
  const highlight = (html, rx) => html.split(/(<mark>.*?<\/mark>)/).map((part, i) => i % 2 ? part : part.replace(rx, "<mark>$&</mark>")).join("");
  const STATUS = { schoenbrunn: "nach Schönbrunn", vienna: "nach Wien", free: "entflogen", died: "gestorben", unknown: "Verbleib unbekannt" };

  const days = E.days;
  const shipDays = days.filter((d) => d.ship);
  const afterDays = days.filter((d) => !d.ship);
  const episodes = [...E.episodes].sort((a, b) => a.start.localeCompare(b.start));

  // --- chapters ------------------------------------------------------------------------
  const chapters = [];
  const within = (list, a, b) => list.filter((d) => d.date >= a && d.date <= b);
  function voyageChapter(list) {
    const places = [...new Set(list.map((d) => shortPlace(d.place)).filter(Boolean))];
    const title = places.length === 0 ? "Auf See"
      : places.length === 1 ? places[0] : `Von ${places[0]} nach ${places[places.length - 1]}`;
    return { kind: "voyage", id: `fahrt-${list[0].date}`, title, places, days: list,
      start: list[0].date, end: list[list.length - 1].date, slim: list.length < 3 };
  }
  let cursor = shipDays[0].date;
  episodes.forEach((ep, i) => {
    const gap = shipDays.filter((d) => d.date >= cursor && d.date < ep.start);
    if (gap.length) chapters.push(voyageChapter(gap));
    chapters.push({ kind: "hunt", id: ep.id, n: i + 1, ep, title: ep.label.replace(/\s*\(.*?\)/g, ""),
      days: within(shipDays, ep.start, ep.end), start: ep.start, end: ep.end });
    cursor = nextDay(ep.end);
  });
  const rest = shipDays.filter((d) => d.date >= cursor);
  if (rest.length) chapters.push(voyageChapter(rest));
  chapters.push({ kind: "after", id: "heimreise", title: "Heimreise ohne die Kaiserin Elisabeth", days: afterDays,
    start: afterDays[0].date, end: afterDays[afterDays.length - 1].date });
  const chapterOf = (iso) => chapters.find((c) => iso >= c.start && iso <= c.end);

  // --- intro -----------------------------------------------------------------------------
  const kills = episodes.reduce((a, e) => a + e.kill_sentences, 0);
  const shipPress = E.press.filter((p) => episodes.some((e) => e.id === p.episode)).length;
  const shipPhotos = E.photos.filter((p) => p.date && p.date <= E.ship.end).length;
  const live = E.heroes.reduce((a, h) => a + (h.count || 1), 0);
  document.getElementById("lead").textContent =
    `Am ${fmt(shipDays[0].date)} verließ der österreichische Thronfolger Triest an Bord des Kreuzers ` +
    `Kaiserin Elisabeth. Bis Yokohama, wo er am ${fmt(nextDay(E.ship.end))} von Bord ging, jagte er in Ägypten, ` +
    `Ceylon, Indien, Nepal, auf Java, in Australien und auf den Inseln des Pazifiks. Sein Tagebuch, die Zeitungen ` +
    `daheim, Fotos und Objekte zeigen, was erlegt, gesammelt und lebend mitgenommen wurde.`;
  document.getElementById("numbers").innerHTML = [
    [shipDays.length, "Tage an Bord"], [episodes.length, "Jagden"], [kills, "Sätze vom Erlegen im Tagebuch"],
    [shipPress, "Zeitungsausgaben in ANNO"], [shipPhotos, "datierte Fotos"], [live, "lebende Tiere an Bord"],
  ].map(([n, t]) => `<div><dt>${esc(t)}</dt><dd>${n}</dd></div>`).join("");

  // --- chapter content ----------------------------------------------------------------------
  // one large photo; with more photos of the chapter a row of thumbnails below swaps it
  const caption = (p) => `${esc(p.title)} · ${esc(p.creator)} · ${link(p.url, "Weltmuseum Wien")}${p.open ? " · CC BY-NC-SA 4.0" : ""}`;
  const MAX_THUMBS = 12;
  const gallery = (list) => {
    if (!list.length) return "";
    const thumbs = list.length > 1 ? `<div class="thumbs" role="list">${list.slice(0, MAX_THUMBS).map((p, i) =>
      `<button type="button" role="listitem" data-photo="${E.photos.indexOf(p)}" aria-label="${esc(p.title)}"${i === 0 ? ' aria-current="true"' : ""}>
        <img src="${esc(p.preview)}" alt="" loading="lazy"></button>`).join("")}${list.length > MAX_THUMBS ? `<span class="more">+${list.length - MAX_THUMBS}</span>` : ""}</div>` : "";
    return `<figure class="gallery"><img class="main" src="${esc(list[0].preview)}" alt="${esc(list[0].title)}" loading="lazy">
      <figcaption>${list.length > 1 ? `<span class="count">Foto 1 von ${list.length}</span> · ` : ""}${caption(list[0])}</figcaption>${thumbs}</figure>`;
  };
  const dayList = (list) => `<details class="days"><summary>Tag für Tag (${plural(list.length, "Tag", "Tage")})</summary><ol>${
    list.map((d) => `<li><span class="d">${esc(fmt(d.date, false))}</span>${esc(d.place)}${d.hunt ? ' <span class="k">· Jagd</span>' : ""}
      · ${link(d.page_url, "Tagebuch")}${d.site_url ? " · " + link(d.site_url, "Übersetzung") : ""}</li>`).join("")}</ol></details>`;
  const heroEvents = (a, b) => E.heroes.flatMap((h) => (h.route || [])
    .filter((r) => r.date && r.date >= a && r.date <= b)
    .map((r) => `<li><b>${esc(h.name)}</b> (${esc(h.species_de)}): ${esc(r.event)}${r.label ? `, ${esc(r.label)}` : ""}</li>`));
  const objectsIn = (a, b) => E.objects.filter((o) => o.strength === "strong" && o.date && o.date >= a && o.date <= b)
    .slice(0, 4).map((o) => `<li>${link(o.url, [o.type, o.title].filter(Boolean).join(": ") || o.inventory)}
      <span class="src">${esc(o.inventory)}, ${esc(fmt(o.date))}</span></li>`);
  const photosIn = (c) => E.photos.filter((p) => p.preview && (c.kind === "hunt" ? p.hunt === c.id : p.date && p.date >= c.start && p.date <= c.end));

  function huntHTML(c) {
    const ep = c.ep;
    // strong hits first (snippet names the archduke with the place or a specific animal), then by date; quoted are
    // only snippets that name the archduke themselves (a place alone can be a namesake: the Lloyd steamer "Gwalior")
    const press = E.press.filter((p) => p.episode === ep.id)
      .sort((a, b) => (a.relevance !== "high") - (b.relevance !== "high") || a.date.localeCompare(b.date));
    const quotable = press.filter((p) => p.snippets[0] && namesFF(plain(p.snippets[0].text)));
    const others = press.filter((p) => !quotable.includes(p));
    // terms to mark: the archduke, the places and animals of this hunt
    const words = [...ep.places.flatMap((p) => p.label.split(/[\s,()·\/]+/)), ...ep.animals.flatMap((a) => a.label_de.split(/[\s()\/]+/))]
      .filter((w) => w.length > 3 && !/^(sonstige|State|Island)$/i.test(w)).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    const rx = new RegExp(`\\b(?:Erzherzog(?:s|e|en)?(?!in)|Thronfolger(?:s|n)?|Franz\\s+Ferdinand${words.length ? "|" + words.join("|") : ""})\\w*`, "gi");
    const pressItem = (p) => `<li>${highlight(marked(p.snippets[0].text), rx)}
      <span class="src">${link(p.snippets[0].url || p.url, p.newspaper)}, ${esc(fmt(p.date))}${p.snippets[0].page ? `, S. ${esc(p.snippets[0].page)}` : ""}</span></li>`;
    const quotes = ep.quotes.filter((q) => q.checked);
    const quoteItem = (q) => `<blockquote><p>„${esc(q.checked)}“</p>
      <cite>Tagebuch, ${esc(fmt(q.date))} · ${link(q.scan && days.find((d) => d.date === q.date)?.page_url, `Bd. ${q.band}, Scan ${q.scan}`)}</cite></blockquote>`;
    const photos = photosIn(c);
    const hunters = (ep.people || []).filter((p) => p.kill_sentences);
    const heroes = heroEvents(c.start, c.end), objects = objectsIn(c.start, c.end);
    return `<p class="kicker">Jagd ${c.n} von ${episodes.length}</p>
      <h2>${esc(c.title)}</h2>
      <p class="meta">${esc(span(c.start, c.end))} · ${esc(ep.places.map((p) => p.label.replace(/\s*\(.*?\)/g, "")).join(" · "))}</p>
      ${gallery(photos)}
      <ul class="chips">${ep.animals.map((a) => `<li>${esc(a.label_de)}</li>`).join("")}
        <li class="n">${plural(ep.kill_sentences, "Satz", "Sätze")} vom Erlegen im Tagebuch</li></ul>
      ${quotes.slice(0, 3).map(quoteItem).join("")}
      ${quotes.length > 3 ? `<details class="more"><summary>${plural(quotes.length - 3, "weiteres Zitat", "weitere Zitate")} aus dem Tagebuch</summary>
        ${quotes.slice(3).map(quoteItem).join("")}</details>` : ""}
      ${press.length ? `<h3>Echo in der Presse · ${plural(press.length, "Ausgabe", "Ausgaben")}</h3><ul class="press">${
        quotable.slice(0, 2).map(pressItem).join("")}</ul>
      ${quotable.length > 2 ? `<details class="more"><summary>${plural(quotable.length - 2, "weiterer Zeitungsausschnitt", "weitere Zeitungsausschnitte")}</summary>
        <ul class="press">${quotable.slice(2).map(pressItem).join("")}</ul></details>` : ""}
      ${others.length ? `<details class="more"><summary>${plural(others.length, "weitere Ausgabe", "weitere Ausgaben")} ohne passenden Ausschnitt</summary>
        <p class="note">Gefunden über die Suche nach Erzherzog/Thronfolger und Ort oder Tier in der Ausgabe; der Ausschnitt nennt den Erzherzog nicht selbst.</p>
        <ul class="plain">${others.map((p) => `<li>${link(p.url, p.newspaper)}, ${esc(fmt(p.date))}</li>`).join("")}</ul></details>` : ""}` : ""}
      ${hunters.length ? `<h3>Mit auf der Jagd</h3><p>${hunters.map((p) => esc(p.name)).join(" · ")}</p>` : ""}
      ${heroes.length ? `<h3>Lebend an Bord</h3><ul class="plain">${heroes.join("")}</ul>` : ""}
      ${objects.length ? `<h3>Objekte aus diesen Tagen</h3><ul class="plain">${objects.join("")}</ul>` : ""}
      ${dayList(c.days)}`;
  }
  function voyageHTML(c) {
    const sea = c.days.filter((d) => !shortPlace(d.place)).length;
    const via = c.places.slice(1, -1);
    if (c.slim) {
      return `<p class="kicker">Unterwegs · ${esc(span(c.start, c.end))}</p><h2>${esc(c.title)}</h2>${dayList(c.days)}`;
    }
    const photos = photosIn(c);
    const heroes = heroEvents(c.start, c.end), objects = objectsIn(c.start, c.end);
    return `<p class="kicker">Unterwegs</p><h2>${esc(c.title)}</h2>
      <p class="meta">${esc(span(c.start, c.end))} · ${plural(c.days.length, "Tag", "Tage")}${sea ? `, davon ${sea} auf See` : ""}</p>
      ${via.length ? `<p>Über ${esc(via.slice(0, 6).join(", "))}${via.length > 6 ? " und weitere Orte" : ""}.</p>` : ""}
      ${gallery(photos)}
      ${heroes.length ? `<h3>Lebend an Bord</h3><ul class="plain">${heroes.join("")}</ul>` : ""}
      ${objects.length ? `<h3>Objekte aus diesen Tagen</h3><ul class="plain">${objects.join("")}</ul>` : ""}
      ${dayList(c.days)}`;
  }
  function afterHTML(c) {
    const fates = E.heroes.filter((h) => h.status).map((h) =>
      `<li><b>${esc(h.name)}</b> (${esc(h.species_de)}): ${esc(STATUS[h.status] || h.status)}</li>`);
    return `<p class="kicker">Epilog · ${esc(span(c.start, c.end))}</p><h2>${esc(c.title)}</h2>
      <p>${esc(E.ship.note)} Diese ${c.days.length} Tage gehören nicht mehr zur Fahrt der Kaiserin Elisabeth; die
        Karte zeigt sie nur als gestrichelte Linie.</p>
      <h3>Was aus den Tieren wurde</h3><ul class="plain">${fates.join("")}</ul>
      ${dayList(c.days)}`;
  }
  document.getElementById("chapters").innerHTML = chapters.map((c) =>
    `<section class="chapter ${c.kind}${c.slim ? " slim" : ""}" id="${esc(c.id)}" data-i="${chapters.indexOf(c)}">${
      c.kind === "hunt" ? huntHTML(c) : c.kind === "voyage" ? voyageHTML(c) : afterHTML(c)}</section>`).join("");

  document.getElementById("chapters").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-photo]");
    if (!b) return;
    const fig = b.closest("figure"), p = E.photos[+b.dataset.photo], all = [...fig.querySelectorAll("button[data-photo]")];
    fig.querySelector("img.main").src = p.preview;
    fig.querySelector("img.main").alt = p.title;
    const total = fig.querySelector(".count") ? fig.querySelector(".count").textContent.split(" von ")[1] : all.length;
    fig.querySelector("figcaption").innerHTML = `<span class="count">Foto ${all.indexOf(b) + 1} von ${total}</span> · ${caption(p)}`;
    all.forEach((x) => x.toggleAttribute("aria-current", x === b));
  });

  // --- map -------------------------------------------------------------------------------
  // Same 1872 base map as reise.html; points move like the nearest place calibrated on it (ke_places_1872.js).
  const map = L.map("map", { zoomControl: true, scrollWheelZoom: false, worldCopyJump: false, attributionControl: true })
    .setView([15, 90], 3);
  L.tileLayer("https://mapwarper.net/maps/tile/98512/{z}/{x}/{y}.png", {
    maxNativeZoom: 6, attribution: 'Karte 1872: <a href="https://mapwarper.net/maps/98512" target="_blank" rel="noopener">Map Warper 98512</a>',
  }).addTo(map);
  const H1872 = window.KE1872 || {};
  const TODAY = { ...E.geonames };
  for (const [name, h] of Object.entries(H1872)) if (h.heute) TODAY[name] = h.heute;
  const REF = Object.entries(TODAY).filter(([n]) => H1872[n]);
  const pos = (lat, lon) => {
    const raw = ((lon + 180) % 360 + 360) % 360 - 180;
    let best = null, bestD = 16;
    for (const [name, [rlat, rlon]] of REF) {
      const dd = (rlat - lat) ** 2 + (rlon - raw) ** 2;
      if (dd < bestD) { best = name; bestD = dd; }
    }
    if (!best) return [lat, lon];
    const [rlat, rlon] = TODAY[best];
    return [lat + H1872[best].lat - rlat, lon + H1872[best].lon - rlon];
  };
  const SHIP = "#1f4e79", HUNT = "#b4471b", AFTER = "#5f5a50";
  const ll = (d) => pos(d.lat, d.lon);
  const shipLine = shipDays.filter((d) => d.lat !== null);
  // after Yokohama the route runs east around the world: unwrap longitudes so each step is < 180°
  let lastLon = null;
  const afterLine = [shipLine[shipLine.length - 1], ...afterDays.filter((d) => d.lat !== null)].map((d) => {
    let lon = d.lon;
    if (lastLon !== null) while (lon - lastLon < -180) lon += 360;
    lastLon = lon;
    return pos(d.lat, lon);
  });
  L.polyline(afterLine, { color: AFTER, weight: 3, dashArray: "5 7", opacity: 0.95, interactive: false }).addTo(map);
  L.polyline(shipLine.map(ll), { color: SHIP, weight: 2, opacity: 0.3, interactive: false }).addTo(map);
  const travelled = L.polyline([], { color: SHIP, weight: 3, opacity: 0.85, interactive: false }).addTo(map);
  const current = L.polyline([], { color: HUNT, weight: 4, opacity: 0.95, interactive: false }).addTo(map);
  const hunts = L.layerGroup().addTo(map), here = L.layerGroup().addTo(map);
  for (const c of chapters.filter((c) => c.kind === "hunt")) {
    const d = c.days.find((x) => x.lat !== null);
    if (d) L.circleMarker(ll(d), { radius: 5, color: "#fff", weight: 1, fillColor: HUNT, fillOpacity: 0.55 })
      .bindTooltip(`${c.title} · ${span(c.start, c.end)}`).on("click", () => go(c)).addTo(hunts);
  }
  L.marker(ll(shipLine[shipLine.length - 1]), { interactive: false, icon: L.divIcon({ className: "", iconSize: null,
    html: `<span style="font:12px system-ui;background:#fbf8f1;border:1px solid #d9cfbc;padding:1px 6px;border-radius:3px;white-space:nowrap;position:relative;left:8px;top:-8px">Yokohama: Franz Ferdinand verlässt die Kaiserin Elisabeth</span>` }) }).addTo(map);

  function showOnMap(c) {
    const pts = c.days.filter((d) => d.lat !== null);
    here.clearLayers();
    if (c.kind === "after") {
      travelled.setLatLngs(shipLine.map(ll));
      current.setLatLngs([]);
      map.flyToBounds(L.latLngBounds(afterLine), { padding: [24, 24], duration: 0.8 });
      return;
    }
    travelled.setLatLngs(shipLine.filter((d) => d.date <= c.end).map(ll));
    const prev = shipLine.filter((d) => d.date < c.start).pop();
    current.setLatLngs((prev ? [prev, ...pts] : pts).map(ll));
    const seen = new Set();
    for (const d of pts) {
      const k = `${d.lat},${d.lon}`;
      if (seen.has(k)) continue;
      seen.add(k);
      L.circleMarker(ll(d), { radius: 7, color: "#fff", weight: 2, fillColor: c.kind === "hunt" ? HUNT : SHIP, fillOpacity: 1 })
        .bindTooltip(shortPlace(d.place) || d.place).addTo(here);
    }
    const focus = pts.length ? pts : [prev || shipLine[0]];
    const b = L.latLngBounds(focus.map(ll));
    if (prev && pts.length) b.extend(ll(prev));
    map.flyToBounds(b.pad(0.4), { maxZoom: c.kind === "hunt" ? 6 : 5, duration: 0.8 });
  }

  // --- timeline: one row; ship days take 90 % of the width, the days after Yokohama the rest -------
  // Drawn at the real pixel width (no stretched viewBox, so the labels keep their shape); redrawn on resize.
  const svg = document.getElementById("tl"), Y = 14, H = 16;
  let active = null;
  let W = 1000, SHIP_W = 900;
  const xOf = (iso) => {
    const i = shipDays.findIndex((d) => d.date === iso);
    if (i >= 0) return (i / shipDays.length) * SHIP_W;
    const j = afterDays.findIndex((d) => d.date === iso);
    return SHIP_W + 10 + (j / afterDays.length) * (W - SHIP_W - 10);
  };
  const xEnd = (iso) => {
    const i = shipDays.findIndex((d) => d.date === iso);
    return i >= 0 ? ((i + 1) / shipDays.length) * SHIP_W : W;
  };
  function drawTimeline() {
    W = Math.max(300, svg.getBoundingClientRect().width);
    SHIP_W = Math.round(W * 0.9) - 10;
    svg.setAttribute("viewBox", `0 0 ${W} 54`);
    let parts = "";
    // land and sea as two shades; one rect per run of equal days
    let run = null;
    const flush = () => run && (parts += `<rect x="${run.x}" y="${Y}" width="${run.w}" height="${H}" fill="${run.sea ? "#b9cdd6" : "#cdbf9f"}"/>`);
    shipDays.forEach((d, i) => {
      const sea = d.lat === null, x = (i / shipDays.length) * SHIP_W, w = SHIP_W / shipDays.length;
      if (run && run.sea === sea) run.w += w; else { flush(); run = { sea, x, w }; }
    });
    flush();
    parts += `<rect x="${SHIP_W + 10}" y="${Y + 4}" width="${W - SHIP_W - 10}" height="${H - 8}" fill="#d6d1c6"/>`;
    for (const c of chapters) {
      const x = xOf(c.start), w = Math.max(3, xEnd(c.end) - x);
      parts += c.kind === "hunt"
        ? `<rect class="hunt" data-id="${c.id}" x="${x}" y="${Y - 6}" width="${w}" height="${H + 12}"><title>Jagd ${c.n}: ${esc(c.title)}, ${esc(span(c.start, c.end))}</title></rect>`
        : `<rect class="seg" data-id="${c.id}" x="${x}" y="${Y - 6}" width="${w}" height="${H + 12}"><title>${esc(c.title)}, ${esc(span(c.start, c.end))}</title></rect>`;
    }
    // month labels, thinned out when narrow
    let lastM = "", lastX = -99;
    shipDays.forEach((d, i) => {
      const m = d.date.slice(0, 7);
      if (m === lastM) return;
      lastM = m;
      const x = (i / shipDays.length) * SHIP_W;
      parts += `<line x1="${x}" x2="${x}" y1="${Y + H + 2}" y2="${Y + H + 7}" stroke="#a39d90"/>`;
      if (x - lastX > 28 && x < SHIP_W - (W < 500 ? 40 : 22)) {
        parts += `<text x="${x + 2}" y="${Y + H + 19}">${MONTHS[+m.slice(5) - 1].slice(0, 3)}</text>`;
        lastX = x;
      }
    });
    parts += `<text x="${W}" y="${Y + H + 19}" text-anchor="end">Heimreise</text>`;
    parts += `<rect class="cur" id="tl-cur" x="0" y="${Y - 8}" width="0" height="${H + 16}" rx="2"/>`;
    svg.innerHTML = parts;
    if (active) markTimeline(active);
  }
  function markTimeline(c) {
    const cur = document.getElementById("tl-cur"), x = xOf(c.start);
    cur.setAttribute("x", x - 2);
    cur.setAttribute("width", Math.max(5, xEnd(c.end) - x + 4));
    svg.querySelectorAll(".hunt").forEach((r) => r.classList.toggle("on", r.dataset.id === c.id));
  }
  let resizeTimer = null;
  addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(drawTimeline, 150); });
  addEventListener("load", drawTimeline);   // width is final only after fonts and layout
  svg.addEventListener("click", (ev) => {
    const id = ev.target.dataset && ev.target.dataset.id;
    if (id) return go(chapters.find((c) => c.id === id));
    // click on the bar between chapters: nearest day
    const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width * W;
    const i = Math.min(shipDays.length - 1, Math.floor(x / SHIP_W * shipDays.length));
    go(x > SHIP_W ? chapters[chapters.length - 1] : chapterOf(shipDays[i].date));
  });

  // --- current chapter -------------------------------------------------------------------------
  function setActive(c) {
    if (!c || c === active) return;
    active = c;
    markTimeline(c);
    document.getElementById("tl-label").textContent =
      `${c.kind === "hunt" ? `Jagd ${c.n} · ` : ""}${c.title} · ${span(c.start, c.end)}`;
    showOnMap(c);
  }
  // only an explicit jump writes the URL (Chrome scrolls on a fragment change)
  function go(c) {
    if (!c) return;
    if (history.replaceState) history.replaceState(null, "", `#${c.id}`);
    document.getElementById(c.id).scrollIntoView({ behavior: "smooth", block: "start" });
    setActive(c);
  }
  drawTimeline();
  const io = new IntersectionObserver((entries) => {
    const vis = entries.filter((e) => e.isIntersecting);
    if (vis.length) setActive(chapters[+vis[0].target.dataset.i]);
  }, { rootMargin: "-35% 0px -60% 0px" });
  document.querySelectorAll(".chapter").forEach((s) => io.observe(s));

  const start = chapters.find((c) => c.id === decodeURIComponent(location.hash.slice(1))) ||
    chapterOf(decodeURIComponent(location.hash.slice(1)));
  if (start) {
    const el = document.getElementById(start.id);
    el.scrollIntoView();
    setActive(start);
    if (document.fonts) document.fonts.ready.then(() => el.scrollIntoView());   // the web font changes line breaks
  } else {
    setActive(chapters[0]);
  }
})();
