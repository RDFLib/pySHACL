from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://datashapes.org/js/tests/rules/rectangle.test#> .

ex:RectangleShape
	a sh:NodeShape ;
	sh:targetClass ex:Rectangle ;
	sh:rule [
		a sh:JSRule ;    # This triple is optional
		sh:jsFunctionName "computeArea" ;
		sh:jsLibrary [ sh:jsLibraryURL "file://test/resources/js/rectangle.js"^^xsd:anyURI ] ;
    ] ;
    sh:property [
        sh:path ex:area ;
        sh:datatype xsd:double ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] .
'''

data_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://datashapes.org/js/tests/rules/rectangle.test#> .
@prefix exdata: <http://datashapes.org/js/tests/rules/rectangle.test.data#> .

exdata:ExampleRectangle
	a ex:Rectangle ;
	ex:width 7 ;
	ex:height 8 .
'''

def test_js_rules():
    s1 = Graph().parse(data=shapes_graph, format="turtle")
    g1 = Graph().parse(data=data_graph, format="turtle")
    conforms, result_graph, result_text = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
    assert not conforms

if __name__ == "__main__":
    test_js_rules()
