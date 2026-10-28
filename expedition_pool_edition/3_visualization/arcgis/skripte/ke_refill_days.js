// Refill KE1893_days in place from the team's ke_enrichment.js at a newer commit (28.10.: a4b8b5a,
// 216 days with a point instead of 206, 31 moved, new coord_source = method, basis, link, note).
// Labels follow the team's reise.js so both pages use the same words. Service URL and item id stay,
// so the web map and any app on it keep working. Also: two Livingston photos (GeoNames had put
// Livingston in New Jersey, the team removed it) move to the team's hand-set Livingston, Montana
// point of the diary day 20.9.1893; the Nepal hunt gets the team's new coord_note.
// Run in a page of the org (see README). Old features stay in window.__daysOld for comparison.
const SHA = 'a4b8b5a4eb2a7717502bb8a458729274ce81f097';
const ENR = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/kaiserin_elisabeth/prototype/data/ke_enrichment.js`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const METHOD = { heading: 'eigener Eintrag im Tagebuch', aligned: 'Teil eines mehrtägigen Eintrags, per Abgleich zugeordnet', no_entry: 'kein eigener Eintrag im Tagebuch' };
const COORDS = { camp: 'Lager/Station eines Jagdorts', hunt: 'Jagdort', heading: 'Ortsverzeichnis (Überschrift des Tages)', site: 'Ortsverzeichnis (gleicher Ort an anderem Tag)', wikidata: 'Ort der Route', hand: 'Ortsliste von Hand' };
const BASIS = { wikidata: 'Wikidata', geonames: 'GeoNames', estimated: 'geschätzt', hand: 'von Hand, ungefähr' };
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }), { cache: 'no-store' })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok);
  const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const txt = await (await fetch(ENR)).text();
const KEE = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1));
const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };
const clean = s => s == null ? null : String(s).replace(/\s+/g, ' ').replace(/</g, '‹').replace(/>/g, '›').trim();
const S = (name, length) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true });
const NEW_FIELDS = [S('coord_basis', 32), S('coord_basis_de', 64), S('coord_name', 128), S('coord_ref', 256), S('coord_note', 512)];

// 0. stop before any write if the pop-up line to replace is not where we expect it
const SPAN = /<span style=["']font-size:smaller["']>Tageszuordnung:[\s\S]*?<\/span>/;
const d0 = await get(`${REST}/content/items/${WEBMAP}/data`);
if (!SPAN.test(String(d0.operationalLayers.find(l => l.id === 'KE1893_days').popupInfo.popupElements[0].text))) throw new Error('days pop-up line not found; nothing written');

// 1. diary days
const days = KEE.days.filter(d => d.lat != null && d.lon != null);
const rows = days.map(d => { const s = d.coord_source || {}; return { geometry: { x: d.lon, y: d.lat, spatialReference: { wkid: 4326 } }, attributes: {
  day_date: toMs(d.date), place: clean(d.place), heading: clean(d.heading), method: d.method, method_de: METHOD[d.method] || d.method,
  coords: d.coords, coords_de: COORDS[s.method || d.coords] || d.coords, band: d.band, scan: d.scan, page_url: d.page_url, site_url: d.site_url,
  hunt_day: d.hunt ? 1 : 0, episode: d.episode,
  coord_basis: s.basis || null, coord_basis_de: s.basis ? (BASIS[s.basis] || s.basis) : null, coord_name: clean(s.name), coord_ref: s.ref || null, coord_note: clean(s.note) } }; });
const url = SVC + 'KE1893_days/FeatureServer/0', admin = (SVC + 'KE1893_days/FeatureServer').replace('/rest/services/', '/rest/admin/services/');
window.__daysOld = (await get(url + '/query', { where: '1=1', outFields: '*', returnGeometry: true, outSR: 4326, resultRecordCount: 2000 })).features;
const have = (await get(url)).fields.map(f => f.name);
const add = NEW_FIELDS.filter(f => !have.includes(f.name));
if (add.length) await post(admin + '/0/addToDefinition', { addToDefinition: { fields: add } });
await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Create,Delete,Query,Update,Editing' } });
try {
  await post(url + '/deleteFeatures', { where: '1=1' });
  const res = await post(url + '/addFeatures', { rollbackOnFailure: true, features: rows });
  if (res.addResults.some(r => !r.success)) throw new Error('days: addFeatures failed');
} finally { await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } }); }
const times = rows.map(r => r.attributes.day_date);
const ti = (await get(url)).timeInfo;
await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: { ...ti, timeExtent: [Math.min(...times), Math.max(...times)] } } });

// 2. Livingston photos -> the team's Livingston, Montana point (diary day 20.9.1893, set by hand)
const liv = KEE.days.find(d => d.date === '1893-09-20');
const P = SVC + 'KE1893_photos_all/FeatureServer/0';
const lp = (await get(P + '/query', { where: "museum_geography = 'Livingston'", outFields: 'OBJECTID,vf_id', returnGeometry: false })).features;
const pu = await post(P + '/updateFeatures', { features: lp.map(f => ({ attributes: { OBJECTID: f.attributes.OBJECTID, place_name: 'Livingston, Montana',
  place_src: 'von Hand (Team, Tagebuchtag 20.9.1893)' }, geometry: { x: liv.lon, y: liv.lat, spatialReference: { wkid: 4326 } } })) });

// 3. Nepal hunt: the team's new coord_note
const nep = KEE.episodes.find(e => e.id === 'hunt-1893-03-09-nepal');
const H = SVC + 'KE1893_hunts/FeatureServer/0';
const hf = (await get(H + '/query', { where: "coord_note LIKE '%Kanchanpur%'", outFields: 'OBJECTID', returnGeometry: false })).features;
const hu = await post(H + '/updateFeatures', { features: hf.map(f => ({ attributes: { OBJECTID: f.attributes.OBJECTID, coord_note: clean(nep.places[0].coord_note) } })) });

// 4. web map pop-up of the days: coordinate origin with link; the footer element stays
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const L = d.operationalLayers.find(l => l.id === 'KE1893_days'), p = L.popupInfo;
for (const f of NEW_FIELDS) if (!p.fieldInfos.some(x => x.fieldName === f.name)) p.fieldInfos.push({ fieldName: f.name, label: f.name, visible: false, isEditable: false });
p.expressionInfos = (p.expressionInfos || []).filter(e => !['cname', 'reflabel', 'cnote'].includes(e.name)).concat([
  { name: 'cname', returnType: 'string', expression: "IIf(IsEmpty($feature.coord_name), '', ' „' + $feature.coord_name + '“')" },
  { name: 'reflabel', returnType: 'string', expression: "IIf(IsEmpty($feature.coord_ref), '', 'Beleg')" },
  { name: 'cnote', returnType: 'string', expression: "IIf(IsEmpty($feature.coord_note), '', ' — ' + $feature.coord_note)" }]);
const el = p.popupElements.find(e => e.type === 'text' && String(e.text).includes('Tageszuordnung'));
el.text = el.text.replace(SPAN,
  '<span style="font-size:smaller">Tageszuordnung: {method_de}. Koordinate: {coords_de}{expression/cname} · {coord_basis_de} ' +
  '<a href="{coord_ref}" target="_blank">{expression/reflabel}</a>{expression/cnote}.</span>');
await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });

const count = (await get(url + '/query', { where: '1=1', returnCountOnly: true })).count;
JSON.stringify({ sent: rows.length, count, old: window.__daysOld.length, livingston: [lp.length, pu.updateResults?.every(r => r.success), liv.lat, liv.lon],
  nepal: [hf.length, hu.updateResults?.every(r => r.success)], popupHasOrigin: el.text.includes('coord_basis_de') });
