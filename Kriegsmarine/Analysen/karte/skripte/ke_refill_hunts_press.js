// Refill KE1893_hunts (12 -> 18 episodes) and KE1893_press (69 -> 104 ANNO items) in place from
// the team's ke_enrichment.js (khm-team b5e1464), so layer URLs, the web map and filters stay valid.
// Why: our 12/69 came from an older export (export_dated.py ran before enrichment commit 1f2b7cc
// added the bird hunts; press there came from presse_anno.csv, a different pipeline).
// Wording rule from enrichment/README.md: animal counts are MENTIONS in kill sentences (uncorrected
// OCR, keyword rules), not animals killed. Press: relevance high/medium kept and shown.
const SHA = 'b5e146400c47e07539fa1eb62c2dc1d61bb4d197';
const ENR = `https://raw.githubusercontent.com/RichterHenje/Hack-The-Pool-2026/${SHA}/Kriegsmarine/kaiserin_elisabeth/prototype/data/ke_enrichment.js`;
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const SVC = 'https://services5.arcgis.com/Kri0Q7xwN5k6MG7L/arcgis/rest/services/';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include',
  headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }))).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const post = async (u, p = {}) => { const b = new URLSearchParams(); for (const [k, v] of Object.entries(p)) b.append(k, typeof v === 'string' ? v : JSON.stringify(v)); b.append('f', 'json'); b.append('token', tok); const j = await (await fetch(u, { method: 'POST', body: b })).json(); if (j.error) throw new Error(JSON.stringify(j.error)); return j; };
const USER = (await get(REST + '/community/self')).username;
const txt = await (await fetch(ENR)).text();
const KEE = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1));
const toMs = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d, 12); };
// < and > in OCR text trip ArcGIS's XSS filter ("unsafe html content")
const clean = s => String(s || '').replace(/\s+/g, ' ').replace(/</g, '‹').replace(/>/g, '›').trim();
// archive.org page links per volume, derived from the team's day records
const scanBase = {};
for (const d of KEE.days) if (d.page_url && d.band && !scanBase[d.band]) scanBase[d.band] = d.page_url.replace(/\/page\/n\d+.*$/, '');
const scanUrl = (band, scan) => scanBase[band] && scan ? `${scanBase[band]}/page/n${scan - 1}/mode/1up` : null;

async function refill(name, newFields, rows) {
  const url = SVC + name + '/FeatureServer/0', admin = (SVC + name + '/FeatureServer').replace('/rest/services/', '/rest/admin/services/');
  const have = (await get(url)).fields.map(f => f.name);
  const add = newFields.filter(f => !have.includes(f.name));
  if (add.length) await post(admin + '/0/addToDefinition', { addToDefinition: { fields: add } });
  await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Create,Delete,Query,Update,Editing' } });
  try {
    await post(url + '/deleteFeatures', { where: '1=1' });
    const res = await post(url + '/addFeatures', { rollbackOnFailure: true, features: rows });
    if (res.addResults.some(r => !r.success)) throw new Error(name + ': addFeatures failed');
  } finally { await post(admin + '/updateDefinition', { updateDefinition: { capabilities: 'Query' } }); }
  const times = rows.map(r => r.attributes[name === 'KE1893_press' ? 'date_published' : 'date_from']).concat(name === 'KE1893_hunts' ? rows.map(r => r.attributes.date_to) : []);
  const ti = (await get(url)).timeInfo;
  await post(admin + '/0/updateDefinition', { updateDefinition: { timeInfo: { ...ti, timeExtent: [Math.min(...times), Math.max(...times)] } } });
  return (await get(url + '/query', { where: '1=1', returnCountOnly: true })).count;
}
const S = (name, length) => ({ name, type: 'esriFieldTypeString', alias: name, length, nullable: true, editable: true });
const I = name => ({ name, type: 'esriFieldTypeInteger', alias: name, nullable: true, editable: true });

// hunts
const hunts = KEE.episodes.map(e => {
  const pl = e.places[0], q = (e.quotes || [])[0] || {};
  const animals = (e.animals || []).map(a => `${a.label_de} ${a.mentions}`).join(' · ');
  return { geometry: { x: pl.lon, y: pl.lat, spatialReference: { wkid: 4326 } }, attributes: {
    id: e.id, title: e.label, date_from: toMs(e.start), date_to: toMs(e.end), animals,
    kill_sentences: e.kill_sentences, description: animals,
    quote: clean(q.text).slice(0, 900), quote_date: q.date ? toMs(q.date) : null, quote_url: scanUrl(q.band, q.scan),
    anno_issues: e.anno ? e.anno.issues_found : null, anno_high: e.anno ? e.anno.issues_high : null,
    kp_count: (e.kulturpool || []).length, coord_note: pl.coord_note || null } };
});
const huntCount = await refill('KE1893_hunts', [S('quote', 2048), { name: 'quote_date', type: 'esriFieldTypeDate', alias: 'quote_date', nullable: true, editable: true },
  S('quote_url', 256), I('anno_issues'), I('anno_high'), I('kp_count'), S('coord_note', 256)], hunts);

// press
const ep = Object.fromEntries(KEE.episodes.map(e => [e.id, e]));
const press = KEE.press.filter(p => ep[p.episode]).map(p => {
  const e = ep[p.episode], pl = e.places[0];
  const snip = (p.snippets || []).map(s => typeof s === 'string' ? s : (s.text || '')).filter(Boolean)[0] || '';
  return { geometry: { x: pl.lon, y: pl.lat, spatialReference: { wkid: 4326 } }, attributes: {
    title: `${p.newspaper}, ${p.date}`, date_published: toMs(p.date), event_date: toMs(e.start), newspaper: p.newspaper,
    place: e.label, pub_place: p.place, episode: p.episode, relevance: p.relevance, quote: clean(snip).slice(0, 1000),
    page_url: String(p.url || '').replace(/\?query=[^&]*&?/, '?'), status: 'automatisch ausgewählt, ungeprüft (OCR)' } };
});
const pressCount = await refill('KE1893_press', [S('pub_place', 64)], press);

// web map: pop-ups and symbols
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const L = Object.fromEntries(d.operationalLayers.map(l => [l.id, l]));
const hu = L.KE1893_hunts;
const ks = hunts.map(h => h.attributes.kill_sentences);
const vv = hu.layerDefinition.drawingInfo.renderer.visualVariables[0];
vv.minDataValue = Math.min(...ks); vv.maxDataValue = Math.max(...ks);
vv.legendOptions = { title: 'Abschuss-Sätze im Tagebuch (automatisch gezählt)' };
const hf = (await get(SVC + 'KE1893_hunts/FeatureServer/0')).fields.filter(f => f.type !== 'esriFieldTypeOID').map(f => f.name);
hu.popupInfo.fieldInfos = hf.map(n => ({ fieldName: n, label: n, visible: false, isEditable: false }));
hu.popupInfo.expressionInfos = [
  { name: 'from', returnType: 'string', expression: "Text($feature.date_from, 'D.M.Y')" },
  { name: 'to', returnType: 'string', expression: "Text($feature.date_to, 'D.M.Y')" },
  { name: 'qd', returnType: 'string', expression: "IIf(IsEmpty($feature.quote_date), '', Text($feature.quote_date, 'D.M.Y'))" },
  { name: 'note', returnType: 'string', expression: "IIf(IsEmpty($feature.coord_note), '', ' Ort ungefähr: ' + $feature.coord_note + '.')" }];
hu.popupInfo.popupElements = [{ type: 'text', text:
  'Jagd laut Tagebuch, {expression/from} – {expression/to}.<br>' +
  '<b>Tiere in Abschuss-Sätzen</b> (Erwähnungen, nicht Zahl der getöteten Tiere): {animals}<br>' +
  '„{quote}“ (<a href="{quote_url}" target="_blank">Scan, {expression/qd}</a>)<br>' +
  'Presse (ANNO): {anno_issues} Ausgaben gefunden, davon {anno_high} mit hoher Relevanz. Kulturpool: {kp_count} Datensätze im Kontext.<br>' +
  '<span style="font-size:smaller">Automatisch aus dem OCR-Text ermittelt ({kill_sentences} Sätze mit Tötungsverb und Tiername), nicht an den Scans geprüft.{expression/note}</span>' }];
const pr = L.KE1893_press;
const pf = (await get(SVC + 'KE1893_press/FeatureServer/0')).fields.filter(f => f.type !== 'esriFieldTypeOID').map(f => f.name);
pr.popupInfo.fieldInfos = pf.map(n => ({ fieldName: n, label: n, visible: false, isEditable: false }));
pr.popupInfo.popupElements = [{ type: 'text', text:
  '„{quote}“<br>Zur Jagd: {place} (ab {expression/ev}); erschienen {expression/lag} Tage nach Jagdbeginn, in {pub_place}. Relevanz: {relevance}.<br>' +
  '<a href="{page_url}" target="_blank">Seite in ANNO (Österreichische Nationalbibliothek)</a><br>' +
  '<span style="font-size:smaller"><i>{status}</i>: Text per OCR, automatisch der Jagd zugeordnet.</span>' }];
pr.layerDefinition.drawingInfo.renderer = { type: 'uniqueValue', field1: 'relevance',
  defaultSymbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [0, 0, 0, 0], size: 16, outline: { color: [50, 50, 50, 230], width: 1.25 } },
  uniqueValueInfos: [
    { value: 'high', label: 'Zeitungsbericht, hohe Relevanz (am Erscheinungstag)', symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [0, 0, 0, 0], size: 16, outline: { color: [50, 50, 50, 230], width: 1.5 } } },
    { value: 'medium', label: 'Zeitungsbericht, mittlere Relevanz', symbol: { type: 'esriSMS', style: 'esriSMSCircle', color: [0, 0, 0, 0], size: 20, outline: { color: [90, 90, 90, 150], width: 1 } } }] };
await post(`${REST}/content/users/${USER}/items/${WEBMAP}/update`, { text: d });
JSON.stringify({ hunts: [KEE.episodes.length, huntCount], press: [KEE.press.length, press.length, pressCount], huntRange: [Math.min(...ks), Math.max(...ks)], scanBase: Object.keys(scanBase) });
