// Starter web map (PRIVATE) over the four KE1893_* hosted layers made by ke_publish.js:
// time slider (1 day, current interval, the setting StoryMaps accepts), the six demo
// bookmarks from docs/13_arcgis_demo.md, labels with the historical name, dashed legs
// without the ship, photo clustering, pop-ups with links only (no Weltmuseum images).
// Styling beyond that is done by hand in Map Viewer. Run like ke_publish.js.
const ORG = location.origin, REST = ORG + '/sharing/rest';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const TITLE = 'SMS Kaiserin Elisabeth 1892–93 (Demo)';

const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;

const R = 6378137;
const merc = (lon, lat) => [lon * Math.PI / 180 * R, Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * R];
const ext = (x1, y1, x2, y2) => { const [a, b] = merc(x1, y1), [c, d] = merc(x2, y2); return { xmin: a, ymin: b, xmax: c, ymax: d, spatialReference: { wkid: 102100 } }; };

// Basemap: Esri "Vintage Shaded Relief" if found, else the org default.
let baseMap;
const bm = await get(REST + '/search', { q: 'title:"Vintage Shaded Relief" AND type:"Web Map" AND owner:esri*', num: 5 });
const hit = (bm.results || []).find(i => i.title === 'Vintage Shaded Relief');
if (hit) baseMap = (await get(`${REST}/content/items/${hit.id}/data`)).baseMap;
if (!baseMap) baseMap = (await get(REST + '/portals/self')).defaultBasemap;

const items = Object.fromEntries((await get(REST + '/search', { q: `owner:${USER} AND type:"Feature Service" AND title:KE*`, num: 20 }))
  .results.map(i => [i.url.split('/services/')[1].split('/')[0], i]));
const fieldInfos = async (name, show) => (await get(SVC + name + '/FeatureServer/0')).fields
  .filter(f => f.type !== 'esriFieldTypeOID')
  .map(f => ({ fieldName: f.name, label: f.name, visible: show.includes(f.name), isEditable: false,
               ...(f.type === 'esriFieldTypeDate' ? { format: { dateFormat: 'dayShortMonthYear' } } : {}) }));
const layer = async (name, title, show, extra = {}) => ({
  id: name, title, url: SVC + name + '/FeatureServer/0', itemId: items[name]?.id, layerType: 'ArcGISFeatureLayer',
  visibility: true, opacity: 1,
  popupInfo: { title: '{title}', fieldInfos: await fieldInfos(name, show), showAttachments: false,
               popupElements: [{ type: 'fields' }] },
  ...extra });
const text = (c, s) => ({ type: 'esriTS', color: c, haloColor: [255, 255, 255, 255], haloSize: 1, font: { family: 'Arial', size: s } });

const operationalLayers = [ // bottom -> top
  await layer('KE1893_legs', 'Etappen', ['date_from', 'date_to', 'on_ship'], { layerDefinition: { drawingInfo: { renderer: {
    type: 'uniqueValue', field1: 'on_ship',
    defaultSymbol: { type: 'esriSLS', style: 'esriSLSSolid', color: [140, 40, 30, 255], width: 2.25 },
    uniqueValueInfos: [{ value: 'nein', label: 'ohne Schiff (Franz Ferdinand an Land)',
      symbol: { type: 'esriSLS', style: 'esriSLSDash', color: [140, 40, 30, 255], width: 2 } }] } } } }),
  await layer('KE1893_stops', 'Stationen', ['name_then', 'name_now', 'arrival_date', 'description', 'kp_hits', 'kp_search_url', 'image_licence', 'image_record_url'],
    { layerDefinition: { drawingInfo: {
      renderer: { type: 'simple', symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [140, 40, 30, 230], size: 8, outline: { color: [255, 255, 255, 255], width: 1 } } },
      labelingInfo: [{ labelExpressionInfo: { expression: '$feature.name_then' }, labelPlacement: 'esriServerPointLabelPlacementAboveRight',
                       symbol: text([60, 30, 20, 255], 9), minScale: 0, maxScale: 0 }] } }, showLabels: true }),
  await layer('KE1893_hunts', 'Jagden', ['date_from', 'date_to', 'animals', 'description'], { layerDefinition: { drawingInfo: { renderer: { type: 'simple',
    symbol: { type: 'esriSMS', style: 'esriSMSTriangle', color: [200, 30, 30, 230], size: 10, outline: { color: [255, 255, 255, 255], width: 1 } } } } } }),
  await layer('KE1893_photos', 'Fotos Weltmuseum (nur Links)', ['photo_date', 'museum_date', 'place_of_day', 'museum_geography', 'vf_id', 'museum_url'],
    { layerDefinition: { drawingInfo: { renderer: { type: 'simple',
      symbol: { type: 'esriSMS', style: 'esriSMSSquare', color: [30, 70, 120, 220], size: 6, outline: { color: [255, 255, 255, 255], width: 0.75 } } } },
      featureReduction: { type: 'cluster', clusterRadius: 40 } } }),
];

const start = Date.UTC(1892, 11, 15, 12), end = Date.UTC(1893, 9, 17, 12);
const webmap = {
  operationalLayers, baseMap, spatialReference: { wkid: 102100, latestWkid: 3857 },
  version: '2.29', authoringApp: 'ArcGIS Online', authoringAppVersion: '2026',
  initialState: { viewpoint: { targetGeometry: ext(-130, -45, 179, 62) } },
  bookmarks: [
    ['1 Europa / Rotes Meer', 5, 10, 50, 48], ['2 Ceylon (Kalawewa)', 78.5, 5.5, 82.5, 10.5],
    ['3 Hyderabad', 75, 14.5, 80.5, 20], ['4 Nepal Terai', 79, 25.5, 88.5, 30.5],
    ['5 Pazifik (Yokohama → Vancouver)', 130, 18, 245, 60], ['6 Le Havre', -2.5, 48, 2.5, 50.8],
  ].map(([name, ...b]) => ({ name, extent: ext(...b) })),
  widgets: { timeSlider: { properties: { startTime: start, endTime: end, thumbCount: 2, thumbMoves: true,
    timeStopInterval: { interval: 1, units: 'esriTimeUnitsDays' }, currentTimeExtent: [start, start + 86400000] } } },
};

const res = await post(`${REST}/content/users/${USER}/addItem`, {
  type: 'Web Map', title: TITLE, text: webmap,
  typeKeywords: 'ArcGIS Online,Explorer Web Map,Map,Online Map,Web Map',
  tags: 'Hack the Pool 2026,Kaiserin Elisabeth,1892-93',
  snippet: 'Private demo map for the Hack the Pool slam; data from the team repo (khm-team b5e1464).',
  extent: '-130,-45,179,62' });
if (items.KE1893_hunts && items.KE1893_hunts.title !== 'KE 1892-93 Jagden')
  await post(`${REST}/content/users/${USER}/items/${items.KE1893_hunts.id}/update`, { title: 'KE 1892-93 Jagden' });
const item = await get(`${REST}/content/items/${res.id}`);
JSON.stringify({ id: res.id, access: item.access, basemap: hit ? 'Vintage Shaded Relief' : 'org default', layers: operationalLayers.map(l => [l.title, !!l.itemId]),
  open: `${ORG}/apps/mapviewer/index.html?webmap=${res.id}` }, null, 1);
