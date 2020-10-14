from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:MaxCountConstraintComponent
	a sh:ConstraintComponent ;
	sh:parameter [
		sh:path ex:maxCount ;
		sh:datatype xsd:integer ;
	] ;
	sh:propertyValidator ex:hasMaxCount .

ex:hasMaxCount
	a sh:JSValidator ;
	sh:message "Path has more than {$maxCount} values." ;
	sh:jsLibrary [ sh:jsLibraryURL "file://test/resources/js/hasMaxCount.js"^^xsd:anyURI ] ;
	sh:jsFunctionName "hasMaxCount" .

ex:TestShape
  rdf:type sh:NodeShape ;
  rdfs:label "Test shape" ;
  sh:property [
    sh:path ex:parent ;
    ex:maxCount 2 ;
  ] ;
  sh:targetNode ex:InvalidResource1 ;
  sh:targetNode ex:ValidResource1 ;
  .

'''

data_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:InvalidResource1 a rdf:Resource ;
  ex:parent ex:Parent1 ;
  ex:parent ex:Parent2 ;
  ex:parent ex:Parent3 .

ex:ValidResource1 a rdf:Resource ;
  ex:parent ex:Parent1 ;
  ex:parent ex:Parent2 .
'''

def test_js_constraint_path_component():
    s1 = Graph().parse(data=shapes_graph, format="turtle")
    g1 = Graph().parse(data=data_graph, format="turtle")
    conforms, result_graph, result_text = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
    assert not conforms

if __name__ == "__main__":
    test_js_constraint_path_component()
