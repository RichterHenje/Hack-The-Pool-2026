// Export the web map and all its hosted layers (read-only) as one JSON bundle, saved by the browser
// as ke_arcgis_export_<date>.json; scripts/arcgis_export_split.py splits it into
// prototype/arcgis/export_<date>/. GeoJSON per service layer (all features, all fields, WGS84),
// the web map JSON and the item texts. The token is only used in requests; the bundle is checked
// for 'token' before it is saved. Run in a page of the org (see README).
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => { const j = await (await fetch(u + '?' + new URLSearchParams({ ...p, f: p.f || 'json', token: tok }), { cache: 'no-store' })).json(); if (j.error) throw new Error(u + ' ' + JSON.stringify(j.error)); return j; };
const ITEM_FIELDS = ['id', 'title', 'type', 'snippet', 'description', 'accessInformation', 'licenseInfo', 'tags', 'access', 'created', 'modified'];
const pick = (o) => Object.fromEntries(ITEM_FIELDS.map(k => [k, o[k]]));
const bundle = { exported_utc: new Date().toISOString(), webmap: { item: pick(await get(`${REST}/content/items/${WEBMAP}`)), data: await get(`${REST}/content/items/${WEBMAP}/data`) }, layers: {} };
const seen = new Set();
for (const l of bundle.webmap.data.operationalLayers) {
  if (seen.has(l.url)) { bundle.layers[l.id] = { same_as: [...seen].indexOf(l.url), url: l.url, definitionExpression: l.layerDefinition?.definitionExpression || null }; continue; }
  seen.add(l.url);
  const meta = await get(l.url);
  const gj = await get(l.url + '/query', { f: 'geojson', where: '1=1', outFields: '*', outSR: 4326, returnGeometry: true, resultRecordCount: 2000 });
  bundle.layers[l.id] = { url: l.url, item: pick(await get(`${REST}/content/items/${l.itemId}`)), definitionExpression: l.layerDefinition?.definitionExpression || null,
    fields: meta.fields.map(f => ({ name: f.name, type: f.type, length: f.length })), timeInfo: meta.timeInfo || null, count: gj.features.length,
    exceededTransferLimit: !!gj.properties?.exceededTransferLimit, geojson: gj };
}
const text = JSON.stringify(bundle);
if (text.includes(tok) || /[?&]token=/.test(text)) throw new Error('token found in bundle; not saved');
const a = document.createElement('a');
a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
a.download = `ke_arcgis_export_${bundle.exported_utc.slice(0, 16).replace(':', '')}.json`;
document.body.appendChild(a); a.click(); a.remove();
JSON.stringify({ bytes: text.length, layers: Object.fromEntries(Object.entries(bundle.layers).map(([k, v]) => [k, v.count ?? ('same as ' + v.same_as)])),
  truncated: Object.entries(bundle.layers).filter(([, v]) => v.exceededTransferLimit).map(([k]) => k) });
