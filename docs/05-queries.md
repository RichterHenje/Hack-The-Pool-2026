# 05 · Queries

Sammelstelle für alles Abfragbare: SPARQL, API-Calls, Filterausdrücke, Tricks.

![Swordfish](gifs/swordfish-hack.gif)

## SPARQL

Endpunkt `https://sparql.kulturpool.at/query`, User Interface unter [sparql.kulturpool.at](https://sparql.kulturpool.at/).

> [!TIP]
> Eine annotierte, interaktive Version der folgenden Queries gibt es auf [✨ SPARQL in the Dark ✨](https://acdh-oeaw.github.io/sparql-in-the-dark-kulturpool/).

### Nützliche Präfixe

```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX edm:  <http://www.europeana.eu/schemas/edm/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX gnd: <https://d-nb.info/gnd/>
PREFIX ore: <http://www.openarchives.org/ore/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX id:  <https://id.kulturpool.at/>
```

### Graph-Struktur

Die Datenbank beinhaltet alle Kulturpool-Objekte im EDM-Schema. EDM Aggregations sind als `rdf:type` `ore:Aggregation` gespeichert. Der CHO ist mit der Aggregation über das Prädikat `edm:aggregatedCHO` verknüpft und vom (RDF-)Typ `edm:ProvidedCHO`.

#### Datensets als Sub-Graphen

Einzelne Datensets (`edm:dataProvider`) sind als Sub-Graphen nach dem Schema `https://id.kulturpool.at/dataset/[EDM_DATAPROVIDER]#graph` verfügbar. Einzelne EDM-Records sind als Sub-Graphen nach dem Schema `https://id.kulturpool.at/[UUID]/aggregation#graph` abgelegt.

### Vollständige Abfragen

#### Attribute von Aggregations

```sparql
PREFIX edm:  <http://www.europeana.eu/schemas/edm/>
PREFIX ore: <http://www.openarchives.org/ore/terms/>

SELECT * WHERE {
  ?aggregation a ore:Aggregation .
  ?aggregation ?pAggregation ?oAggregation .
}
LIMIT 100
```

#### Attribute von CHOs

```sparql
PREFIX edm:  <http://www.europeana.eu/schemas/edm/>
PREFIX ore: <http://www.openarchives.org/ore/terms/>

SELECT * WHERE {
  ?cho a edm:ProvidedCHO .
  ?cho ?pCHO ?oCHO .
}
LIMIT 100
```

### Anzahl der CHOs, die denselben dc:creator haben

```sparql
PREFIX edm: <http://www.europeana.eu/schemas/edm/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?dcCreator (COUNT(?cho) AS ?count) WHERE {
  ?cho a edm:ProvidedCHO .
  ?cho dc:creator ?dcCreator .
}

GROUP BY ?dcCreator
ORDER BY DESC(?count)

LIMIT 100
```

### Abfrage auf Datensets eingrenzen

```sparql
SELECT * WHERE {
  GRAPH <https://id.kulturpool.at/dataset/oenb-abo#graph> {
    ?s ?p ?o .
  }
}

LIMIT 100
```


#### Verbinde GND-Referenzen im Kulturpool mit Wikidata

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX edm:  <http://www.europeana.eu/schemas/edm/>
PREFIX ore: <http://www.openarchives.org/ore/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?cho ?title ?gndCreator ?wikidataObject ?wikidataSubjectLabel ?wikidataEntityLabel ?wikidataObjectLabel WHERE {
  {
    SELECT ?cho ?title ?gndCreator WHERE {
      ?cho dc:creator ?gndCreator .
      ?cho dc:title ?title .
      ?aggregation edm:aggregatedCHO ?cho .
      ?cho a edm:ProvidedCHO .
      ?cho dcterms:created ?created .
  	  
      FILTER(ISIRI(?gndCreator)) .
  	  FILTER(STRSTARTS(str(?gndCreator), "https://d-nb.info/gnd/")) .
      FILTER(xsd:integer(SUBSTR(STR(?created), 1, 4)) >= 1920) .
    }
    GROUP BY ?cho ?title ?gndCreator
    OFFSET 123
    LIMIT 10
  }
  .
  {
  	SERVICE <https://query.wikidata.org/sparql> {
      ?wikidataSubject <http://www.wikidata.org/prop/direct-normalized/P227> ?gndCreator .
      ?wikidataSubject ?wikidataPredicate ?wikidataObject .
      { ?wikidataEntity wikibase:directClaim ?wikidataPredicate } UNION { ?wikidataEntity wikibase:claim ?wikidataPredicate }
      FILTER(strstarts(str(?wikidataObject), "http://www.wikidata.org/entity/Q"))
      
      # Wikidata Label Service
	  SERVICE wikibase:label { bd:serviceParam wikibase:language "de" . }
      OPTIONAL { ?wikidataSubjectLabel a <urn:something> } # Hack to bind label to outer scope
      OPTIONAL { ?wikidataEntityLabel a <urn:something> } # Hack to bind label to outer scope
      OPTIONAL { ?wikidataObjectLabel a <urn:something> } # Hack to bind label to outer scope
  	}
  }
}
LIMIT 50
```

### Good to know

#### Langsame Abfrage "DISTINCT GRAPH"

Eine Abfrage nach Graph-Zugehörigkeit und dem `DISTINCT` Modifier ist sehr langsam (Service Timeout):

```sparql
SELECT DISTINCT ?g WHERE {
  GRAPH ?g {
    ?s ?p ?o .
  }
} LIMIT 10
```

Einschränkung auf z.B. Prädikate (wo möglich) hilft:

```sparql
PREFIX edm:  <http://www.europeana.eu/schemas/edm/>

SELECT DISTINCT ?g WHERE {
  GRAPH ?g {
    ?s edm:aggregatedCHO ?o .
  }
}
LIMIT 10
```

Derzeit unbekannt, in welchen Abfragen und warum die `DISTINCT` Gruppierung von Graphen diese Rolle spielt.

## REST-API

Basis `https://api.kulturpool.at`, [Referenz](https://api.kulturpool.at/reference/).

### Suche mit Facetten

```bash
curl -G https://api.kulturpool.at/v2/search \
  --data-urlencode "q=Gletscher" \
  --data-urlencode "facet_by=dataProvider" \
  --data-urlencode "per_page=5"
```

### Nach Institution filtern

```bash
curl -G https://api.kulturpool.at/v2/search \
  --data-urlencode "q=Porträt" \
  --data-urlencode "filter_by=dataProvider:=Österreichische Nationalbibliothek"
```

### Ähnliche Objekte

`on=metadata` sucht über Textvektoren, `on=image` über Bildvektoren.

```bash
curl "https://api.kulturpool.at/v2/similar?id=<UUID>&on=image&per_page=10"
```

Die UUID steht im Suchergebnis unter `hits[].document.id`.

## Beitragen

Neue Query? Rein damit — passender Abschnitt, kurze Überschrift, ein bis zwei Sätze was sie tut und wofür sie gut ist, dann der Codeblock. Lauffähig halten, Platzhalter als `<UUID>` markieren.

---

[← Daten & APIs](04-daten.md) · [Übersicht](../README.md) · [Weiter: Beispiele →](06-beispiele.md)
