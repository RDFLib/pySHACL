"""\
A cool test that combines a bunch of SHACL-AF features, including:
SHACL Functions (implemented as SPARQL functions)
SHACL Rules
Node Expressions
Expression Constraint
SPARQL constraints that call SHACL Functions as SPARQL extension functions
"""

from typing import Tuple, Union
from pyshacl import validate
from rdflib import Graph

from pyshacl.graph_abstraction import has_oxigraph

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
  sh:declare [
    sh:prefix "ex" ;
    sh:namespace "http://datashapes.org/shasf/tests/expression/advanced.test.shacl#" ;
  ] ;
  sh:declare [
    sh:prefix "exOnt" ;
    sh:namespace "http://datashapes.org/shasf/tests/expression/advanced.test.ont#" ;
  ] ;
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
        SELECT ?result ?op1 ?op2
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
        SELECT ?result ?op1
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
        SELECT ?result ?op1 ?op2
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

ex:PersonSparqlFunctionShape
    a sh:NodeShape ;
    sh:targetClass exOnt:Person ;
    sh:sparql ex:PersonFullNameLength-sparql .

ex:PersonFullNameLength-sparql
    a sh:SPARQLConstraintObject ;
    sh:prefixes <http://datashapes.org/shasf/tests/expression/advanced.test.shacl> ;
    sh:message "Person full name must be under 35 characters (SPARQL custom function path)." ;
    sh:select """
        SELECT $this
        WHERE {
            $this exOnt:firstName ?firstName .
            $this exOnt:lastName ?lastName .
            FILTER (STRLEN(ex:concat(?firstName, ?lastName)) >= 35)
        }
        """ .

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

ex:Bob
  rdf:type exOnt:Person ;
  exOnt:firstName "Robert" ;
  exOnt:lastName "Bartholomew-Williamson-Jefferson-III" ;
.
'''


def test_advanced():
    d = Graph().parse(data=data_graph, format="turtle")
    s = Graph().parse(data=shacl_file, format="turtle")
    conforms, report, message = validate(d, shacl_graph=s, advanced=True, debug=False)
    print(message)
    assert not conforms

if has_oxigraph:
    def test_advanced_sparql_custom_function():
        """Validate SPARQL constraints that invoke SHACL Functions as SPARQL extension functions.

        Unlike node-expression evaluation (which calls SPARQLFunction.execute() in Python), this
        path registers custom functions and invokes execute_from_sparql / execute_from_sparql_oxigraph
        from inside the SPARQL engine when a constraint query contains calls like ex:concat(...).
        """
        import pyoxigraph as ox
        from pyoxigraph import RdfFormat, NamedNode, BlankNode, Literal

        from pyshacl.functions.shacl_function import SPARQLFunction

        oxigraph_sparql_fn_calls = []
        orig = SPARQLFunction.execute_from_sparql_oxigraph

        def recording_execute_from_sparql_oxigraph(self, g, *args: Tuple[Union[NamedNode, BlankNode, Literal], ...]):
            oxigraph_sparql_fn_calls.append(self.node)
            return orig(self, g, *args)

        SPARQLFunction.execute_from_sparql_oxigraph = recording_execute_from_sparql_oxigraph
        try:
            d = ox.Store()
            d.bulk_load(data_graph, format=RdfFormat.TURTLE)
            s = Graph().parse(data=shacl_file, format="turtle")
            conforms, report, message = validate(d, shacl_graph=s, advanced=True, debug=False)
        finally:
            SPARQLFunction.execute_from_sparql_oxigraph = orig

        assert not conforms
        assert len(oxigraph_sparql_fn_calls) > 0, (
            "Expected ex:concat to be invoked via execute_from_sparql_oxigraph "
            "from the PersonFullNameLength SPARQL constraint"
        )
        concat_uri = "http://datashapes.org/shasf/tests/expression/advanced.test.shacl#concat"
        assert any(str(node) == concat_uri for node in oxigraph_sparql_fn_calls)


if __name__ == "__main__":
    exit(test_advanced())
