// Photos: licence, Europeana link and photographer from the team's ke_enrichment.js (khm-team
// b5e1464, photos[].rights/.europeana/.creator), matched to our photo layer by inventory number.
// Checked at the source 28.10.: Europeana record 15504/VF_14687: edmRights CC BY-NC-SA 4.0,
// edmDataProvider Weltmuseum Wien (org 1628), edmProvider = Kulturpool (org 3053), created 2019.
// Photos not in the team's list keep licence = null ("nicht geprüft" in the pop-up).
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const ENR = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/kaiserin_elisabeth/prototype/data/ke_enrichment.js`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const URL0 = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/KE1893_photos/FeatureServer';
const ADMIN = URL0.replace('/rest/services/', '/rest/admin/services/');
const LIC = { 'http://creativecommons.org/licenses/by-nc-sa/4.0/': 'CC BY-NC-SA 4.0', 'http://rightsstatements.org/vocab/InC/1.0/': 'In Copyright (InC)' };
const CREATOR = { 'Deen Dayal': 'Lala Deen Dayal', 'Imhoff': 'Max von Imhof' };
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const txt = await (await fetch(ENR)).text();
const KEE = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1));
const R = {};
for (const p of KEE.photos) {
  const c = p.creator.split(',')[0].replace(' (photographer)', '').trim();
  R[p.vf] = { licence: LIC[p.rights] || p.rights, europeana: p.europeana, creator: CREATOR[c] || c };
}

// 1 fields
const have = (await get(URL0 + '/0')).fields.map(f => f.name);
const add = [['licence', 64], ['europeana', 128], ['creator', 128]].filter(([n]) => !have.includes(n))
  .map(([name, length]) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true }));
if (add.length) await post(ADMIN + '/0/addToDefinition', { addToDefinition: { fields: add } });
await post(ADMIN + '/updateDefinition', { updateDefinition: { capabilities: 'Query,Update,Editing' } });
let res;
try {
  const feats = (await get(URL0 + '/0/query', { where: '1=1', outFields: 'OBJECTID,vf_id', returnGeometry: false })).features;
  const updates = feats.filter(f => R[f.attributes.vf_id]).map(f => ({ attributes: { OBJECTID: f.attributes.OBJECTID, ...R[f.attributes.vf_id] } }));
  res = await post(URL0 + '/0/updateFeatures', { features: updates, rollbackOnFailure: true });
} finally { await post(ADMIN + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } }); }

// 2 pop-up caption
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const ph = d.operationalLayers.find(l => l.id === 'KE1893_photos').popupInfo;
for (const n of ['licence', 'europeana', 'creator'])
  if (!ph.fieldInfos.some(f => f.fieldName === n)) ph.fieldInfos.push({ fieldName: n, label: n, visible: false, isEditable: false });
ph.expressionInfos = (ph.expressionInfos || []).filter(e => !['credit', 'eu'].includes(e.name)).concat([
  { name: 'credit', returnType: 'string', expression:
    "IIf(IsEmpty($feature.licence), 'Weltmuseum Wien; Lizenz nicht geprüft', IIf(IsEmpty($feature.creator), '', $feature.creator + ', ') + 'Weltmuseum Wien, ' + $feature.licence + ' (über Europeana; Aggregator: Kulturpool)')" },
  { name: 'eu', returnType: 'string', expression:
    "IIf(IsEmpty($feature.europeana), '', ' · Europeana: ' + $feature.europeana)" }]);
ph.popupElements[0].mediaInfos[0].caption = 'Foto: {expression/credit}';
ph.popupElements[1].text = ph.popupElements[1].text.replace(' (Bild vom Server des Museums geladen)', '{expression/eu}');
await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
const filled = (await get(URL0 + '/0/query', { where: 'licence IS NOT NULL', returnCountOnly: true })).count;
JSON.stringify({ teamPhotos: KEE.photos.length, updated: res.updateResults.filter(r => r.success).length, failed: res.updateResults.filter(r => !r.success).length, filled });
