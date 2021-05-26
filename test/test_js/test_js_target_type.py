from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix dash: <http://datashapes.org/dash#> .
@prefix ex: <http://datashapes.org/sh/tests/js/target/jsTargetType-001.test#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://datashapes.org/sh/tests/js/target/jsTargetType-001.test>
  rdf:type owl:Ontology ;
  rdfs:label "Test of sh:JSTargetType 001" ;
  owl:imports <http://datashapes.org/dash> ;
.
ex:GraphValidationTestCase
  rdf:type dash:GraphValidationTestCase ;
  dash:expectedResult [
      rdf:type sh:ValidationReport ;
      sh:conforms "false"^^xsd:boolean ;
      sh:result [
          rdf:type sh:ValidationResult ;
          sh:focusNode ex:Barry ;
          sh:resultSeverity sh:Violation ;
          sh:sourceConstraintComponent sh:ClassConstraintComponent ;
          sh:sourceShape ex:USCitizenShape ;
          sh:value ex:Barry ;
        ] ;
    ] ;
.

ex:Person
  rdf:type owl:Class ;
  rdfs:label "A person" ;
.

ex:Country
  rdf:type owl:Class ;
  rdfs:label "A country" ;
.

ex:USA
  rdf:type ex:Country ;
.

ex:Germany
  rdf:type ex:Country ;
.

ex:bornIn
  rdf:type owl:ObjectProperty ;
.

ex:GermanCitizen
  rdf:type owl:Class ;
.
ex:USCitizen
  rdf:type owl:Class ;
.

ex:PeopleBornInCountryTarget
	a sh:JSTargetType ;
	rdfs:subClassOf sh:Target ;
	sh:labelTemplate "All persons born in {$country}" ;
	sh:parameter [
		sh:path ex:country ;
		sh:description "The country that the focus nodes are 'born' in." ;
		sh:class ex:Country ;
		sh:nodeKind sh:IRI ;
	] ;
	sh:jsFunctionName "findBornIn" ;
	sh:jsLibrary [ sh:jsLibraryURL "file://test/resources/js/findBornIn.js"^^xsd:anyURI ] ;
.

ex:GermanCitizenShape
	a sh:NodeShape ;
	sh:target [
		a ex:PeopleBornInCountryTarget ;
		ex:country ex:Germany ;
	] ;
	sh:class ex:GermanCitizen ;
.

ex:USCitizenShape
	a sh:NodeShape ;
	sh:target [
		a ex:PeopleBornInCountryTarget ;
		ex:country ex:USA ;
	] ;
	sh:class ex:USCitizen ;
.
'''

data_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://datashapes.org/sh/tests/js/target/jsTargetType-001.test#> .
@prefix exdata: <http://datashapes.org/sh/tests/js/target/jsTargetType-001.test.data#> .

exdata:Ludwig
  rdf:type ex:Person ;
  rdf:type ex:GermanCitizen ;
  ex:bornIn ex:Germany .

exdata:Barry
  rdf:type ex:Person ;
  ex:bornIn ex:USA .

'''

def test_js_target_type():
    s1 = Graph().parse(data=shapes_graph, format="turtle")
    g1 = Graph().parse(data=data_graph, format="turtle")
    conforms, result_graph, result_text = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
    assert not conforms

if __name__ == "__main__":
    test_js_target_type()
