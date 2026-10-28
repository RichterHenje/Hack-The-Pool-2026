// Write the provenance texts into the layer items and the web map, then read every field back.
// Run in a page of the org with PAYLOAD = the content of scripts/arcgis/ke_metadata_payload.json
// (rendered by scripts/arcgis_provenance.py) and ONLY = null (all) or a list of item ids.
// Changes snippet, description, accessInformation, licenseInfo only; data, sharing and pop-ups
// stay as they are. ArcGIS sanitises item HTML, so the read-back compares text without tags.
// const PAYLOAD = {...}; const ONLY = ['a79a79039fe545559c5fe540a72d4575'];
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const FIELDS = ['snippet', 'description', 'accessInformation', 'licenseInfo'];
const plain = (s) => String(s || '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
const targets = { ...PAYLOAD.items, [WEBMAP]: PAYLOAD.map };
const report = [];
for (const [id, t] of Object.entries(targets)) {
  if (ONLY && !ONLY.includes(id)) continue;
  const item = await (await fetch(`${REST}/content/items/${id}?f=json&token=${tok}`, { cache: 'no-store' })).json();
  const body = new URLSearchParams({ f: 'json', token: tok });
  for (const f of FIELDS) body.set(f, t[f]);
  const res = await (await fetch(`${REST}/content/users/${item.owner}/items/${id}/update`, { method: 'POST', body })).json();
  const back = await (await fetch(`${REST}/content/items/${id}?f=json&token=${tok}&_=${Date.now()}`, { cache: 'no-store' })).json();
  const diff = FIELDS.filter(f => plain(back[f]) !== plain(t[f]));
  report.push({ id, layer: t.layer || 'webmap', ok: !!res.success, error: res.error?.message, access: back.access, mismatched: diff,
    lengths: Object.fromEntries(FIELDS.map(f => [f, String(back[f] || '').length])) });
}
JSON.stringify(report);
