from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:MaxLengthConstraintComponent
	a sh:ConstraintComponent ;
	sh:parameter [
		sh:path ex:maxLength ;
		sh:datatype xsd:integer ;
	] ;
	sh:validator ex:hasMaxLength .

ex:hasMaxLength
	a sh:JSValidator ;
	sh:message "Value has more than {$maxLength} characters" ;
	rdfs:comment """
		Note that $value and $maxLength are RDF nodes expressed in JavaScript Objects.
		Their string value is accessed via the .lex and .uri attributes.
		The function returns true if no violation has been found.
		""" ;
	sh:jsLibrary [ sh:jsLibraryURL "file://test/resources/js/hasMaxLength.js"^^xsd:anyURI ] ;
	sh:jsFunctionName "hasMaxLength" .

ex:TestShape
  rdf:type sh:NodeShape ;
  rdfs:label "Test shape" ;
  sh:property [
    sh:path ex:postcode ;
    ex:maxLength 4 ;
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
  ex:postcode "12345" .

ex:ValidResource1 a rdf:Resource ;
  ex:postcode "1234" .
'''

def test_js_constraint_component():
    s1 = Graph().parse(data=shapes_graph, format="turtle")
    g1 = Graph().parse(data=data_graph, format="turtle")
    conforms, result_graph, result_text = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
    assert not conforms

if __name__ == "__main__":
    test_js_constraint_component()
