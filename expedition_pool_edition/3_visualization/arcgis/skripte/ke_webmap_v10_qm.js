// v10 QM fixes (28.10. ~06:00), found by ke_qm_check.js and the null-link check:
// - diary days: 4 have no scan link, 3 no English day page -> link text only when the link exists;
// - kill entries: 10 belong to no team hunt episode -> "keiner Jagd des Teams zugeordnet" instead of "Jagd: .".
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const L = Object.fromEntries(d.operationalLayers.map(l => [l.id, l]));
const dp = L.KE1893_days.popupInfo;
dp.expressionInfos = dp.expressionInfos.filter(e => !['scan', 'site', 'noscan'].includes(e.name)).concat([
  { name: 'scan', returnType: 'string', expression: "IIf(IsEmpty($feature.page_url), '', 'Scan im Tagebuch (Bd. ' + $feature.band + ', Scan ' + $feature.scan + ', archive.org)')" },
  { name: 'site', returnType: 'string', expression: "IIf(IsEmpty($feature.site_url), '', 'englische Tagesseite')" },
  { name: 'noscan', returnType: 'string', expression: "IIf(IsEmpty($feature.page_url), ' (kein Scan-Link)', '')" }]);
dp.popupElements[0].text = 'Ort: {place} · <a href="{page_url}" target="_blank">{expression/scan}</a>{expression/noscan} · <a href="{site_url}" target="_blank">{expression/site}</a><br>' +
  '<span style="font-size:smaller">Tageszuordnung: {method_de}. Koordinate aus: {coords_de}. Quelle: Franz Ferdinand, Tagebuch meiner Reise um die Erde (1895), Datensatz des Teams.</span>';
const kp = L.KE1893_kills.popupInfo;
kp.expressionInfos = kp.expressionInfos.filter(e => e.name !== 'ep').concat([{ name: 'ep', returnType: 'string',
  expression: "IIf(IsEmpty($feature.episode), 'Keiner Jagd des Teams zugeordnet.', 'Jagd: ' + $feature.episode + '.')" }]);
kp.popupElements[0].text = kp.popupElements[0].text.replace('Jagd: {episode}.', '{expression/ep}');
// singular after the screen check ("1 Sätze")
kp.expressionInfos = kp.expressionInfos.filter(e => e.name !== 'ks').concat([{ name: 'ks', returnType: 'string',
  expression: "IIf($feature.kill_sentences == 1, '1 Satz', $feature.kill_sentences + ' Sätze')" }]);
kp.popupElements[0].text = kp.popupElements[0].text.replace('{kill_sentences} Sätze mit', '{expression/ks} mit');
await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
JSON.stringify({ days: dp.popupElements[0].text.includes('expression/scan'), kills: kp.popupElements[0].text.includes('expression/ep') });
