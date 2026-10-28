// v7 patch (owner request 28.10.): hide 21 photos whose museum geography contradicts the place
// they get from the route (docs/15_map_qm.md, manual check 1). Map-level filter only
// (layerDefinition.definitionExpression); the hosted layer keeps all 87.
// Why they conflict: mostly the placement rule, not the museum: date ranges are placed on the
// first day (Bombay 20.–23.1. → Tandur photos at Bombay); travel days go to the destination
// (Pacific 29.8. "Ozeanien" → Vancouver; Atlantic 8.–14.10. "Nordamerika" → Le Havre; Fuji
// 13.8. → Kyoto). Tokyo "VR China" 18.8. and Jaipur/Jodhpur 5.3. stay open.
const HIDE = ['VF_14536', 'VF_14537', 'VF_14538', 'VF_14539', 'VF_14622', 'VF_14887', 'VF_14891', 'VF_14892',
  'VF_14893', 'VF_15221', 'VF_15222', 'VF_15223', 'VF_56932', 'VF_56933', 'VF_56934', 'VF_56935', 'VF_56936',
  'VF_56937', 'VF_56938', 'VF_56939', 'VF_56940'];
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const ph = d.operationalLayers.find(l => l.id === 'KE1893_photos');
if (!ph) throw new Error('photos layer missing');
const where = `vf_id NOT IN (${HIDE.map(v => `'${v}'`).join(',')})`;
ph.layerDefinition.definitionExpression = where;
await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
const url = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/KE1893_photos/FeatureServer/0/query';
const shown = (await get(url, { where, returnCountOnly: true })).count;
const back = (await get(`${REST}/content/items/${WEBMAP}/data`)).operationalLayers.find(l => l.id === 'KE1893_photos').layerDefinition.definitionExpression;
JSON.stringify({ hidden: HIDE.length, shown, saved: back === where });
