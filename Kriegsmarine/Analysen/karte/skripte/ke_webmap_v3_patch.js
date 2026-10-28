// v3: patch (not rebuild) of web map 977298da… after the owner-side Map Viewer save that set
// "Show data progressively" (stored as timeSlider thumbCount 1). Reads the saved JSON, changes
// only: playback speed, German date format in pop-ups, labels that ignore diacritic-only
// differences (Pilibhit/Pīlibhīt, Nikko/Nikkō), photo cluster labels + cluster pop-up.
// Guard: refuses unless the map still has the structure this patch expects.
const ORG = location.origin, REST = ORG + '/sharing/rest';
const WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const L = Object.fromEntries(d.operationalLayers.map(l => [l.id, l]));
const ts = d.widgets?.timeSlider?.properties;
if (!ts || ts.thumbCount !== 1 || d.baseMap?.title !== 'Vintage Shaded Relief' ||
    !['KE1893_legs', 'KE1893_stops', 'KE1893_hunts', 'KE1893_photos'].every(k => L[k]))
  throw new Error('map is not in the expected state; not patching');

const D = 86400000;
ts.thumbMovingRate = 300;                       // ms per day: whole voyage in ~1.5 min
ts.currentTimeExtent = [null, ts.startTime + D]; // opens on 15.12.1892

const de = f => `IIf(IsEmpty($feature.${f}), '', Text($feature.${f}, 'D.M.Y'))`;
const plain = "function p(s) { var t = Lower(s); for (var k in ['ā','ī','ū','ō','ē']) { t = Replace(t, ['ā','ī','ū','ō','ē'][k], ['a','i','u','o','e'][k]); } return t; }";
const both = (fmt) => `${plain}
var a = $feature.name_then; var b = $feature.name_now;
IIf(!IsEmpty(b) && p(a) != p(b), ${fmt}, a)`;

// Stops: labels + title ignore diacritic-only differences; German arrival date.
const st = L.KE1893_stops;
st.layerDefinition.drawingInfo.labelingInfo[0].labelExpressionInfo.expression = both("a + ' (' + b + ')'");
const sx = st.popupInfo.expressionInfos;
sx.find(e => e.name === 'names').expression = both("a + ' (heute ' + b + ')'");
sx.push({ name: 'arr', returnType: 'string', expression: de('arrival_date') });
st.popupInfo.popupElements[0].text = st.popupInfo.popupElements[0].text.replace('{arrival_date}', '{expression/arr}');

// Legs and hunts: German dates.
for (const id of ['KE1893_legs', 'KE1893_hunts']) {
  const p = L[id].popupInfo;
  p.expressionInfos = (p.expressionInfos || []).concat([
    { name: 'from', returnType: 'string', expression: de('date_from') },
    { name: 'to', returnType: 'string', expression: de('date_to') }]);
  p.popupElements[0].text = p.popupElements[0].text.replace('{date_from}', '{expression/from}').replace('{date_to}', '{expression/to}');
}

// Photos: the image in the pop-up (owner decision 28.10.; field image_url from ke_photos_images.js),
// hot-linked from the museum's server, linked to the object page.
const ph = L.KE1893_photos;
ph.title = 'Fotos Weltmuseum Wien';
if (!ph.popupInfo.fieldInfos.some(f => f.fieldName === 'image_url'))
  ph.popupInfo.fieldInfos.push({ fieldName: 'image_url', label: 'image_url', visible: false, isEditable: false });
ph.popupInfo.popupElements = [
  { type: 'media', mediaInfos: [{ type: 'image', title: '', caption: 'Foto: Weltmuseum Wien, {vf_id}', altText: '{title}',
    value: { sourceURL: '{image_url}', linkURL: '{museum_url}' } }] },
  { type: 'text', text:
    'Titel (historische Bildunterschrift des Weltmuseums, zitiert): „{title}“<br>' +
    'Datum laut Museum: {museum_date} · Ort des Tages laut Route: {place_of_day}<br>' +
    '<span style="font-size:smaller">Verortung: {coord_source}</span><br>' +
    '<a href="{museum_url}" target="_blank">Objektseite im Weltmuseum Wien</a> (Bild vom Server des Museums geladen)' }];

// Photos: clusters show their count and have their own pop-up (Browse features lists the photos).
const fr = L.KE1893_photos.layerDefinition.featureReduction;
fr.labelsVisible = true;
fr.labelingInfo = [{ labelExpressionInfo: { expression: "Text($feature.cluster_count, '#,###')" },
  labelPlacement: 'esriServerPointLabelPlacementCenterCenter', deconflictionStrategy: 'none',
  symbol: { type: 'esriTS', color: [255, 255, 255, 255], font: { family: 'Arial', size: 9, weight: 'bold' }, haloColor: [30, 70, 120, 255], haloSize: 0.5 } }];
fr.popupEnabled = true;
fr.popupInfo = { title: '{cluster_count} Fotos der Weltreise an diesem Ort',
  fieldInfos: [{ fieldName: 'cluster_count', label: 'Anzahl', format: { places: 0, digitSeparator: true } }],
  popupElements: [{ type: 'text', text:
    'Weltmuseum Wien, Fotosammlung. Einzelne Fotos mit Bild: „Browse features“ (Funktionen durchsuchen).' }] };

await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
const back = await get(`${REST}/content/items/${WEBMAP}/data`);
JSON.stringify({ rate: back.widgets.timeSlider.properties.thumbMovingRate, thumbs: back.widgets.timeSlider.properties.thumbCount,
  clusterLabels: !!back.operationalLayers.find(l => l.id === 'KE1893_photos').layerDefinition.featureReduction.labelingInfo,
  stopsExpr: back.operationalLayers.find(l => l.id === 'KE1893_stops').popupInfo.expressionInfos.map(e => e.name) });
