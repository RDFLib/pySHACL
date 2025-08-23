# This example uses PySHACL's SHACL Rules executor to add triples to a
# given data graph. The rules, contained below in both TripleRule and
# SPARQLRule form calculate grandparents and great-grandparents, based on
# chains of hasParent predicates.
#
# This demo uses the graph parsing and graph difference functions from
# RDFLib, as well as PySHACL's rules executor which implements the
# SHACL Rules of the SHACL Advanced Features specification, see
# https://www.w3.org/TR/shacl-af/#rules

from rdflib import Graph
from pyshacl import shacl_rules

data_graph = Graph().parse(
    data="""
        PREFIX ex: <http://example.com/>

        ex:a
            a ex:Person ;
            ex:hasParent ex:b ;
        .

        ex:b
            a ex:Person ;
            ex:hasParent ex:c ;
        .

        ex:c
            a ex:Person ;
            ex:hasParent ex:d ;
        .
        """,
    format="turtle",
)

shacl_graph_triple_rule = Graph().parse(
    data="""
        PREFIX ex: <http://example.com/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX sh: <http://www.w3.org/ns/shacl#>

        ex:CalcGrandparent
            a sh:NodeShape ;
            sh:targetClass ex:Person ;
            sh:rule [
                a sh:TripleRule ;
                sh:subject sh:this ;
                sh:predicate ex:hasGrandparent ;
                sh:object [ sh:path ( ex:hasParent ex:hasParent ) ] ;
            ] ;
        .

        ex:CalcGreatGrandparent
            a sh:NodeShape ;
            sh:targetClass ex:Person ;
            sh:rule [
                a sh:TripleRule ;
                sh:subject sh:this ;
                sh:predicate ex:hasGreatGrandparent ;
                sh:object [ sh:path ( ex:hasParent ex:hasParent ex:hasParent ) ] ;
            ] ;
        .
        """,
    format="turtle",
)

shacl_graph_sparql_rule = Graph().parse(
    data='''
        PREFIX ex: <http://example.com/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX sh: <http://www.w3.org/ns/shacl#>

        ex:CalcGrandparent
            a sh:SPARQLRule ;
            sh:targetClass ex:Person ;
            sh:rule [
                a sh:SPARQLRule ;
                sh:construct """
                    CONSTRUCT {
                        $this ex:hasGrandparent ?grandparent .
                    }
                    WHERE {
                        $this ex:hasParent/ex:hasParent ?grandparent .
                    }
                    """ ;
            ] ;
        .

        ex:CalcGreatGrandparent
            a sh:SPARQLRule ;
            sh:targetClass ex:Person ;
            sh:rule [
                a sh:SPARQLRule ;
                sh:construct """
                    CONSTRUCT {
                        $this ex:hasGreatGrandparent ?greatgrandparent .
                    }
                    WHERE {
                        $this ex:hasParent/ex:hasParent/ex:hasParent ?greatgrandparent .
                    }
                    """ ;
            ] ;
        .
        ''',
    format="turtle",
)

expected_output = """
PREFIX ex: <http://example.com/>

ex:a
    ex:hasGrandparent ex:c ;
    ex:hasGreatGrandparent ex:d ;
.

ex:b
    ex:hasGrandparent ex:d ;
.
"""

# run the TripleRule rules
output_graph = shacl_rules(data_graph, shacl_graph=shacl_graph_triple_rule, advanced=True)

# remove the original data in data_graph from output_graph to see new triples only
new_triples = output_graph - data_graph
new_triples.bind("ex", "http://example.com/")
print(new_triples.serialize(format="longturtle"))
# should print as per expected_output


# run the SPARQLRule rules
output_graph2 = shacl_rules(data_graph, shacl_graph=shacl_graph_sparql_rule, advanced=True)

# remove the original data in data_graph from output_graph to see new triples only
new_triples = output_graph2 - data_graph
new_triples.bind("ex", "http://example.com/")
print(new_triples.serialize(format="longturtle"))
# should also print as per expected_output
