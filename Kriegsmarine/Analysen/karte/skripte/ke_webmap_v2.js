// v2 of the starter web map, written IN PLACE over item 977298da… (v1 = ke_webmap.js, the backup).
// Changes (docs/14_improvements.md, bucket 1): basemap Vintage Shaded Relief (no modern labels);
// stops in four classes = Kulturpool names the place 1892-93 or not x arrival dated or estimated;
// labels with both names; estimated legs dotted; pop-ups in plain wording (quoted museum captions,
// hunts unchecked, Kulturpool hits name the place, not the voyage); bookmarks as an argument with
// time extents from 15.12.1892 to the day; progressive slider. No 1914 borders (checked: Triest
// falls in "Italy"). Hosted layers untouched. Refuses to run if the item was saved by hand.
const ORG = location.origin, REST = ORG + '/sharing/rest';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const WEBMAP = '977298da4e1a47c380c77a9041e11908';
const VINTAGE = 'a8588e0401e246469260f03ee44d69f1';

const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;

// Guard: stop if the owner saved the map by hand (modified well after created).
const item = await get(`${REST}/content/items/${WEBMAP}`);
if (item.modified - item.created > 5 * 60 * 1000) throw new Error('web map was edited after creation; not overwriting');

// Basemap: check the tiling scheme before using it.
const vItem = await get(`${REST}/content/items/${VINTAGE}`);
const vSvc = await (await fetch(vItem.url + '?f=json')).json();
if ((vSvc.spatialReference || {}).latestWkid !== 3857 && (vSvc.spatialReference || {}).wkid !== 102100)
  throw new Error('Vintage Shaded Relief is not Web Mercator: ' + JSON.stringify(vSvc.spatialReference));
const baseMap = { title: 'Vintage Shaded Relief', baseMapLayers: [{ id: 'vintage', title: 'Vintage Shaded Relief',
  layerType: 'ArcGISTiledMapServiceLayer', url: vItem.url, visibility: true, opacity: 1 }] };

// Dates for the bookmarks come from the stops layer itself.
const stops = (await get(SVC + 'KE1893_stops/FeatureServer/0/query', { where: '1=1', outFields: 'name_then,arrival_date,country', returnGeometry: false }))
  .features.map(f => f.attributes);
const day = n => { const s = stops.find(s => s.name_then === n); if (!s || !s.arrival_date) throw new Error('no date for ' + n); return s.arrival_date; };
const D = 86400000, START = Date.UTC(1892, 11, 15, 12), END = Date.UTC(1893, 9, 17, 12);
const lastIndia = Math.max(...stops.filter(s => s.country === 'IN' && s.arrival_date).map(s => s.arrival_date));

const R = 6378137;
const merc = (lon, lat) => [lon * Math.PI / 180 * R, Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * R];
const ext = (x1, y1, x2, y2) => { const [a, b] = merc(x1, y1), [c, d] = merc(x2, y2); return { xmin: a, ymin: b, xmax: c, ymax: d, spatialReference: { wkid: 102100 } }; };
const bm = (name, box, until) => ({ name, extent: ext(...box), timeExtent: [START, until + D] });

const items = Object.fromEntries((await get(REST + '/search', { q: `owner:${USER} AND type:"Feature Service" AND title:KE*`, num: 20 }))
  .results.map(i => [i.url.split('/services/')[1].split('/')[0], i]));
const fieldInfos = async name => (await get(SVC + name + '/FeatureServer/0')).fields
  .filter(f => f.type !== 'esriFieldTypeOID')
  .map(f => ({ fieldName: f.name, label: f.name, visible: false, isEditable: false,
               ...(f.type === 'esriFieldTypeDate' ? { format: { dateFormat: 'dayShortMonthYear' } } : {}) }));
const text = (c, s) => ({ type: 'esriTS', color: c, haloColor: [250, 245, 235, 255], haloSize: 1.5, font: { family: 'Arial', size: s } });
const RED = [140, 40, 30, 255], GREY = [110, 110, 110, 255];
const marker = (fill, outline, dash) => ({ type: 'esriSMS', style: 'esriSMSCircle', size: 9, color: fill,
  outline: { type: 'esriSLS', style: dash ? 'esriSLSDash' : 'esriSLSSolid', color: outline, width: 1.5 } });
const layer = async (name, title, popupInfo, layerDefinition, extra = {}) => ({
  id: name, title, url: SVC + name + '/FeatureServer/0', itemId: items[name]?.id, layerType: 'ArcGISFeatureLayer',
  visibility: true, opacity: 1, popupInfo: { ...popupInfo, fieldInfos: await fieldInfos(name) }, layerDefinition, ...extra });

const operationalLayers = [ // bottom -> top
  await layer('KE1893_legs', 'Etappen', {
    title: '{title}',
    expressionInfos: [{ name: 'mode', returnType: 'string', expression:
      "IIf($feature.on_ship == 'nein', 'Franz Ferdinand ohne das Schiff (andere Schiffe, Bahn)', 'an Bord der Kaiserin Elisabeth') + IIf($feature.estimated == 1, '; Datum geschätzt', '')" }],
    popupElements: [{ type: 'text', text: '{date_from} – {date_to}<br>{expression/mode}' }] },
    { drawingInfo: { renderer: { type: 'uniqueValue',
      valueExpression: "IIf($feature.estimated == 1, 'est', IIf($feature.on_ship == 'nein', 'land', 'ship'))",
      defaultSymbol: { type: 'esriSLS', style: 'esriSLSSolid', color: RED, width: 2.25 },
      uniqueValueInfos: [
        { value: 'ship', label: 'an Bord', symbol: { type: 'esriSLS', style: 'esriSLSSolid', color: RED, width: 2.25 } },
        { value: 'land', label: 'ohne das Schiff', symbol: { type: 'esriSLS', style: 'esriSLSDash', color: RED, width: 2 } },
        { value: 'est', label: 'Datum geschätzt', symbol: { type: 'esriSLS', style: 'esriSLSDot', color: [140, 40, 30, 170], width: 2 } }] } } }),
  await layer('KE1893_stops', 'Stationen', {
    title: '{expression/names}',
    expressionInfos: [
      { name: 'names', returnType: 'string', expression:
        "IIf(!IsEmpty($feature.name_now) && $feature.name_now != $feature.name_then, $feature.name_then + ' (heute ' + $feature.name_now + ')', $feature.name_then)" },
      { name: 'est', returnType: 'string', expression: "IIf($feature.date_estimated == 1, ' (geschätzt, zwischen den Nachbarstationen)', '')" },
      { name: 'kp', returnType: 'string', expression:
        "IIf($feature.kp_hits > 0, $feature.kp_hits + ' Datensätze nennen den Ort in den Jahren der Reise. Sie nennen den Ort, nicht die Reise.', 'Kein Datensatz nennt den Ort in den Jahren der Reise.')" }],
    popupElements: [{ type: 'text', text:
      'Ankunft laut Höfer (2010, nach dem Tagebuch): {arrival_date}{expression/est}<br>' +
      '<b>Kulturpool:</b> {expression/kp} <a href="{kp_search_url}" target="_blank">Suche öffnen</a><br>' +
      '<span style="font-size:smaller">Namen: {names_history}</span>' }] },
    { drawingInfo: {
      renderer: { type: 'uniqueValue',
        valueExpression: "IIf($feature.kp_hits > 0, 'hit', 'none') + IIf($feature.date_estimated == 1, '_est', '')",
        defaultSymbol: marker([250, 245, 235, 255], GREY, false),
        uniqueValueInfos: [
          { value: 'hit', label: 'Kulturpool nennt den Ort 1892–93', symbol: marker([140, 40, 30, 230], [255, 255, 255, 255], false) },
          { value: 'hit_est', label: 'nennt den Ort, Datum geschätzt', symbol: marker([140, 40, 30, 130], RED, true) },
          { value: 'none', label: 'Kulturpool nennt den Ort 1892–93 nicht', symbol: marker([250, 245, 235, 230], GREY, false) },
          { value: 'none_est', label: 'nennt den Ort nicht, Datum geschätzt', symbol: marker([250, 245, 235, 160], GREY, true) }] },
      labelingInfo: [{ labelExpressionInfo: { expression:
        "IIf(!IsEmpty($feature.name_now) && $feature.name_now != $feature.name_then, $feature.name_then + ' (' + $feature.name_now + ')', $feature.name_then)" },
        labelPlacement: 'esriServerPointLabelPlacementAboveRight', symbol: text([60, 30, 20, 255], 9.5), minScale: 0, maxScale: 0 }] } },
    { showLabels: true }),
  await layer('KE1893_hunts', 'Jagden (laut Tagebuch)', {
    title: '{title}',
    popupElements: [{ type: 'text', text:
      'Jagd laut Tagebuch, {date_from} – {date_to}: {animals}.<br>Automatisch aus dem Tagebuchtext ermittelt ({kill_sentences} Sätze), noch nicht an den Scans geprüft.' }] },
    { drawingInfo: { renderer: { type: 'simple',
      symbol: { type: 'esriSMS', style: 'esriSMSTriangle', color: [120, 70, 40, 220], size: 10, outline: { color: [255, 255, 255, 255], width: 1 } } } } }),
  await layer('KE1893_photos', 'Fotos Weltmuseum (nur Links)', {
    title: 'Foto {vf_id}',
    popupElements: [{ type: 'text', text:
      'Titel (historische Bildunterschrift des Weltmuseums, zitiert): „{title}“<br>' +
      'Datum laut Museum: {museum_date} · Ort des Tages laut Route: {place_of_day}<br>' +
      '<span style="font-size:smaller">Verortung: {coord_source}</span><br>' +
      '<a href="{museum_url}" target="_blank">Objekt im Weltmuseum Wien</a> (Bildrechte beim Museum, daher nur ein Link)' }] },
    { drawingInfo: { renderer: { type: 'simple',
      symbol: { type: 'esriSMS', style: 'esriSMSSquare', color: [30, 70, 120, 220], size: 6, outline: { color: [255, 255, 255, 255], width: 0.75 } } } },
      featureReduction: { type: 'cluster', clusterRadius: 40 } }),
];

const webmap = {
  operationalLayers, baseMap, spatialReference: { wkid: 102100, latestWkid: 3857 },
  version: '2.29', authoringApp: 'ArcGIS Online', authoringAppVersion: '2026',
  initialState: { viewpoint: { targetGeometry: ext(-130, -45, 179, 62) } },
  bookmarks: [
    bm('1 Triest, 15.12.1892: Abfahrt', [8, 33, 38, 49], START),
    bm('2 Ceylon, 11.1.1893: vier Quellen, ein Tag', [78.5, 5.5, 82.5, 10.5], Date.UTC(1893, 0, 11, 12)),
    bm('3 Indien: wo der Kulturpool nichts nennt', [68, 15, 92, 32], lastIndia),
    bm('4 Hyderabad, 24.–26.1.1893: Fotos', [75, 14.5, 80.5, 20], Date.UTC(1893, 0, 26, 12)),
    bm('5 Japan → Pazifik → Vancouver', [125, 18, 245, 58], day('Vancouver')),
    bm('6 Zurück in Europa: Le Havre', [-6, 40, 16, 54], day('Le Havre')),
  ],
  widgets: { timeSlider: { properties: { startTime: START, endTime: END, thumbCount: 2, thumbMoves: false,
    timeStopInterval: { interval: 1, units: 'esriTimeUnitsDays' }, currentTimeExtent: [START, START + D] } } },
};

await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, {
  text: webmap,
  description: 'Private demo for Hack the Pool 2026. Route and dates: Höfer (ed.) 2010 after the 1895 diary. ' +
    'Stops coloured by whether Kulturpool records name the place in 1892–93 (the place, not the voyage). ' +
    'Photos: Weltmuseum Wien, links only. Names: GeoNames (CC BY 4.0), Wikidata (CC0). Press: ANNO/ÖNB (unchecked OCR). ' +
    'Data: team repo khm-team b5e1464.',
  accessInformation: 'Basemap: Kenneth Townsend, NASA, Natural Earth, John Nelson (Esri). Data: Hack the Pool team; Kulturpool per record; GeoNames; Wikidata; Weltmuseum Wien (links).' });
const after = await get(`${REST}/content/items/${WEBMAP}`);
JSON.stringify({ updated: true, access: after.access, basemapSR: vSvc.spatialReference.latestWkid || vSvc.spatialReference.wkid,
  bookmarks: webmap.bookmarks.map(b => b.name + ' → ' + new Date(b.timeExtent[1]).toISOString().slice(0, 10)),
  layers: operationalLayers.map(l => [l.title, !!l.itemId]) }, null, 1);
