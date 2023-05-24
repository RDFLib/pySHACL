import pyshacl
from rdflib.namespace import SH


test_node_ttl = """\
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .


ex:PersonShape
  a sh:NodeShape ;
  sh:targetClass ex:Person ;
  sh:node ex:Shape1 ;
.

ex:Shape1
  a sh:NodeShape ;
  sh:node ex:Shape2 ;
  sh:property [
    a sh:PropertyShape ;
    sh:path ex:familyName ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
  ] ;
.

ex:Shape2
  a sh:NodeShape ;
  sh:property [
    a sh:PropertyShape ;
    sh:path ex:givenName ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
  ] ;
.

ex:Person1
  a ex:Person ;
.
"""


def test_node_details():
    conforms, graph, text = pyshacl.validate(test_node_ttl, data_graph_format="turtle")
    assert not conforms
    top_results = set(graph.objects(None, SH.result))
    assert len(top_results) == 1
    top_result = top_results.pop()
    details = set(graph.objects(top_result, SH.detail))
    assert len(details) == 2
    for r in details:
        details = set(graph.objects(r, SH.detail))
        if len(details) == 0:
            source_1 = r
        elif len(details) == 1:
            mid_result = r
    assert source_1
    assert mid_result
    assert (source_1, SH.sourceConstraintComponent, SH.MinCountConstraintComponent) in graph
    assert (mid_result, SH.detail / SH.sourceConstraintComponent, SH.MinCountConstraintComponent) in graph
