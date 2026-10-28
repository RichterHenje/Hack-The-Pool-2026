// Sammlung Este objects (Weltmuseum) linked to the voyage as SUGGESTIONS with evidence, from the team's
// ke_enrichment.js objects[] (khm-team b5e1464; method: enrichment/README.md "Objects", 03d_objects.py).
// strong = the diary sentence speaks of buying or a gift, or the index card records a gift;
// medium = the object type is described in the diary on the days at that stop. date = that diary day.
// Placed at Franz Ferdinand's place on that day (days[] coordinates); 136 of 149 placeable.
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const ENR = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/kaiserin_elisabeth/prototype/data/ke_enrichment.js`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const txt = await (await fetch(ENR)).text();
const KEE = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1));
const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };
// < and > in OCR text trip ArcGIS's XSS filter ("unsafe html content", VO_109083 on 28.10.)
const clean = s => String(s || '').replace(/\s+/g, ' ').replace(/</g, '‹').replace(/>/g, '›').trim();
const DAY = Object.fromEntries(KEE.days.filter(d => d.lat != null).map(d => [d.date, d]));
const S = (name, length) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true });
const fields = [S('inventory', 64), S('obj_type', 128), S('title', 256), S('region', 256), S('strength', 16), S('strength_de', 160),
  { name: 'diary_date', type: 'esriFieldTypeDate', alias: 'diary_date', nullable: true, editable: true }, S('place', 128),
  S('evidence', 2048), S('url', 256), S('page_url', 256), { name: 'acquisition', type: 'esriFieldTypeInteger', alias: 'acquisition', nullable: true, editable: true }];
const SDE = { strong: 'stark: der Tagebuchsatz spricht von Kauf oder Geschenk, oder die Inventarkarte nennt ein Geschenk',
              medium: 'mittel: der Objekttyp wird an den Tagen dieser Station im Tagebuch beschrieben' };
const objs = KEE.objects.filter(o => o.date && DAY[o.date]);
const features = objs.map(o => { const d = DAY[o.date]; return { geometry: { x: d.lon, y: d.lat, spatialReference: { wkid: 4326 } }, attributes: {
  inventory: o.inventory, obj_type: o.type, title: o.title && o.title !== 'None' ? o.title : null, region: o.region, strength: o.strength,
  strength_de: SDE[o.strength] || o.strength, diary_date: toMs(o.date), place: d.place, evidence: clean(o.evidence).slice(0, 1000),
  url: o.url, page_url: o.page_url || d.page_url, acquisition: o.acquisition === true || o.acquisition === 'True' ? 1 : 0 } }; });

let url = SVC + 'KE1893_objects/FeatureServer/0', itemId;
const found = (await get(REST + '/search', { q: `owner:${USER} AND title:"KE 1892-93 Sammlung Este"`, num: 2 })).results[0];
if (found) { itemId = found.id; } else {
  const xs = features.map(f => f.geometry.x), ys = features.map(f => f.geometry.y);
  const extent = { xmin: Math.min(...xs), ymin: Math.min(...ys), xmax: Math.max(...xs), ymax: Math.max(...ys), spatialReference: { wkid: 4326 } };
  const svc = await post(`${REST}/content/users/${USER}/createService`, { outputType: 'featureService', createParameters: {
    name: 'KE1893_objects', serviceDescription: '', hasStaticData: false, maxRecordCount: 2000, supportedQueryFormats: 'JSON',
    capabilities: 'Create,Delete,Query,Update,Editing', spatialReference: { wkid: 4326 }, initialExtent: extent, allowGeometryUpdates: true,
    units: 'esriDecimalDegrees', xssPreventionInfo: { xssPreventionEnabled: true, xssPreventionRule: 'InputOnly', xssInputRule: 'rejectInvalid' } } });
  itemId = svc.itemId; url = svc.serviceurl + '/0';
  const admin = svc.serviceurl.replace('/rest/services/', '/rest/admin/services/');
  await post(admin + '/addToDefinition', { addToDefinition: { layers: [{ id: 0, name: 'KE 1892-93 Sammlung Este', type: 'Feature Layer', geometryType: 'esriGeometryPoint',
    objectIdField: 'OBJECTID', displayField: 'obj_type',
    fields: [{ name: 'OBJECTID', type: 'esriFieldTypeOID', alias: 'OBJECTID', nullable: false, editable: false }, ...fields],
    extent, hasAttachments: false, htmlPopupType: 'esriServerHTMLPopupTypeNone', capabilities: 'Create,Delete,Query,Update,Editing', supportsRollbackOnFailureParameter: true,
    drawingInfo: { renderer: { type: 'simple', symbol: { type: 'esriSMS', style: 'esriSMSDiamond', color: [120, 90, 20, 200], size: 7, outline: { color: [255, 255, 255, 200], width: 0.75 } } } },
    timeInfo: { startTimeField: 'diary_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays' } }] } });
  const add = await post(url + '/addFeatures', { rollbackOnFailure: true, features });
  if (add.addResults.some(r => !r.success)) throw new Error('addFeatures failed');
  const times = features.map(f => f.attributes.diary_date);
  await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: { startTimeField: 'diary_date', endTimeField: null, timeReference: null, timeInterval: 1, timeIntervalUnits: 'esriTimeUnitsDays', timeExtent: [Math.min(...times), Math.max(...times)] } } });
  await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } });
  await post(`${REST}/content/users/${USER}/items/${itemId}/update`, { title: 'KE 1892-93 Sammlung Este (Vorschläge mit Beleg)', tags: 'Hack the Pool 2026,Kaiserin Elisabeth,1892-93', snippet: `Team data at ${SHA.slice(0, 7)}; private demo` });
}
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
if (!d.operationalLayers.some(l => l.id === 'KE1893_objects')) {
  const at = d.operationalLayers.findIndex(l => l.id === 'KE1893_press');
  d.operationalLayers.splice(at, 0, { id: 'KE1893_objects', title: 'Sammlung Este (Vorschläge)', url, itemId, layerType: 'ArcGISFeatureLayer', visibility: true, opacity: 1,
    layerDefinition: { drawingInfo: { renderer: { type: 'uniqueValue', field1: 'strength',
      defaultSymbol: { type: 'esriSMS', style: 'esriSMSDiamond', color: [120, 90, 20, 140], size: 6, outline: { color: [255, 255, 255, 160], width: 0.5 } },
      uniqueValueInfos: [
        { value: 'strong', label: 'Objekt: Kauf oder Geschenk im Tagebuch belegt', symbol: { type: 'esriSMS', style: 'esriSMSDiamond', color: [120, 90, 20, 230], size: 10, outline: { color: [255, 255, 255, 230], width: 1 } } },
        { value: 'medium', label: 'Objekt: Typ im Tagebuch beschrieben (schwächer)', symbol: { type: 'esriSMS', style: 'esriSMSDiamond', color: [120, 90, 20, 120], size: 6, outline: { color: [255, 255, 255, 140], width: 0.5 } } }] } },
      featureReduction: { type: 'cluster', clusterRadius: 30 } },
    popupInfo: { title: '{obj_type} ({inventory})',
      fieldInfos: fields.map(f => ({ fieldName: f.name, label: f.name, visible: false, isEditable: false })),
      expressionInfos: [{ name: 'd', returnType: 'string', expression: "Text($feature.diary_date, 'D.M.Y')" }],
      popupElements: [{ type: 'text', text:
        'Herkunft laut Museum: {region}<br>Tagebuch, {expression/d} ({place}): „{evidence}“ (<a href="{page_url}" target="_blank">Scan</a>)<br>' +
        '<a href="{url}" target="_blank">Objekt im Weltmuseum Wien</a><br>' +
        '<span style="font-size:smaller">Verknüpfung ist ein Vorschlag, Stärke {strength_de}. Punkt = Ort Franz Ferdinands an diesem Tagebuchtag.</span>' }] } });
  await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
}
const count = (await get(url + '/query', { where: '1=1', returnCountOnly: true })).count;
const strong = (await get(url + '/query', { where: "strength = 'strong'", returnCountOnly: true })).count;
JSON.stringify({ itemId, sent: features.length, count, strong, order: (await get(`${REST}/content/items/${WEBMAP}/data`)).operationalLayers.map(l => l.title) });
