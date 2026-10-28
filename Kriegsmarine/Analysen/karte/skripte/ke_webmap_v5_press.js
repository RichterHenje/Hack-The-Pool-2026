// v5 patch (after the comparison with the team's reise.html): adds the press layer KE1893_press
// (69 ANNO clippings, on the slider by publication date, rings around the hunt they report;
// pop-up: quote, newspaper, delay in days, ANNO link, "ungeprüft (OCR)") and sizes the hunts by
// kill_sentences, as the team's page does. Other layers untouched.
const ORG = location.origin, REST = ORG + '/sharing/rest';
const WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
if (d.operationalLayers.some(l => l.id === 'KE1893_press')) throw new Error('press layer already in the map');
const hunts = d.operationalLayers.find(l => l.id === 'KE1893_hunts');
if (!hunts) throw new Error('map is not in the expected state');

// Hunts: size by kill sentences (range read from the layer).
const ks = (await get(SVC + 'KE1893_hunts/FeatureServer/0/query', { where: '1=1', outFields: 'kill_sentences', returnGeometry: false }))
  .features.map(f => f.attributes.kill_sentences).filter(v => v != null);
hunts.layerDefinition.drawingInfo.renderer.visualVariables = [{ type: 'sizeInfo', field: 'kill_sentences',
  minDataValue: Math.min(...ks), maxDataValue: Math.max(...ks), minSize: 8, maxSize: 24,
  legendOptions: { title: 'Sätze über Abschüsse im Tagebuch (automatisch gezählt)' } }];

// Press layer.
const pItem = (await get(REST + '/search', { q: `owner:${USER} AND title:"KE 1892-93 Presse"`, num: 3 })).results[0];
const pFields = (await get(SVC + 'KE1893_press/FeatureServer/0')).fields.filter(f => f.type !== 'esriFieldTypeOID')
  .map(f => ({ fieldName: f.name, label: f.name, visible: false, isEditable: false }));
const press = {
  id: 'KE1893_press', title: 'Presse in Wien (ANNO, ungeprüft)', url: SVC + 'KE1893_press/FeatureServer/0', itemId: pItem.id,
  layerType: 'ArcGISFeatureLayer', visibility: true, opacity: 1,
  layerDefinition: { drawingInfo: { renderer: { type: 'simple', label: 'Zeitungsbericht, am Tag des Erscheinens',
    symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [0, 0, 0, 0], size: 16, outline: { color: [50, 50, 50, 230], width: 1.25 } } } } },
  popupInfo: { title: '{newspaper}, {expression/pub}', fieldInfos: pFields,
    expressionInfos: [
      { name: 'pub', returnType: 'string', expression: "Text($feature.date_published, 'D.M.Y')" },
      { name: 'ev', returnType: 'string', expression: "Text($feature.event_date, 'D.M.Y')" },
      { name: 'lag', returnType: 'string', expression: "Text(DateDiff($feature.date_published, $feature.event_date, 'days'), '#')" }],
    popupElements: [{ type: 'text', text:
      '„{quote}“<br>Zur Jagd: {place} ({expression/ev}); erschienen {expression/lag} Tage danach.<br>' +
      '<a href="{page_url}" target="_blank">Seite in ANNO (Österreichische Nationalbibliothek)</a><br>' +
      '<span style="font-size:smaller"><i>{status}</i>: Text per OCR, automatisch der Jagd zugeordnet.</span>' }] } };
const hi = d.operationalLayers.indexOf(hunts);
d.operationalLayers.splice(hi + 1, 0, press); // directly above the hunts

await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
const back = await get(`${REST}/content/items/${WEBMAP}/data`);
JSON.stringify({ order: back.operationalLayers.map(l => l.title), huntSize: [Math.min(...ks), Math.max(...ks)] });
