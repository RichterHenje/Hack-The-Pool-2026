// v6 QM patch: wording that claimed more than the fields mean (same error class as on_ship).
// 1 Stops: kp_hits = records that name the place AND are dated 1890–1895 (segment years ±2,
//   scripts/ke_stop_records.py), not "1892–93".
// 2 Legs: date_from/date_to are the ARRIVAL dates at the two stops (export_dated.py build_legs),
//   not travel start/end.
// 3 Press: papers from all over the monarchy (Pester Lloyd, Prager Tagblatt, Graz, Linz …), not "Wien".
// 4 Photos: the point is Franz Ferdinand's place on the museum's date (route), not where the photo
//   was taken; show the museum's geography; mark date ranges.
// 5 Bookmarks 2 and 3 renamed: no mapped photo 5.–16.1.1893 (the "four sources" are not on the map);
//   Bombay, Calcutta, Colombo, Kandy do have Kulturpool hits.
const ORG = location.origin, REST = ORG + '/sharing/rest';
const WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const L = Object.fromEntries(d.operationalLayers.map(l => [l.id, l]));
if (!L.KE1893_press) throw new Error('map is not in the expected (v5) state');

// 1 Stops
const st = L.KE1893_stops;
st.popupInfo.expressionInfos.find(e => e.name === 'kp').expression =
  "IIf($feature.kp_hits > 0, $feature.kp_hits + ' Datensätze nennen den Ort und sind 1890–1895 datiert (Reisejahre ±2). Sie nennen den Ort, nicht die Reise.', 'Kein Datensatz nennt den Ort mit einer Datierung 1890–1895 (Reisejahre ±2).')";
const lab = { hit: 'Kulturpool: Datensätze 1890–1895 nennen den Ort', hit_est: 'Treffer, Ankunftsdatum geschätzt',
              none: 'Kulturpool: kein Datensatz 1890–1895 nennt den Ort', none_est: 'kein Treffer, Ankunftsdatum geschätzt' };
for (const u of st.layerDefinition.drawingInfo.renderer.uniqueValueInfos) u.label = lab[u.value] || u.label;

// 2 Legs
const lg = L.KE1893_legs.popupInfo;
lg.popupElements[0].text = 'Ankunft in {from_name}: {expression/from} · Ankunft in {to_name}: {expression/to}<br>{expression/mode}';
const mode = lg.expressionInfos.find(e => e.name === 'mode');
mode.expression = mode.expression.replace('Franz Ferdinand verließ die Elisabeth in Yokohama (Tagebuch, 24.8.1893).',
  'Letzter Tag an Bord der Elisabeth laut Tagebuch: 24.8.1893 in Yokohama.');

// 3 Press
const pr = L.KE1893_press;
pr.title = 'Presse (ANNO, ungeprüft)';
pr.layerDefinition.drawingInfo.renderer.label = 'Zeitungsbericht über die Jagd, am Erscheinungstag';

// 4 Photos
const ph = L.KE1893_photos.popupInfo;
ph.expressionInfos = [{ name: 'range', returnType: 'string', expression: "IIf($feature.date_range == 'ja', ' (Zeitraum; hier der erste Tag)', '')" }];
ph.popupElements[1].text =
  'Titel (historische Bildunterschrift des Weltmuseums, zitiert): „{title}“<br>' +
  'Datum laut Museum: {museum_date}{expression/range} · Geografie laut Museum: {museum_geography}<br>' +
  '<span style="font-size:smaller">Der Punkt zeigt, wo Franz Ferdinand an diesem Datum laut Route war ({place_of_day}), nicht den Aufnahmeort. Verortung: {coord_source}</span><br>' +
  '<a href="{museum_url}" target="_blank">Objektseite im Weltmuseum Wien</a> (Bild vom Server des Museums geladen)';

// 5 Bookmarks
const bm = d.bookmarks;
bm[1].name = '2 Ceylon: Jagd bei Kala Wewa, 10.–12.1.1893';
bm[2].name = '3 Indien abseits der Häfen: kein Kulturpool-Treffer';

await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d,
  description: 'Private demo for Hack the Pool 2026. Route and dates: Höfer (ed.) 2010 after the 1895 diary; leg dates are arrival dates. ' +
    'Stops coloured by whether Kulturpool records name the place and are dated 1890–1895 (voyage years ±2; the place, not the voyage). ' +
    'Photos: Weltmuseum Wien, placed where Franz Ferdinand was on the museum date (not the place shown). Press: ANNO/ÖNB, unchecked OCR. ' +
    'Names: GeoNames (CC BY 4.0), Wikidata (CC0). Data: team repo khm-team b5e1464.' });
const back = await get(`${REST}/content/items/${WEBMAP}/data`);
JSON.stringify({ bookmarks: back.bookmarks.map(b => b.name), press: back.operationalLayers.find(l => l.id === 'KE1893_press').title,
  stopLabels: back.operationalLayers.find(l => l.id === 'KE1893_stops').layerDefinition.drawingInfo.renderer.uniqueValueInfos.map(u => u.label) });
