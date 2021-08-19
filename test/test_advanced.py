"""\
A cool test that combines a bunch of SHACL-AF features, including:
SHACL Functions (implemented as SPARQL functions)
SHACL Rules
Node Expressions
Expression Constraint
"""

from pyshacl import validate
from rdflib import Graph

shacl_file = '''\
# prefix: ex

@prefix ex: <http://datashapes.org/shasf/tests/expression/advanced.test.shacl#> .
@prefix exOnt: <http://datashapes.org/shasf/tests/expression/advanced.test.ont#> .
@prefix exData: <http://datashapes.org/shasf/tests/expression/advanced.test.data#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://datashapes.org/shasf/tests/expression/advanced.test.shacl>
  rdf:type owl:Ontology ;
  rdfs:label "Test of advanced features" ;
.

ex:concat
    a sh:SPARQLFunction ;
    rdfs:comment "Concatenates strings $op1 and $op2." ;
    sh:parameter [
        sh:path ex:op1 ;
        sh:datatype xsd:string ;
        sh:description "The first string" ;
    ] ;
    sh:parameter [
        sh:path ex:op2 ;
        sh:datatype xsd:string ;
        sh:description "The second string" ;
    ] ;
    sh:returnType xsd:string ;
    sh:select """
        SELECT ?result
        WHERE {
          BIND(CONCAT(STR(?op1),STR(?op2)) AS ?result) .
        }
        """ .

ex:strlen
    a sh:SPARQLFunction ;
    rdfs:comment "Returns length of the given string." ;
    sh:parameter [
        sh:path ex:op1 ;
        sh:datatype xsd:string ;
        sh:description "The string" ;
    ] ;
    sh:returnType xsd:integer ;
    sh:select """
        SELECT ?result
        WHERE {
          BIND(STRLEN(?op1) AS ?result) .
        }
        """ .

ex:lessThan
    a sh:SPARQLFunction ;
    rdfs:comment "Returns True if op1 < op2." ;
    sh:parameter [
        sh:path ex:op1 ;
        sh:datatype xsd:integer ;
        sh:description "The first int" ;
    ] ;
    sh:parameter [
        sh:path ex:op2 ;
        sh:datatype xsd:integer ;
        sh:description "The second int" ;
    ] ;
    sh:returnType xsd:boolean ;
    sh:select """
        SELECT ?result
        WHERE {
          BIND(IF(?op1 < ?op2, true, false) AS ?result) .
        }
        """ .

ex:PersonExpressionShape
    a sh:NodeShape ;
    sh:targetClass exOnt:Person ;
    sh:expression [
        sh:message "Person's firstName and lastName together should be less than 35 chars long." ;
        ex:lessThan (
            [ ex:strlen (
                [ ex:concat ( [ sh:path exOnt:firstName] [ sh:path exOnt:lastName ] ) ] )
            ]
            35 );
    ] .

ex:PersonRuleShape
	a sh:NodeShape ;
	sh:targetClass exOnt:Administrator ;
	sh:message "An administrator is a person too." ;
	sh:rule [
		a sh:TripleRule ;
		sh:subject sh:this ;
		sh:predicate rdf:type ;
		sh:object exOnt:Person ;
	] .
'''

data_graph = '''
# prefix: ex

@prefix ex: <http://datashapes.org/shasf/tests/expression/advanced.test.data#> .
@prefix exOnt: <http://datashapes.org/shasf/tests/expression/advanced.test.ont#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Kate
  rdf:type exOnt:Person ;
  exOnt:firstName "Kate" ;
  exOnt:lastName "Jones" ;
.

ex:Jenny
  rdf:type exOnt:Administrator ;
  exOnt:firstName "Jennifer" ;
  exOnt:lastName "Wolfeschlegelsteinhausenbergerdorff" ;
.
'''

def test_advanced():
    d = Graph().parse(data=data_graph, format="turtle")
    s = Graph().parse(data=shacl_file, format="turtle")
    conforms, report, message = validate(d, shacl_graph=s, advanced=True, debug=False)
    print(message)
    assert not conforms

if __name__ == "__main__":
    exit(test_advanced())
