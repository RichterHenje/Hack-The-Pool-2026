// All Weltmuseum photos of the voyage (team bilder.json, 408) as one private layer KE1893_photos_all.
// ONE placement rule: the point is the place the museum/team names for the photo, not Franz
// Ferdinand's position. Tiers: A = 'Ortschaft (Route)' (team) -> team gazetteer (route_places/
// hunt places = Wikidata, bundle GeoNames, our stops); A2 = 'Geografie' -> same gazetteer;
// B = 'Geografie' -> Wikidata (photo_places_wikidata.json, country-checked); T = 'Terai' -> team's
// Nepal hunt place (approximate); regions are never placed (tier C, counted only).
// Day dates from the team's ke_photos_dated.csv (by vf_id). Reference (Python): placed 357
// (A 236, A2 6, B 96, T 19), unplaced 51, dated among placed 128.
// Web map: two operational layers on this service (with / without day date; the undated one has
// timeAnimation false), the old KE1893_photos layer is removed from the map (item kept).
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const RAW = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const WD = {"Varanasi": {"qid": "Q79980", "label": "Varanasi", "lat": 25.31889, "lon": 83.01278}, "Yellowstone National Park": {"qid": "Q351", "label": "Yellowstone National Park", "lat": 44.6, "lon": -110.5}, "Enoshima": {"qid": "Q989803", "label": "Enoshima", "lat": 35.29933, "lon": 139.48091}, "Mande": {"qid": "Q566062", "label": "Mande (Cianjur, West Java)", "lat": -6.75522, "lon": 107.22853}, "Kamakura": {"qid": "Q10939227", "label": "Kamakura (historic centre)", "lat": 35.31881, "lon": 139.55192}, "Salt Lake City": {"qid": "Q23337", "label": "Salt Lake City", "lat": 40.75, "lon": -111.88333}, "Yumoto": {"qid": "Q11563576", "label": "Yumoto (Hakone)", "lat": 35.23242, "lon": 139.10681}, "Hakone": {"qid": "Q671040", "label": "Hakone", "lat": 35.23236, "lon": 139.10694}, "Kurume": {"qid": "Q320934", "label": "Kurume", "lat": 33.31925, "lon": 130.50833}, "Fuji-San": {"qid": "Q39231", "label": "Mount Fuji", "lat": 35.36056, "lon": 138.7275}, "Blackheath": {"qid": "Q526224", "label": "Blackheath (New South Wales)", "lat": -33.63389, "lon": 150.28472}, "Wollondilly River": {"qid": "Q1164736", "label": "Wollondilly River", "lat": -33.95, "lon": 150.433}, "Ashi Lake": {"qid": "Q187053", "label": "Lake Ashi", "lat": 35.21167, "lon": 139.00389}, "Tonosawa": {"qid": "Q11428353", "label": "Tōnosawa (Hakone)", "lat": 35.23444, "lon": 139.09397}, "Kokura": {"qid": "Q516373", "label": "Kokura", "lat": 33.88342, "lon": 130.87519}, "Moji": {"qid": "Q1045113", "label": "Moji-ku", "lat": 33.94111, "lon": 130.95972}, "Fatehpur Sikri": {"qid": "Q179046", "label": "Fatehpur Sikri", "lat": 27.09111, "lon": 77.66111}, "Sarnath": {"qid": "Q324394", "label": "Sarnath", "lat": 25.38111, "lon": 83.02139}, "Laloki River": {"qid": "Q141440132", "label": "Laloki River", "lat": -9.1284, "lon": 146.96777}, "Katase": {"qid": "Q11569905", "label": "Katase (Fujisawa)", "lat": 35.31486, "lon": 139.48374}, "Ojigoku": {"qid": "Q1134429", "label": "Ōwakudani", "lat": 35.24192, "lon": 139.02067}, "Kitakyushu": {"qid": "Q188806", "label": "Kitakyūshū", "lat": 33.88342, "lon": 130.87519}, "Osaka": {"qid": "Q35765", "label": "Osaka", "lat": 34.69375, "lon": 135.50211}, "Shizuoka": {"qid": "Q174691", "label": "Shizuoka", "lat": 34.97556, "lon": 138.3825}, "Nara": {"qid": "Q169134", "label": "Nara", "lat": 34.685, "lon": 135.80478}};
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const text = async p => (await fetch(RAW + p)).text();
const json = async p => JSON.parse((await text(p)).replace(/^﻿/, ''));
const clean = s => String(s ?? '').replace(/\s+/g, ' ').replace(/</g, '‹').replace(/>/g, '›').trim();
const first = v => (Array.isArray(v) ? v[0] : v) || '';
const norm = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z]/g, '');
function parseCSV(t) { // RFC 4180, quotes and embedded newlines
  const rows = []; let row = [], f = '', q = false;
  t = t.replace(/^﻿/, '');
  for (let i = 0; i < t.length; i++) { const c = t[i];
    if (q) { if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true; else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n') { row.push(f.replace(/\r$/, '')); rows.push(row); row = []; f = ''; } else f += c; }
  if (f || row.length) { row.push(f); rows.push(row); }
  const h = rows.shift(); return rows.filter(r => r.length > 1).map(r => Object.fromEntries(h.map((k, i) => [k, r[i]])));
}

// gazetteer, same order as the Python reference (first entry wins)
const G = {};
const put = (n, lat, lon, src) => { const k = norm(n); if (k && lat != null && !(k in G)) G[k] = { lat, lon, src, name: n }; };
const rp = await json('enrichment/data/route_places.json');
for (const p of (rp.places || rp)) for (const n of [(p.label || '').split(',')[0], p.wikidata_label, (p.vault_note || '').split(',')[0]]) put(n, p.lat, p.lon, 'Wikidata (Ortsliste des Teams)');
const hp = await json('enrichment/places.json');
for (const p of hp) for (const n of [p.label.split('(')[0], ...(p.diary || []), ...(p.vault || [])]) put(n.split(',')[0], p.lat, p.lon, 'Wikidata (Jagdorte des Teams)');
const et = await text('kaiserin_elisabeth/prototype/data/ke_enrichment.js');
const KEE = JSON.parse(et.slice(et.indexOf('{'), et.lastIndexOf('}') + 1));
for (const [n, [lat, lon]] of Object.entries(KEE.geonames)) put(n, lat, lon, 'GeoNames');
for (const f of (await get(SVC + 'KE1893_stops/FeatureServer/0/query', { where: '1=1', outFields: 'name_then,name_now', outSR: 4326 })).features)
  for (const n of [f.attributes.name_then, f.attributes.name_now]) put(n, f.geometry.y, f.geometry.x, 'Stationen');
const lookup = s => { if (!s || s === 'NA') return null; for (const part of s.split(/[,(;|]/)) { const k = norm(part); if (k in G) return G[k]; } return null; };
const nepal = hp.find(p => p.id.includes('nepal'));
const dated = Object.fromEntries(parseCSV(await text('kaiserin_elisabeth/prototype/arcgis/ke_photos_dated.csv')).map(r => [r.vf_id, r]));
const LIC = { 'http://creativecommons.org/licenses/by-nc-sa/4.0/': 'CC BY-NC-SA 4.0', 'http://rightsstatements.org/vocab/InC/1.0/': 'In Copyright (InC)' };
const CRE = { 'Deen Dayal': 'Lala Deen Dayal', 'Imhoff': 'Max von Imhof' };
const lic = Object.fromEntries(KEE.photos.map(p => { const c = p.creator.split(',')[0].replace(' (photographer)', '').trim(); return [p.vf, { licence: LIC[p.rights] || p.rights, europeana: p.europeana, creator: CRE[c] || c }]; }));
const TIER = { A: "Ortschaft (Route) laut Teamliste", A2: "Geografie laut Museum", B: "Geografie laut Museum", T: "Geografie laut Museum: Terai" };
const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };

const B = await json('normalization/json/bilder.json');
const count = { A: 0, A2: 0, B: 0, T: 0, C: 0, dated: 0 }, regions = {};
const features = [];
for (const b of B) {
  const vf = first(b['Inventarnummer']), o = first(b['Ortschaft (Route)']), g = first(b['Geografie']);
  let hit = lookup(o), tier = 'A';
  if (!hit) {
    if (WD[g]) { hit = { lat: WD[g].lat, lon: WD[g].lon, src: 'Wikidata ' + WD[g].qid, name: WD[g].label }; tier = 'B'; }
    else if (g === 'Terai') { hit = { lat: nepal.lat, lon: nepal.lon, src: 'Jagdort des Teams, ungefähr', name: nepal.label }; tier = 'T'; }
    else { hit = lookup(g); tier = hit ? 'A2' : 'C'; }
  }
  count[tier]++;
  if (tier === 'C') { regions[g || '–'] = (regions[g || '–'] || 0) + 1; continue; }
  const d = dated[vf]?.date || '';
  if (d) count.dated++;
  features.push({ geometry: { x: hit.lon, y: hit.lat, spatialReference: { wkid: 4326 } }, attributes: {
    vf_id: vf, title: clean(first(b['Titel'])).slice(0, 500), museum_date: clean(first(b['Datierung'])), photo_date: d ? toMs(d) : null,
    date_range: dated[vf]?.date_range || null, place_name: clean(hit.name), place_tier: tier, place_rule: TIER[tier], place_src: hit.src,
    museum_geography: clean(g), route_place: o === 'NA' ? null : clean(o), image_url: first(b['Bild-Link']) || null,
    museum_url: first(b['Weltmuseum-Link']) || null, licence: lic[vf]?.licence || null, creator: lic[vf]?.creator || null, europeana: lic[vf]?.europeana || null } });
}
const S = (name, length) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true });
const fields = [S('vf_id', 32), S('title', 1024), S('museum_date', 64), { name: 'photo_date', type: 'esriFieldTypeDate', alias: 'photo_date', nullable: true, editable: true },
  S('date_range', 8), S('place_name', 128), S('place_tier', 4), S('place_rule', 128), S('place_src', 128), S('museum_geography', 128), S('route_place', 128),
  S('image_url', 256), S('museum_url', 256), S('licence', 64), S('creator', 128), S('europeana', 128)];

let url = SVC + 'KE1893_photos_all/FeatureServer/0', itemId;
const found = (await get(REST + '/search', { q: `owner:${USER} AND title:"KE 1892-93 Fotos (alle)"`, num: 2 })).results[0];
if (found) itemId = found.id; else {
  const extent = { xmin: -180, ymin: -60, xmax: 180, ymax: 70, spatialReference: { wkid: 4326 } };
  const svc = await post(`${REST}/content/users/${USER}/createService`, { outputType: 'featureService', createParameters: {
    name: 'KE1893_photos_all', serviceDescription: '', hasStaticData: false, maxRecordCount: 2000, supportedQueryFormats: 'JSON',
    capabilities: 'Create,Delete,Query,Update,Editing', spatialReference: { wkid: 4326 }, initialExtent: extent, allowGeometryUpdates: true,
    units: 'esriDecimalDegrees', xssPreventionInfo: { xssPreventionEnabled: true, xssPreventionRule: 'InputOnly', xssInputRule: 'rejectInvalid' } } });
  itemId = svc.itemId; url = svc.serviceurl + '/0';
  const admin = svc.serviceurl.replace('/rest/services/', '/rest/admin/services/');
  await post(admin + '/addToDefinition', { addToDefinition: { layers: [{ id: 0, name: 'KE 1892-93 Fotos (alle)', type: 'Feature Layer', geometryType: 'esriGeometryPoint',
    objectIdField: 'OBJECTID', displayField: 'vf_id', fields: [{ name: 'OBJECTID', type: 'esriFieldTypeOID', alias: 'OBJECTID', nullable: false, editable: false }, ...fields],
    extent, hasAttachments: false, htmlPopupType: 'esriServerHTMLPopupTypeNone', capabilities: 'Create,Delete,Query,Update,Editing', supportsRollbackOnFailureParameter: true,
    drawingInfo: { renderer: { type: 'simple', symbol: { type: 'esriSMS', style: 'esriSMSSquare', color: [30, 70, 120, 220], size: 6, outline: { color: [255, 255, 255, 255], width: 0.75 } } } },
    timeInfo: { startTimeField: 'photo_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays' } }] } });
  const add = await post(url + '/addFeatures', { rollbackOnFailure: false, features });
  const bad = add.addResults.filter(r => !r.success);
  if (bad.length) throw new Error(bad.length + ' failed: ' + JSON.stringify(bad[0].error));
  const t = features.map(f => f.attributes.photo_date).filter(v => v != null);
  await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: { startTimeField: 'photo_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays', timeExtent: [Math.min(...t), Math.max(...t)] } } });
  await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } });
  await post(`${REST}/content/users/${USER}/items/${itemId}/update`, { title: 'KE 1892-93 Fotos (alle)', tags: 'Hack the Pool 2026,Kaiserin Elisabeth,1892-93', snippet: `Team data at ${SHA.slice(0, 7)}; private demo` });
}

// web map: replace the old photo layer by two layers on the new service
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const old = d.operationalLayers.find(l => l.id === 'KE1893_photos');
if (old && !d.operationalLayers.some(l => l.id === 'KE1893_photos_dated')) {
  const fi = fields.map(f => ({ fieldName: f.name, label: f.name, visible: false, isEditable: false }));
  const popup = { title: 'Foto {vf_id}', fieldInfos: fi,
    expressionInfos: [
      { name: 'credit', returnType: 'string', expression: "IIf(IsEmpty($feature.licence), 'Weltmuseum Wien; Lizenz nicht geprüft', IIf(IsEmpty($feature.creator), '', $feature.creator + ', ') + 'Weltmuseum Wien, ' + $feature.licence + ' (über Europeana; Aggregator: Kulturpool)')" },
      { name: 'eu', returnType: 'string', expression: "IIf(IsEmpty($feature.europeana), '', ' · Europeana: ' + $feature.europeana)" },
      { name: 'range', returnType: 'string', expression: "IIf($feature.date_range == 'ja', ' (Zeitraum; auf der Zeitleiste der erste Tag)', '')" }],
    popupElements: [
      { type: 'media', mediaInfos: [{ type: 'image', title: '', caption: 'Foto: {expression/credit}', altText: '{title}', value: { sourceURL: '{image_url}', linkURL: '{museum_url}' } }] },
      { type: 'text', text: 'Titel (historische Bildunterschrift des Weltmuseums, zitiert): „{title}“<br>' +
        'Datierung laut Museum: {museum_date}{expression/range} · Geografie laut Museum: {museum_geography}<br>' +
        '<span style="font-size:smaller">Punkt = Ort laut {place_rule}: {place_name} (Koordinate: {place_src}), nicht der Standort Franz Ferdinands.</span><br>' +
        '<a href="{museum_url}" target="_blank">Objektseite im Weltmuseum Wien</a>{expression/eu}' }] };
  const base = { url, itemId, layerType: 'ArcGISFeatureLayer', opacity: 1, popupInfo: popup };
  const dated = { ...base, id: 'KE1893_photos_dated', title: 'Fotos Weltmuseum, mit Tagesdatum', visibility: true,
    layerDefinition: { definitionExpression: 'photo_date IS NOT NULL', drawingInfo: old.layerDefinition.drawingInfo,
      featureReduction: old.layerDefinition.featureReduction } };
  const undated = { ...base, id: 'KE1893_photos_undated', title: 'Fotos Weltmuseum, ohne Tagesdatum (immer sichtbar)', visibility: false, timeAnimation: false,
    layerDefinition: { definitionExpression: 'photo_date IS NULL', drawingInfo: { renderer: { type: 'simple', label: 'Foto ohne Tagesdatum',
      symbol: { type: 'esriSMS', style: 'esriSMSSquare', color: [30, 70, 120, 110], size: 5, outline: { color: [255, 255, 255, 160], width: 0.5 } } } },
      featureReduction: { ...old.layerDefinition.featureReduction, popupInfo: { ...old.layerDefinition.featureReduction.popupInfo, title: '{cluster_count} Fotos ohne Tagesdatum an diesem Ort' } } } };
  const i = d.operationalLayers.indexOf(old);
  d.operationalLayers.splice(i, 1, undated, dated);
  await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
}
const n = (await get(url + '/query', { where: '1=1', returnCountOnly: true })).count;
const nd = (await get(url + '/query', { where: 'photo_date IS NOT NULL', returnCountOnly: true })).count;
JSON.stringify({ itemId, count, regions, layerCount: n, datedInLayer: nd, order: (await get(`${REST}/content/items/${WEBMAP}/data`)).operationalLayers.map(l => l.title) });
