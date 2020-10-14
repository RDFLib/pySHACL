from rdflib import Graph
from pyshacl import validate
shapes_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:Rectangle
  rdf:type rdfs:Class ;
  rdf:type sh:NodeShape ;
  rdfs:label "Rectangle" ;
  rdfs:subClassOf rdfs:Resource ;
  sh:property [
      sh:path ex:height ;
      sh:datatype xsd:integer ;
      sh:maxCount 1 ;
      sh:minCount 1 ;
      sh:name "height" ;
    ] ;
  sh:property [
      sh:path ex:width ;
      sh:datatype xsd:integer ;
      sh:maxCount 1 ;
      sh:minCount 1 ;
      sh:name "width" ;
    ] ;
  sh:property [
      sh:path ex:area ;
      sh:datatype xsd:integer ;
      sh:maxCount 1 ;
      sh:minCount 1 ;
      sh:name "area" ;
    ] ;
.

ex:CheckArea
  rdf:type sh:PropertyShape ;
  sh:path ex:area ;
  sh:sparql ex:CheckArea-sparql ;
  sh:targetClass ex:Rectangle ;
.
ex:CheckArea-sparql
  rdf:type sh:SPARQLConstraintObject ;
  sh:message "Height * Width = Area." ;
  sh:prefixes <http://example.com/ex> ;
  sh:select """
		SELECT $this ?value
		WHERE {
		    $this ex:width ?width .
		    $this ex:height ?height .
			$this $PATH ?value .
			FILTER (ex:multiply(?width, ?height) != ?value)
		}
		""" ;
.
ex:multiply
  a sh:JSFunction ;
  rdfs:comment "Multiplies its two arguments $op1 and $op2." ;
  sh:parameter [
    sh:path ex:op1 ;
    sh:datatype xsd:integer ;
    sh:description "The first operand" ;
  ] ;
  sh:parameter [
    sh:path ex:op2 ;
    sh:datatype xsd:integer ;
    sh:description "The second operand" ;
  ] ;
  sh:returnType xsd:integer ;
  sh:jsLibrary [ sh:jsLibraryURL "file://test/resources/js/multiply.js" ] ;
  sh:jsFunctionName "multiply" ;
.
'''

data_graph = '''\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .
@prefix exdata: <http://example.com/exdata#> .

exdata:NonSquareRectangle
  rdf:type ex:Rectangle ;
  ex:height 3 ;
  ex:width 4 ;
  ex:area 12 ;
.
exdata:SquareRectangle
  rdf:type ex:Rectangle ;
  ex:height 6 ;
  ex:width 6 ;
  ex:area 12 ;
.

'''

def test_js_function():
    s1 = Graph().parse(data=shapes_graph, format="turtle")
    g1 = Graph().parse(data=data_graph, format="turtle")
    conforms, result_graph, result_text = validate(g1, shacl_graph=s1, advanced=True, debug=True, js=True)
    assert not conforms

if __name__ == "__main__":
    test_js_function()
