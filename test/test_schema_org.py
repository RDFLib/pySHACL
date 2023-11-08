from pyshacl import validate
import rdflib

SCHEMA_PATH = "http://datashapes.org/schema.ttl"

data = """\
@prefix ex: <http://example.org/> .
@prefix sch: <http://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:asdgjkj a sch:CommunicateAction ;
    sch:about [ a sch:GameServer ;
            sch:playersOnline "42"^^xsd:integer ] .
"""

shacl = """\
# baseURI: http://example.org/myschema
# imports: http://datashapes.org/schema

@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix : <http://example.org/myschema#> .

<http://example.org/myschema>
  a owl:Ontology ;
  rdfs:comment "Dummy Schema importing from Schema.org shape"@en ;
  rdfs:label "Schema.org importer" ;
  owl:imports <http://datashapes.org/schema> .
"""


def schema_org():
    dataGraph = rdflib.Graph().parse(data=data, format='ttl')
    #print(dataGraph.serialize(format='ttl').decode('utf8'))

    shaclDS = rdflib.Dataset()
    shaclGraph = shaclDS.default_context
    shaclDS.graph(shaclGraph)
    shaclGraph.parse(data=shacl, format='ttl')

    report = validate(dataGraph, shacl_graph=shaclDS, abort_on_first=False, inference='both', meta_shacl=False, debug=False, advanced=True, do_owl_imports=True)

    print(report[2])

if __name__ == "__main__":
    schema_org()
