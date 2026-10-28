// v9 (28.10. ~04:30, after the visual check of the new layers):
// - diary-day pop-up title without a trailing colon when the day has no heading;
// - Sammlung Este shows only the 18 "strong" links (purchase or gift in the diary sentence, or a gift
//   on the index card). The 131 "medium" links stay in the layer but are filtered out: the check found
//   e.g. a toy horse (votive offering) linked to a sentence about rest houses with horses.
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const L = Object.fromEntries(d.operationalLayers.map(l => [l.id, l]));
const dp = L.KE1893_days.popupInfo;
dp.title = '{expression/t}';
dp.expressionInfos = [{ name: 'd', returnType: 'string', expression: "Text($feature.day_date, 'D.M.Y')" },
  { name: 't', returnType: 'string', expression: "var d = Text($feature.day_date, 'D.M.Y'); IIf(IsEmpty($feature.heading), 'Tagebuch, ' + d, 'Tagebuch, ' + d + ': ' + $feature.heading)" }];
const ob = L.KE1893_objects;
ob.title = 'Sammlung Este: Kauf oder Geschenk belegt';
ob.layerDefinition.definitionExpression = "strength = 'strong'";
await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
JSON.stringify({ daysTitle: dp.title, objects: ob.title });
