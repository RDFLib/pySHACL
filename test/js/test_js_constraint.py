from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:LanguageExampleShape
	a sh:NodeShape ;
	sh:targetClass ex:Country ;
	sh:js [
		a sh:JSConstraint ;
		sh:message "Values are literals with German language tag." ;
		sh:jsLibrary [ sh:jsLibraryURL "file://resources/js/germanLabel.js" ] ;
		sh:jsFunctionName "validateGermanLabel" ;
	] .
'''

data_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:ValidCountry a ex:Country ;
	ex:germanLabel "Spanien"@de .

ex:InvalidCountry a ex:Country ;
	ex:germanLabel "Spain"@en .
'''

s1 = Graph().parse(data=shapes_graph, format="turtle")
g1 = Graph().parse(data=data_graph, format="turtle")


res = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
