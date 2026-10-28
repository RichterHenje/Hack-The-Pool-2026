// Diary days as a private hosted layer KE1893_days + added to the web map (bottom, above the legs).
// Source: team ke_enrichment.js (khm-team b5e1464) days[]: 309 days, 206 with coordinates.
// Every pop-up says how the day was assigned (method) and where the coordinate comes from
// (coords), because 176 day starts are inferred by alignment with a website translation
// (docs/12_diary_days_quality.md). Run in a page of the org (see README).
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const ENR = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/kaiserin_elisabeth/prototype/data/ke_enrichment.js`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const METHOD = { heading: 'gedruckte Tagesüberschrift', aligned: 'erschlossen (Abgleich mit der englischen Tagesseite)', no_entry: 'kein eigener Eintrag' };
const COORDS = { hunt: 'Jagdort', heading: 'Ort der Überschrift', hand: 'von Hand gesetzt (Team)', site: 'englische Tagesseite', wikidata: 'Wikidata', sea: 'auf See', none: 'keine' };
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const txt = await (await fetch(ENR)).text();
const KEE = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1));
const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };
const S = (name, length) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true });
const fields = [{ name: 'day_date', type: 'esriFieldTypeDate', alias: 'day_date', nullable: true, editable: true },
  S('place', 128), S('heading', 256), S('method', 64), S('method_de', 128), S('coords', 32), S('coords_de', 64),
  { name: 'band', type: 'esriFieldTypeInteger', alias: 'band', nullable: true, editable: true },
  { name: 'scan', type: 'esriFieldTypeInteger', alias: 'scan', nullable: true, editable: true },
  S('page_url', 256), S('site_url', 256), { name: 'hunt_day', type: 'esriFieldTypeInteger', alias: 'hunt_day', nullable: true, editable: true }, S('episode', 64)];
const days = KEE.days.filter(d => d.lat != null && d.lon != null);
const features = days.map(d => ({ geometry: { x: d.lon, y: d.lat, spatialReference: { wkid: 4326 } }, attributes: {
  day_date: toMs(d.date), place: d.place, heading: d.heading, method: d.method, method_de: METHOD[d.method] || d.method,
  coords: d.coords, coords_de: COORDS[d.coords] || d.coords, band: d.band, scan: d.scan, page_url: d.page_url, site_url: d.site_url,
  hunt_day: d.hunt ? 1 : 0, episode: d.episode } }));

// service (skip if it exists)
let url = SVC + 'KE1893_days/FeatureServer/0', itemId;
const found = (await get(REST + '/search', { q: `owner:${USER} AND title:"KE 1892-93 Tagebuch"`, num: 2 })).results[0];
if (found) { itemId = found.id; } else {
  const xs = days.map(d => d.lon), ys = days.map(d => d.lat);
  const extent = { xmin: Math.min(...xs), ymin: Math.min(...ys), xmax: Math.max(...xs), ymax: Math.max(...ys), spatialReference: { wkid: 4326 } };
  const svc = await post(`${REST}/content/users/${USER}/createService`, { outputType: 'featureService', createParameters: {
    name: 'KE1893_days', serviceDescription: '', hasStaticData: false, maxRecordCount: 2000, supportedQueryFormats: 'JSON',
    capabilities: 'Create,Delete,Query,Update,Editing', spatialReference: { wkid: 4326 }, initialExtent: extent, allowGeometryUpdates: true,
    units: 'esriDecimalDegrees', xssPreventionInfo: { xssPreventionEnabled: true, xssPreventionRule: 'InputOnly', xssInputRule: 'rejectInvalid' } } });
  itemId = svc.itemId; url = svc.serviceurl + '/0';
  const admin = svc.serviceurl.replace('/rest/services/', '/rest/admin/services/');
  await post(admin + '/addToDefinition', { addToDefinition: { layers: [{ id: 0, name: 'KE 1892-93 Tagebuch', type: 'Feature Layer', geometryType: 'esriGeometryPoint',
    objectIdField: 'OBJECTID', displayField: 'heading',
    fields: [{ name: 'OBJECTID', type: 'esriFieldTypeOID', alias: 'OBJECTID', nullable: false, editable: false }, ...fields],
    extent, hasAttachments: false, htmlPopupType: 'esriServerHTMLPopupTypeNone', capabilities: 'Create,Delete,Query,Update,Editing', supportsRollbackOnFailureParameter: true,
    drawingInfo: { renderer: { type: 'simple', symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [90, 70, 50, 160], size: 4, outline: { color: [255, 255, 255, 120], width: 0.5 } } } },
    timeInfo: { startTimeField: 'day_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays' } }] } });
  const add = await post(url + '/addFeatures', { rollbackOnFailure: true, features });
  if (add.addResults.some(r => !r.success)) throw new Error('addFeatures failed');
  const times = features.map(f => f.attributes.day_date);
  await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: { startTimeField: 'day_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays', timeExtent: [Math.min(...times), Math.max(...times)] } } });
  await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } });
  await post(`${REST}/content/users/${USER}/items/${itemId}/update`, { title: 'KE 1892-93 Tagebuch (Tage mit Ort)', tags: 'Hack the Pool 2026,Kaiserin Elisabeth,1892-93', snippet: `Team data at ${SHA.slice(0, 7)}; private demo` });
}

// web map: add above the legs
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
if (!d.operationalLayers.some(l => l.id === 'KE1893_days')) {
  d.operationalLayers.splice(1, 0, { id: 'KE1893_days', title: 'Tagebuch (Tag für Tag)', url, itemId, layerType: 'ArcGISFeatureLayer', visibility: true, opacity: 1,
    layerDefinition: { drawingInfo: { renderer: { type: 'uniqueValue', field1: 'hunt_day',
      defaultSymbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [90, 70, 50, 160], size: 4, outline: { color: [255, 255, 255, 120], width: 0.5 } },
      uniqueValueInfos: [
        { value: '0', label: 'Tagebuchtag', symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [90, 70, 50, 160], size: 4, outline: { color: [255, 255, 255, 120], width: 0.5 } } },
        { value: '1', label: 'Tagebuchtag mit Jagd', symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [150, 60, 30, 200], size: 5, outline: { color: [255, 255, 255, 160], width: 0.5 } } }] } } },
    popupInfo: { title: 'Tagebuch, {expression/d}: {heading}',
      fieldInfos: fields.map(f => ({ fieldName: f.name, label: f.name, visible: false, isEditable: false })),
      expressionInfos: [{ name: 'd', returnType: 'string', expression: "Text($feature.day_date, 'D.M.Y')" }],
      popupElements: [{ type: 'text', text:
        'Ort: {place} · <a href="{page_url}" target="_blank">Scan im Tagebuch (Bd. {band}, Scan {scan}, archive.org)</a> · ' +
        '<a href="{site_url}" target="_blank">englische Tagesseite</a><br>' +
        '<span style="font-size:smaller">Tageszuordnung: {method_de}. Koordinate aus: {coords_de}. Quelle: Franz Ferdinand, Tagebuch meiner Reise um die Erde (1895), Datensatz des Teams.</span>' }] } });
  await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
}
const count = (await get(url + '/query', { where: '1=1', returnCountOnly: true })).count;
const order = (await get(`${REST}/content/items/${WEBMAP}/data`)).operationalLayers.map(l => l.title);
JSON.stringify({ itemId, sent: features.length, count, order });
