// v4 patch: the legs' "on_ship" does not mean "on board". scripts/ke_itinerary.py sets it True
// for every leg of the vault's route section before Yokohama (incl. Franz Ferdinand's land
// journeys in India, Java, Japan) and False after it. Lines are straight connections. Legend and
// pop-up now say that; the two crossings are named after the diary (FF Tagebuch Bd. 2: Yokohama,
// 24.8.1893, last day on the Elisabeth, then the "Empress of China" of the Canadian Pacific
// Railway Company to Vancouver; from Vancouver the CPR train; the Atlantic on the "Bretagne").
const ORG = location.origin, REST = ORG + '/sharing/rest';
const WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const legs = d.operationalLayers.find(l => l.id === 'KE1893_legs');
if (!legs || d.widgets?.timeSlider?.properties?.thumbMovingRate !== 300) throw new Error('map is not in the expected (v3) state');

const r = legs.layerDefinition.drawingInfo.renderer;
const lab = { ship: 'Reiseabschnitt mit der Kaiserin Elisabeth (Landreisen in Indien, Java, Japan eingeschlossen)',
              land: 'ab Yokohama ohne die Elisabeth (Empress of China, Bahn, Bretagne)',
              est: 'Datum geschätzt' };
for (const u of r.uniqueValueInfos) u.label = lab[u.value] || u.label;
legs.title = 'Etappen (Luftlinie)';
legs.popupInfo.expressionInfos.find(e => e.name === 'mode').expression = `
var t = $feature.to_name;
var m = IIf($feature.on_ship == 'nein',
  When(t == 'Vancouver', 'Über den Pazifik mit der „Empress of China“ (Canadian Pacific Railway Company); Franz Ferdinand verließ die Elisabeth in Yokohama (Tagebuch, 24.8.1893).',
       t == 'Le Havre', 'Über den Atlantik mit der „Bretagne“ (Tagebuch).',
       'Ohne die Elisabeth, über Land.'),
  'Abschnitt der Reise mit der Kaiserin Elisabeth. Ob zu Schiff oder über Land, zeigt die Linie nicht.');
m + IIf($feature.estimated == 1, ' Datum geschätzt.', '') + ' Die Linie ist eine Luftlinie, nicht der Weg.'`;

await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
const back = (await get(`${REST}/content/items/${WEBMAP}/data`)).operationalLayers.find(l => l.id === 'KE1893_legs');
JSON.stringify({ title: back.title, labels: back.layerDefinition.drawingInfo.renderer.uniqueValueInfos.map(u => u.value + ': ' + u.label) });
