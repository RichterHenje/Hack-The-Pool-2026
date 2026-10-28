// Publish the Kaiserin Elisabeth 1892-93 demo layers to ArcGIS Online as PRIVATE hosted
// feature layers with real Date fields, so the Map Viewer time slider works.
//
// How it runs: pasted into a page on the owner's org (any /sharing/rest JSON page) while the
// owner is signed in; the session token comes from oauth2/platformSelf and never leaves the
// page. Set RUN below, then run the whole file. Nothing is ever shared (no group, no org,
// no Everyone): the account cannot create groups, and its org is a foreign Hub community.
//
// Route: createService -> addToDefinition (admin URL) -> addFeatures from the team's GeoJSON,
// dates written as epoch ms at 12:00 UTC (so no time zone shifts the day). No CSV parsing:
// the CSVs carry a BOM, embedded newlines and 72 photo rows without coordinates.
//
// Data pinned to team repo RichterHenje/Hack-The-Pool-2026, branch khm-team at:
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const RUN = 'test'; // 'test' | 'publish' | 'publish:<stops|legs|photos|hunts>' | 'delete:<itemId>'

const ORG = location.origin, REST = ORG + '/sharing/rest';
const RAW = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/kaiserin_elisabeth/prototype/arcgis/`;
const PREFIX = 'KE1893_';
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const RENAME = { date: 'photo_date' }; // "date" is an SQL keyword

const LAYERS = [
  { file: 'ke_stops_dated', name: 'stops', title: 'KE 1892-93 Stationen', start: 'arrival_date' },
  { file: 'ke_legs', name: 'legs', title: 'KE 1892-93 Etappen', start: 'date_from', end: 'date_to' },
  { file: 'ke_photos_dated', name: 'photos', title: 'KE 1892-93 Fotos Weltmuseum (Links)', start: 'photo_date' },
  { file: 'ke_hunts', name: 'hunts', title: 'KE 1892-93 Jagden', start: 'date_from', end: 'date_to' },
  // 28.10.: added after comparing with the team's reise.html; on the slider by publication date
  { file: 'ke_press', name: 'press', title: 'KE 1892-93 Presse (ANNO, ungeprüft)', start: 'date_published' },
];

let TOKEN, USER;
async function login() {
  const r = await fetch(REST + '/oauth2/platformSelf?f=json', {
    method: 'POST', credentials: 'include',
    headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline',
               'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } });
  const t = await r.json();
  if (!t.token) throw new Error('not signed in: ' + JSON.stringify(t.error || t));
  TOKEN = t.token;
  USER = (await get(REST + '/community/self')).username;
}
async function get(url, params = {}) {
  const q = new URLSearchParams({ ...params, f: 'json', token: TOKEN });
  const j = await (await fetch(url + '?' + q)).json();
  if (j.error) throw new Error(url + ' -> ' + JSON.stringify(j.error));
  return j;
}
async function post(url, params = {}) {
  const b = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v));
  b.append('f', 'json'); b.append('token', TOKEN);
  const j = await (await fetch(url, { method: 'POST', body: b })).json();
  if (j.error) throw new Error(url + ' -> ' + JSON.stringify(j.error));
  return j;
}

const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };
const empty = v => v === '' || v === null || v === undefined;

// Field types from the data: all non-empty values a date -> Date; all integers -> Integer;
// else String sized to at least twice the longest value (default 256 would truncate).
function schema(features) {
  const keys = [...new Set(features.flatMap(f => Object.keys(f.properties)))];
  return keys.map(k => {
    const vals = features.map(f => f.properties[k]).filter(v => !empty(v));
    const name = RENAME[k] || k;
    if (vals.length && vals.every(v => typeof v === 'string' && DATE_RE.test(v)))
      return { src: k, name, type: 'esriFieldTypeDate', alias: name, nullable: true, editable: true };
    if (vals.length && vals.every(v => Number.isInteger(v)))
      return { src: k, name, type: 'esriFieldTypeInteger', alias: name, nullable: true, editable: true };
    const mx = Math.max(0, ...vals.map(v => String(v).length));
    let length = 256; while (length < 2 * mx) length *= 2;
    return { src: k, name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true };
  });
}
function attrs(props, fields) {
  const a = {};
  for (const f of fields) {
    const v = props[f.src];
    a[f.name] = empty(v) ? null : f.type === 'esriFieldTypeDate' ? toMs(v) : v;
  }
  return a;
}
function geom(g) {
  const sr = { wkid: 4326 };
  if (g.type === 'Point') return { x: g.coordinates[0], y: g.coordinates[1], spatialReference: sr };
  if (g.type === 'LineString') return { paths: [g.coordinates], spatialReference: sr };
  if (g.type === 'MultiLineString') return { paths: g.coordinates, spatialReference: sr };
  throw new Error('geometry ' + g.type);
}
function bbox(features) {
  const pts = features.flatMap(f => f.geometry.type === 'Point' ? [f.geometry.coordinates]
    : f.geometry.type === 'LineString' ? f.geometry.coordinates : f.geometry.coordinates.flat());
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  return { xmin: Math.min(...xs), ymin: Math.min(...ys), xmax: Math.max(...xs), ymax: Math.max(...ys), spatialReference: { wkid: 4326 } };
}

// One private hosted feature service with one layer; returns ids, url and verification.
async function publishLayer(name, title, features, start, end) {
  const fields = schema(features);
  const isLine = features[0].geometry.type !== 'Point';
  const extent = bbox(features);
  const svc = await post(`${REST}/content/users/${USER}/createService`, {
    outputType: 'featureService',
    createParameters: {
      name: PREFIX + name, serviceDescription: '', hasStaticData: false, maxRecordCount: 2000,
      supportedQueryFormats: 'JSON', capabilities: 'Create,Delete,Query,Update,Editing',
      spatialReference: { wkid: 4326 }, initialExtent: extent, allowGeometryUpdates: true,
      units: 'esriDecimalDegrees',
      xssPreventionInfo: { xssPreventionEnabled: true, xssPreventionRule: 'InputOnly', xssInputRule: 'rejectInvalid' } } });
  const admin = svc.serviceurl.replace('/rest/services/', '/rest/admin/services/');
  const symbol = isLine
    ? { type: 'esriSLS', style: 'esriSLSSolid', color: [140, 40, 30, 255], width: 2 }
    : { type: 'esriSMS', style: 'esriSMSCircle', color: [140, 40, 30, 200], size: 7,
        outline: { color: [255, 255, 255, 255], width: 1 } };
  await post(admin + '/addToDefinition', { addToDefinition: { layers: [{
    id: 0, name: title, type: 'Feature Layer',
    geometryType: isLine ? 'esriGeometryPolyline' : 'esriGeometryPoint',
    objectIdField: 'OBJECTID', displayField: fields.some(f => f.name === 'title') ? 'title' : fields[0].name,
    fields: [{ name: 'OBJECTID', type: 'esriFieldTypeOID', alias: 'OBJECTID', nullable: false, editable: false },
             ...fields.map(({ src, ...f }) => f)],
    extent, hasAttachments: false, htmlPopupType: 'esriServerHTMLPopupTypeNone',
    capabilities: 'Create,Delete,Query,Update,Editing', supportsRollbackOnFailureParameter: true,
    drawingInfo: { renderer: { type: 'simple', symbol } },
    timeInfo: { startTimeField: start, endTimeField: end || null, timeReference: null,
                timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays' } }] } });
  const url = svc.serviceurl + '/0';
  const add = await post(url + '/addFeatures', { rollbackOnFailure: true,
    features: features.map(f => ({ geometry: geom(f.geometry), attributes: attrs(f.properties, fields) })) });
  const failed = add.addResults.filter(r => !r.success);
  // Time extent written explicitly from the data, then editing switched off again.
  const times = features.flatMap(f => [f.properties[start], end && f.properties[end]])
    .filter(v => !empty(v)).map(toMs);
  await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: {
    startTimeField: start, endTimeField: end || null, timeReference: null, timeInterval: 1,
    timeIntervalUnits: 'esriTimeUnitsDays', timeExtent: [Math.min(...times), Math.max(...times)] } } });
  await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } });
  await post(`${REST}/content/users/${USER}/items/${svc.itemId}/update`,
             { title, tags: 'Hack the Pool 2026,Kaiserin Elisabeth,1892-93', snippet: `Team data at ${SHA.slice(0, 7)}; private demo` });
  return { name: PREFIX + name, itemId: svc.itemId, url, sent: features.length,
           added: add.addResults.length - failed.length, failed: failed.length, fields };
}

async function verify(res, dateField) {
  const lyr = await get(res.url);
  const count = (await get(res.url + '/query', { where: '1=1', returnCountOnly: true })).count;
  const item = await get(`${REST}/content/items/${res.itemId}`);
  return { name: res.name, itemId: res.itemId, access: item.access, count, sent: res.sent, failed: res.failed,
           dateType: (lyr.fields.find(f => f.name === dateField) || {}).type, caps: lyr.capabilities,
           timeInfo: lyr.timeInfo && { start: lyr.timeInfo.startTimeField, end: lyr.timeInfo.endTimeField,
             extent: (lyr.timeInfo.timeExtent || []).map(ms => ms === null ? null : new Date(ms).toISOString().slice(0, 10)) },
           url: res.url };
}

async function dateTest() {
  const pt = (d, x) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [x, 45] },
                          properties: { title: 'test ' + (d || 'null'), arrival_date: d } });
  const res = await publishLayer('datetest', 'KE date test (delete me)',
                                 [pt('1892-12-15', 13), pt('1893-01-11', 14), pt('', 15)], 'arrival_date');
  const rows = (await get(res.url + '/query', { where: '1=1', outFields: 'title,arrival_date', returnGeometry: false }))
    .features.map(f => f.attributes);
  const after1893 = (await get(res.url + '/query', { where: "arrival_date >= DATE '1893-01-01'", outFields: 'title', returnGeometry: false }))
    .features.map(f => f.attributes.title);
  return { ...(await verify(res, 'arrival_date')),
           rows: rows.map(r => ({ title: r.title, ms: r.arrival_date, iso: r.arrival_date === null ? null : new Date(r.arrival_date).toISOString() })),
           expectedMs: [toMs('1892-12-15'), toMs('1893-01-11'), null], after1893 };
}

// All four run longer than claude-in-chrome's 45 s limit (the page keeps going and
// finishes); 'publish:<name>' does one layer per call.
async function publishAll(only) {
  const out = [];
  for (const L of LAYERS.filter(L => !only || L.name === only)) {
    try {
      const fc = await (await fetch(RAW + L.file + '.geojson')).json();
      const res = await publishLayer(L.name, L.title, fc.features, L.start, L.end);
      out.push(await verify(res, L.start));
    } catch (e) { out.push({ layer: L.name, error: String(e.message || e) }); break; }
  }
  return out;
}

async function remove(itemId) {
  const item = await get(`${REST}/content/items/${itemId}`);
  if (!/delete me|^KE /.test(item.title)) throw new Error('refusing to delete item not made by this script: ' + item.title);
  return { deleted: item.title, ...(await post(`${REST}/content/users/${USER}/items/${itemId}/delete`)) };
}

await login();
let result;
try {
  result = RUN === 'test' ? await dateTest()
    : RUN === 'publish' ? await publishAll()
    : RUN.startsWith('publish:') ? await publishAll(RUN.slice(8))
    : RUN.startsWith('delete:') ? await remove(RUN.slice(7))
    : 'unknown RUN';
} catch (e) { result = { error: String(e.message || e) }; }
JSON.stringify(result, null, 1);
