// Per-layer counts for the provenance texts (read-only). Run in a page of the org; copy the
// returned JSON to scripts/arcgis/provenance_counts_<date>.json. Every number in the layer
// descriptions and in docs/21_data_provenance.md comes from that file
// (scripts/arcgis_provenance.py), none is typed by hand.
const ORG = location.origin, REST = ORG + '/sharing/rest', WEBMAP = '977298da4e1a47c380c77a9041e11908';
// field groups counted per layer (value -> count); null values are counted as "null"
const GROUPS = {
  KE1893_stops: ['date_estimated'],
  KE1893_legs: ['on_ship', 'estimated'],
  KE1893_days: ['method_de', 'coords_de', 'coord_basis_de'],
  KE1893_hunts: [],
  KE1893_kills: ['first_person', 'no_hunt_place'],
  KE1893_objects: ['strength'],
  KE1893_press: ['relevance', 'status'],
  KE1893_photos_dated: ['place_tier'],
};
const WHERE = { // extra filtered counts
  KE1893_stops: { dated: 'arrival_date IS NOT NULL', kp_hit: 'kp_hits > 0' },
  KE1893_legs: { dated: 'date_from IS NOT NULL' },
  KE1893_photos_dated: { all_rows: '1=1', dated: 'photo_date IS NOT NULL', licence_cc: "licence LIKE '%CC BY-NC-SA 4.0%'", licence_none: 'licence IS NULL' },
  KE1893_kills: { with_quote: "quote IS NOT NULL AND quote <> ''" },
  KE1893_days: { with_ref: 'coord_ref IS NOT NULL' },
};
const tok = (await (await fetch(REST + '/oauth2/platformSelf?f=json', { method: 'POST', credentials: 'include', headers: { 'X-Esri-Auth-Client-Id': 'arcgisonline', 'X-Esri-Auth-Redirect-Uri': ORG + '/home/accountswitcher-callback.html' } })).json()).token;
const get = async (u, p = {}) => (await fetch(u + '?' + new URLSearchParams({ ...p, f: 'json', token: tok }), { cache: 'no-store' })).json();
const d = await get(`${REST}/content/items/${WEBMAP}/data`);
const out = { webmap: WEBMAP, run_utc: new Date().toISOString(), layers: {} };
for (const l of d.operationalLayers) {
  const cnt = async (w) => (await get(l.url + '/query', { where: w, returnCountOnly: true })).count;
  const row = { item: l.itemId, total: await cnt('1=1'), definition: l.layerDefinition?.definitionExpression || null };
  row.shown = row.definition ? await cnt(row.definition) : row.total;
  for (const f of GROUPS[l.id] || []) {
    const r = await get(l.url + '/query', { where: '1=1', groupByFieldsForStatistics: f, returnGeometry: false,
      outStatistics: JSON.stringify([{ statisticType: 'count', onStatisticField: 'OBJECTID', outStatisticFieldName: 'n' }]) });
    row['by_' + f] = r.error ? 'ERR ' + r.error.message : Object.fromEntries(r.features.map(x => [String(x.attributes[f]), x.attributes.n]));
  }
  for (const [k, w] of Object.entries(WHERE[l.id] || {})) row[k] = await cnt(w);
  const te = (await get(l.url)).timeInfo?.timeExtent || [];
  row.time = te.map(x => x == null ? null : new Date(x).toISOString().slice(0, 10));
  out.layers[l.id] = row;
}
// distinct Europeana records among the labelled photos
const P = d.operationalLayers.find(l => l.id === 'KE1893_photos_dated').url;
const eu = (await get(P + '/query', { where: 'licence IS NOT NULL', outFields: 'europeana', returnGeometry: false, resultRecordCount: 2000 })).features;
out.layers.KE1893_photos_dated.europeana_distinct = new Set(eu.map(f => f.attributes.europeana)).size;
JSON.stringify(out);
