from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix dash: <http://datashapes.org/dash#> .
@prefix ex: <http://datashapes.org/sh/tests/js/target/jsTarget-001.test#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://datashapes.org/sh/tests/js/target/jsTarget-001.test>
  rdf:type owl:Ontology ;
  rdfs:label "Test of sh:SPARQLTarget 001" ;
  owl:imports <http://datashapes.org/dash> ;
.
ex:GraphValidationTestCase
  rdf:type dash:GraphValidationTestCase ;
  dash:expectedResult [
      rdf:type sh:ValidationReport ;
      sh:conforms "false"^^xsd:boolean ;
      sh:result [
          rdf:type sh:ValidationResult ;
          sh:focusNode ex:InvalidInstance1 ;
          sh:resultPath rdfs:label ;
          sh:resultSeverity sh:Violation ;
          sh:sourceConstraintComponent sh:MaxCountConstraintComponent ;
          sh:sourceShape ex:TestShape-label ;
        ] ;
    ] ;
.

ex:TestShape
  rdf:type sh:NodeShape ;
  rdfs:label "Test shape" ;
  sh:property ex:TestShape-label ;
  sh:target [
      rdf:type sh:JSTarget ;
	  sh:jsFunctionName "findThings" ;
	  sh:jsLibrary [ sh:jsLibraryURL "file://test/resources/js/findThings.js"^^xsd:anyURI ] ;
    ] ;
.

ex:TestShape-label
  sh:path rdfs:label ;
  rdfs:comment "Must not have any rdfs:label" ;
  rdfs:label "label" ;
  sh:datatype xsd:string ;
  sh:maxCount 0 ;
.


'''

data_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://datashapes.org/sh/tests/js/target/jsTarget-001.test#> .
@prefix exdata: <http://datashapes.org/sh/tests/js/target/jsTarget-001.test.data#> .

exdata:InvalidInstance1
  rdf:type owl:Thing ;
  rdfs:label "Invalid instance1" ;
.
exdata:ValidInstance1
  rdf:type owl:Thing ;
.

'''

def test_js_target():
    s1 = Graph().parse(data=shapes_graph, format="turtle")
    g1 = Graph().parse(data=data_graph, format="turtle")
    conforms, result_graph, result_text = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
    assert not conforms

if __name__ == "__main__":
    test_js_target()
