// Kill entries (the "shot list" per day) as private layer KE1893_kills, from the team's
// enrichment/data/hunt_entries.json (65 diary days with kill sentences, khm-team b5e1464).
// Coordinates: place_id -> enrichment/places.json (Wikidata; some approximate, coord_note).
// Wording rule (team README): counts are MENTIONS in kill sentences of uncorrected OCR (keyword rules),
// not animals killed. first_person = sentences in the first person (FF himself, not companions).
// Added to the web map directly above the hunt episodes; time field = entry date.
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const RAW = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const json = async p => JSON.parse((await (await fetch(RAW + p)).text()).replace(/^﻿/, ''));
const clean = s => String(s ?? '').replace(/\s+/g, ' ').replace(/</g, '‹').replace(/>/g, '›').trim();
const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };
const HE = await json('enrichment/data/hunt_entries.json');
const PL = Object.fromEntries((await json('enrichment/places.json')).map(p => [p.id, p]));
const et = await (await fetch(RAW + 'kaiserin_elisabeth/prototype/data/ke_enrichment.js')).text();
const KEE = JSON.parse(et.slice(et.indexOf('{'), et.lastIndexOf('}') + 1));
const label = id => { const a = KEE.animals[id]; return typeof a === 'string' ? a : (a && (a.label_de || a.de || a.name)) || id; };
const EP = KEE.episodes;
// 4 entries have no place_id (Benares 11.2., Singapore 6.4., Sydney 16.5., Numea 2.6.; one sentence each,
// not part of any hunt episode; Sydney "tiger, elephant, buffalo" is surely no hunt): placed at the
// diary day's coordinates and marked no_hunt_place = 1.
const DAY = Object.fromEntries(KEE.days.filter(d => d.lat != null).map(d => [d.date, d]));
// places.json uses lat 0 / lon 0 as a placeholder for places without coordinates (gwalior, owaraha
// at b5e1464): treat 0/0 as missing and take the diary day's point, keeping the hunting place's name.
const hasXY = p => p && Number.isFinite(p.lat) && Number.isFinite(p.lon) && !(p.lat === 0 && p.lon === 0);
const placeOf = h => hasXY(PL[h.place_id]) ? { ...PL[h.place_id], fallback: false }
  : DAY[h.date] ? (PL[h.place_id]
    ? { label: PL[h.place_id].label, lat: DAY[h.date].lat, lon: DAY[h.date].lon, coord_note: 'Koordinate des Tagebuchtags (Datensatz des Teams); der Jagdort hat keine eigene Koordinate', fallback: false }
    : { label: DAY[h.date].place, lat: DAY[h.date].lat, lon: DAY[h.date].lon, coord_note: 'Ort des Tagebuchtags; kein Jagdort des Teams, vermutlich keine Jagd', fallback: true }) : null;
const missing = HE.filter(h => !placeOf(h)).map(h => h.date);
if (missing.length) throw new Error('no coordinates for: ' + missing.join(', '));
const features = HE.map(h => {
  const p = placeOf(h), q = (h.quotes || []).find(x => x.first_person) || (h.quotes || [])[0] || {};
  const ep = EP.find(e => e.start <= h.date && h.date <= e.end && e.places.some(x => Math.abs(x.lat - p.lat) < 1.5 && Math.abs(x.lon - p.lon) < 1.5));
  return { geometry: { x: p.lon, y: p.lat, spatialReference: { wkid: 4326 } }, attributes: {
    entry_date: toMs(h.date), place: p.label, place_raw: clean(h.place_raw), coord_note: p.coord_note || null,
    animals: Object.entries(h.animals || {}).map(([k, v]) => `${label(k)} ${v}`).join(' · '),
    kill_sentences: h.kill_sentences, first_person: h.first_person || 0, ff_self: (h.first_person || 0) > 0 ? 1 : 0,
    quote: clean(q.text).slice(0, 900), quote_first_person: q.first_person ? 1 : 0,
    page_url: h.page_url || null, band: h.band, scan: h.scan, day_method: h.day_method || null, episode: ep ? ep.label : null,
    no_hunt_place: p.fallback ? 1 : 0 } };
});
const S = (name, length) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true });
const I = name => ({ name, type: 'esriFieldTypeInteger', alias: name, nullable: true, editable: true });
const fields = [{ name: 'entry_date', type: 'esriFieldTypeDate', alias: 'entry_date', nullable: true, editable: true }, S('place', 128), S('place_raw', 128), S('coord_note', 256),
  S('animals', 512), I('kill_sentences'), I('first_person'), I('ff_self'), S('quote', 2048), I('quote_first_person'), S('page_url', 256), I('band'), I('scan'), S('day_method', 32), S('episode', 128), I('no_hunt_place')];
let url = SVC + 'KE1893_kills/FeatureServer/0', itemId;
const found = (await get(REST + '/search', { q: `owner:${USER} AND title:"KE 1892-93 Abschuss-Einträge"`, num: 2 })).results[0];
if (found) itemId = found.id; else {
  const xs = features.map(f => f.geometry.x), ys = features.map(f => f.geometry.y);
  const extent = { xmin: Math.min(...xs), ymin: Math.min(...ys), xmax: Math.max(...xs), ymax: Math.max(...ys), spatialReference: { wkid: 4326 } };
  const svc = await post(`${REST}/content/users/${USER}/createService`, { outputType: 'featureService', createParameters: {
    name: 'KE1893_kills', serviceDescription: '', hasStaticData: false, maxRecordCount: 2000, supportedQueryFormats: 'JSON',
    capabilities: 'Create,Delete,Query,Update,Editing', spatialReference: { wkid: 4326 }, initialExtent: extent, allowGeometryUpdates: true,
    units: 'esriDecimalDegrees', xssPreventionInfo: { xssPreventionEnabled: true, xssPreventionRule: 'InputOnly', xssInputRule: 'rejectInvalid' } } });
  itemId = svc.itemId; url = svc.serviceurl + '/0';
  const admin = svc.serviceurl.replace('/rest/services/', '/rest/admin/services/');
  await post(admin + '/addToDefinition', { addToDefinition: { layers: [{ id: 0, name: 'KE 1892-93 Abschuss-Einträge', type: 'Feature Layer', geometryType: 'esriGeometryPoint',
    objectIdField: 'OBJECTID', displayField: 'place', fields: [{ name: 'OBJECTID', type: 'esriFieldTypeOID', alias: 'OBJECTID', nullable: false, editable: false }, ...fields],
    extent, hasAttachments: false, htmlPopupType: 'esriServerHTMLPopupTypeNone', capabilities: 'Create,Delete,Query,Update,Editing', supportsRollbackOnFailureParameter: true,
    drawingInfo: { renderer: { type: 'simple', symbol: { type: 'esriSMS', style: 'esriSMSX', color: [170, 30, 30, 255], size: 8, outline: { color: [170, 30, 30, 255], width: 2 } } } },
    timeInfo: { startTimeField: 'entry_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays' } }] } });
  const add = await post(url + '/addFeatures', { rollbackOnFailure: false, features });
  const bad = add.addResults.filter(r => !r.success);
  if (bad.length) throw new Error(bad.length + ' failed: ' + JSON.stringify(bad[0].error));
  const t = features.map(f => f.attributes.entry_date);
  await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: { startTimeField: 'entry_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays', timeExtent: [Math.min(...t), Math.max(...t)] } } });
  await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } });
  await post(`${REST}/content/users/${USER}/items/${itemId}/update`, { title: 'KE 1892-93 Abschuss-Einträge (Tagebuch)', tags: 'Hack the Pool 2026,Kaiserin Elisabeth,1892-93', snippet: `Team data at ${SHA.slice(0, 7)}; private demo` });
}
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
if (!d.operationalLayers.some(l => l.id === 'KE1893_kills')) {
  const ks = features.map(f => f.attributes.kill_sentences);
  const sym = (c, s) => ({ type: 'esriSMS', style: 'esriSMSX', color: c, size: s, outline: { color: c, width: 2 } });
  d.operationalLayers.splice(d.operationalLayers.findIndex(l => l.id === 'KE1893_hunts') + 1, 0, {
    id: 'KE1893_kills', title: 'Abschuss-Einträge im Tagebuch (pro Tag)', url, itemId, layerType: 'ArcGISFeatureLayer', visibility: true, opacity: 1,
    layerDefinition: { drawingInfo: { renderer: { type: 'uniqueValue',
      valueExpression: "IIf($feature.no_hunt_place == 1, 'x', Text($feature.ff_self))", defaultSymbol: sym([120, 120, 120, 220], 8),
      uniqueValueInfos: [
        { value: '1', label: 'mit Sätzen in der Ich-Form (Franz Ferdinand selbst)', symbol: sym([170, 30, 30, 255], 9) },
        { value: '0', label: 'nur Sätze über andere (Begleiter, Jäger)', symbol: sym([110, 110, 110, 220], 8) },
        { value: 'x', label: 'kein Jagdort des Teams (vermutlich keine Jagd)', symbol: sym([180, 180, 180, 160], 7) }],
      visualVariables: [{ type: 'sizeInfo', field: 'kill_sentences', minDataValue: Math.min(...ks), maxDataValue: Math.max(...ks), minSize: 7, maxSize: 18,
        legendOptions: { title: 'Abschuss-Sätze an diesem Tag' } }] } } },
    popupInfo: { title: 'Abschuss-Sätze im Tagebuch, {expression/d}',
      fieldInfos: fields.map(f => ({ fieldName: f.name, label: f.name, visible: false, isEditable: false })),
      expressionInfos: [{ name: 'd', returnType: 'string', expression: "Text($feature.entry_date, 'D.M.Y')" },
        { name: 'note', returnType: 'string', expression: "IIf(IsEmpty($feature.coord_note), '', IIf($feature.no_hunt_place == 1, ' ', ' Ort ungefähr: ') + $feature.coord_note + '.')" }],
      popupElements: [{ type: 'text', text:
        '{place} ({place_raw}){expression/note}<br><b>Tiere:</b> {animals}<br>' +
        '{kill_sentences} Sätze mit Tötungsverb und Tiername, davon {first_person} in der Ich-Form. Erwähnungen, nicht Zahl der getöteten Tiere.<br>' +
        '„{quote}“ (<a href="{page_url}" target="_blank">Scan, Bd. {band}, Scan {scan}</a>)<br>' +
        '<span style="font-size:smaller">Automatisch aus dem OCR-Text ermittelt (Schlüsselwörter), nicht an den Scans geprüft. Jagd: {episode}.</span>' }] } });
  await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
}
const n = (await get(url + '/query', { where: '1=1', returnCountOnly: true })).count;
const self = (await get(url + '/query', { where: 'ff_self = 1', returnCountOnly: true })).count;
const noEp = (await get(url + '/query', { where: 'episode IS NULL', returnCountOnly: true })).count;
JSON.stringify({ itemId, n, self, noEpisode: noEp, order: (await get(`${REST}/content/items/${WEBMAP}/data`)).operationalLayers.map(l => l.title) });
