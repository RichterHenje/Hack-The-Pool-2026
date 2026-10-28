// QM check of the web map and all its layers (read-only). Run in a page of the org.
// Checks per operational layer: expected count, item access (ACCESS), read-only service, time extent within
// the voyage, no null geometries, every field referenced in pop-up text / Arcade / labels / renderer
// exists in the layer, definition expression parses (count query). Plus: sample image URLs load,
// sample scan/museum links are well-formed, the old photo layer is gone, bookmarks have time.
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const ACCESS = 'public'; // shared to Everyone on 28.10. (owner decision); was 'private'
const EXPECT = { KE1893_legs: 47, KE1893_days: 216, KE1893_stops: 48, KE1893_hunts: 18, KE1893_kills: 65, KE1893_objects: 136,
  KE1893_press: 104, KE1893_photos_undated: 357, KE1893_photos_dated: 357 };
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json();
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const V0 = Date.UTC(1892, 11, 1), V1 = Date.UTC(1893, 10, 1);
const issues = [], rows = [];
const refs = (s) => [...String(s || '').matchAll(/\{([a-zA-Z_][\w]*)\}/g)].map(m => m[1])
  .concat([...String(s || '').matchAll(/\$feature\.([a-zA-Z_]\w*)/g)].map(m => m[1]));
for (const l of d.operationalLayers) {
  const svcUrl = l.url.replace(/\/\d+$/, '');
  const lyr = await get(l.url), svc = await get(svcUrl), item = l.itemId ? await get(`${REST}/content/items/${l.itemId}`) : {};
  const names = new Set((lyr.fields || []).map(f => f.name).concat(['cluster_count']));
  const total = (await get(l.url + '/query', { where: '1=1', returnCountOnly: true })).count;
  const shown = (await get(l.url + '/query', { where: l.layerDefinition?.definitionExpression || '1=1', returnCountOnly: true }));
  const nullGeom = (await get(l.url + '/query', { where: '1=1', returnGeometry: true, outFields: 'OBJECTID', resultRecordCount: 2000 })).features.filter(f => !f.geometry).length;
  const p = l.popupInfo || {}, ld = l.layerDefinition || {}, r = ld.drawingInfo?.renderer || {};
  const used = [p.title, ...(p.popupElements || []).map(e => e.text || JSON.stringify(e.mediaInfos || '')), ...(p.expressionInfos || []).map(e => e.expression),
    ...(ld.drawingInfo?.labelingInfo || []).map(x => x.labelExpressionInfo?.expression), r.field1, r.valueExpression, ...(r.visualVariables || []).map(v => v.field)]
    .flatMap(s => s && !/^[a-zA-Z_]\w*$/.test(s) ? refs(s) : (s ? [s] : []));
  const exprNames = new Set((p.expressionInfos || []).map(e => e.name));
  const missing = [...new Set(used)].filter(n => !names.has(n) && !exprNames.has(n) && !['expression'].includes(n));
  const te = (lyr.timeInfo?.timeExtent || []);
  const timeOk = !lyr.timeInfo || (te[0] >= V0 && te[1] <= V1);
  const exp = EXPECT[l.id];
  const row = { id: l.id, total, shown: shown.count ?? ('ERR ' + JSON.stringify(shown.error)), expected: exp, access: item.access, caps: svc.capabilities,
    time: te.map(x => x == null ? null : new Date(x).toISOString().slice(0, 10)).join('..'), nullGeom, missingFields: missing };
  rows.push(row);
  if (exp != null && total !== exp) issues.push(`${l.id}: count ${total} != ${exp}`);
  if (item.access !== ACCESS) issues.push(`${l.id}: access ${item.access}`);
  if (svc.capabilities !== 'Query') issues.push(`${l.id}: capabilities ${svc.capabilities}`);
  if (!timeOk) issues.push(`${l.id}: time extent ${row.time}`);
  if (nullGeom) issues.push(`${l.id}: ${nullGeom} null geometries`);
  if (missing.length) issues.push(`${l.id}: unknown fields ${missing.join(',')}`);
  if (shown.error) issues.push(`${l.id}: definitionExpression fails`);
}
if (d.operationalLayers.some(l => l.id === 'KE1893_photos')) issues.push('old KE1893_photos still in the map');
if (!d.bookmarks.every(b => b.timeExtent)) issues.push('bookmark without time extent');
// sample images (12 random) and link formats
const P = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/KE1893_photos_all/FeatureServer/0/query';
const ph = (await get(P, { where: '1=1', outFields: 'vf_id,image_url,museum_url', returnGeometry: false })).features.map(f => f.attributes);
const sample = ph.sort(() => Math.random() - 0.5).slice(0, 12);
const loads = await Promise.all(sample.map(a => new Promise(res => { const im = new Image(); const t = setTimeout(() => res([a.vf_id, 'timeout']), 15000);
  im.onload = () => { clearTimeout(t); res([a.vf_id, im.naturalWidth > 0 ? 'ok' : 'empty']); }; im.onerror = () => { clearTimeout(t); res([a.vf_id, 'error']); }; im.src = a.image_url; })));
const badImg = loads.filter(x => x[1] !== 'ok');
if (badImg.length) issues.push('images not loading: ' + JSON.stringify(badImg));
const badMuseum = ph.filter(a => !/^https:\/\/www\.weltmuseumwien\.at\/objekte\/\d+$/.test(a.museum_url || '')).length;
if (badMuseum) issues.push(badMuseum + ' photos with unusual museum_url');
const scans = (await get('https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/KE1893_days/FeatureServer/0/query', { where: '1=1', outFields: 'page_url', returnGeometry: false })).features
  .filter(f => f.attributes.page_url && !/^https:\/\/archive\.org\/details\/tagebuchmeinerr0[01]ferdgoog\/page\/n\d+/.test(f.attributes.page_url)).length;
if (scans) issues.push(scans + ' diary days with unusual scan link'); // vol. 1 = …r01…, vol. 2 = …r00…; 4 days have none (handled in v10)
// since 28.10. (team a4b8b5a): every day's coordinate reference is a Wikidata or GeoNames link
const refsBad = (await get('https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/KE1893_days/FeatureServer/0/query', { where: 'coord_ref IS NOT NULL', outFields: 'coord_ref', returnGeometry: false })).features
  .filter(f => !/^https:\/\/(www\.wikidata\.org\/wiki\/Q\d+|sws\.geonames\.org\/\d+\/?)$/.test(f.attributes.coord_ref)).length;
if (refsBad) issues.push(refsBad + ' diary days with unusual coord_ref');
// since 28.10. (found by looking at the rendered app): points at 0/0 (placeholder coordinates in the
// team's places.json), legs that end before they start, and stations far from every diary day within
// three days of their arrival (wrong-name GeoNames matches such as Livingston NJ, Wyoming MI)
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const pts = async s => (await get(SVC + s + '/FeatureServer/0/query', { where: '1=1', outFields: '*', returnGeometry: true, outSR: 4326, resultRecordCount: 2000 })).features;
for (const s of ['KE1893_stops', 'KE1893_days', 'KE1893_hunts', 'KE1893_kills', 'KE1893_objects', 'KE1893_press', 'KE1893_photos_all']) {
  const z = (await pts(s)).filter(f => f.geometry && Math.abs(f.geometry.x) < 0.01 && Math.abs(f.geometry.y) < 0.01).length;
  if (z) issues.push(`${s}: ${z} points at 0/0`);
}
const legs = (await get(SVC + 'KE1893_legs/FeatureServer/0/query', { where: 'date_from IS NOT NULL AND date_to IS NOT NULL', outFields: 'from_name,to_name,date_from,date_to', returnGeometry: false })).features;
const inverted = legs.filter(f => f.attributes.date_from > f.attributes.date_to).map(f => f.attributes.from_name + '>' + f.attributes.to_name);
if (inverted.length) issues.push('legs ending before they start: ' + inverted.join(', '));
const RAD = Math.PI / 180, hav = (a, b, c, d) => 12742 * Math.asin(Math.sqrt(Math.sin((c - a) * RAD / 2) ** 2 + Math.cos(a * RAD) * Math.cos(c * RAD) * Math.sin((d - b) * RAD / 2) ** 2));
const stops = await pts('KE1893_stops'), dayPts = await pts('KE1893_days');
for (const s of stops) {
  const t = s.attributes.arrival_date; if (!t) continue;
  const near = dayPts.filter(d => Math.abs(d.attributes.day_date - t) <= 3 * 864e5); if (!near.length) continue;
  const km = Math.min(...near.map(d => hav(s.geometry.y, s.geometry.x, d.geometry.y, d.geometry.x)));
  if (km > 300) issues.push(`station ${s.attributes.name_then}: ${Math.round(km)} km from the diary days around its arrival`);
}
JSON.stringify({ issues, rows, imagesChecked: loads.length }, null, 0);
