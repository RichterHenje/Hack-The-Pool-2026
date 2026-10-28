// Add (or replace) a source footer as the last text element of every pop-up in the web map.
// FOOTERS = payload.popup_footers from scripts/arcgis/ke_metadata_payload.json; MODE = 'add' | 'remove'.
// A footer is recognised by MARK, so a rerun replaces it and 'remove' takes it out again.
// Writes the web map JSON with updateItem(text=…); a Map Viewer tab left open with unsaved
// changes would overwrite this on its next save.
// const FOOTERS = {...}; const MODE = 'add';
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
const MARK = 'Mehr: Beschreibung der Ebene (Details).';
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const item = await (await fetch(`${REST}/content/items/${WEBMAP}?f=json&token=${tok}`, { cache: 'no-store' })).json();
const d = await (await fetch(`${REST}/content/items/${WEBMAP}/data?f=json&token=${tok}&_=${Date.now()}`, { cache: 'no-store' })).json();
window.__wmBackup = JSON.parse(JSON.stringify(d));
const done = [];
for (const l of d.operationalLayers) {
  const p = l.popupInfo;
  if (!p || !p.popupElements) continue;
  p.popupElements = p.popupElements.filter(e => !(e.type === 'text' && String(e.text || '').includes(MARK)));
  if (MODE === 'add' && FOOTERS[l.id]) { p.popupElements.push({ type: 'text', text: FOOTERS[l.id] }); done.push(l.id); }
}
const body = new URLSearchParams({ f: 'json', token: tok, text: JSON.stringify(d) });
const res = await (await fetch(`${REST}/content/users/${item.owner}/items/${WEBMAP}/update`, { method: 'POST', body })).json();
const back = await (await fetch(`${REST}/content/items/${WEBMAP}/data?f=json&token=${tok}&_=${Date.now()}`, { cache: 'no-store' })).json();
const strip = (x) => { const c = JSON.parse(JSON.stringify(x)); c.operationalLayers.forEach(l => { if (l.popupInfo?.popupElements) l.popupInfo.popupElements = l.popupInfo.popupElements.filter(e => !String(e.text || '').includes(MARK)); }); return JSON.stringify(c); };
JSON.stringify({ ok: !!res.success, error: res.error?.message, mode: MODE, footers: done.length,
  footersBack: back.operationalLayers.filter(l => (l.popupInfo?.popupElements || []).some(e => String(e.text || '').includes(MARK))).length,
  restUnchanged: strip(back) === strip(window.__wmBackup), layers: back.operationalLayers.length, bookmarks: back.bookmarks.length });
