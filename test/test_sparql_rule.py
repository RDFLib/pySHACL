"""\
A test which checks that SPARQLRule's generate triples in the default graph of a datasets, even if these triples are
already present in a different graph of that dataset.
"""

from pyshacl import validate
from rdflib import Graph, Dataset, RDFS, URIRef, Literal

shacl_file = '''\
# prefix: ex

@prefix ex: <http://datashapes.org/shasf/tests/expression/sparql-rule.test.shacl#> .
@prefix exOnt: <http://datashapes.org/shasf/tests/expression/sparql-rule.test.ont#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

<http://datashapes.org/shasf/tests/expression/sparql-rule.test.shacl>
  a owl:Ontology ;
  rdfs:label "Test of SPARQLRule in conjunction with datasets" ;
.

ex:rule a sh:SPARQLRule ;
  sh:construct """
    CONSTRUCT {
      $this rdfs:label ?label .
    }
    WHERE {
      $this exOnt:firstName ?firstName .
      $this exOnt:lastName ?lastName .
      BIND(CONCAT(?firstName, " ", ?lastName) AS ?label)
    }
  """ ;
.

ex:PersonExpressionShape
    a sh:NodeShape ;
    sh:targetClass exOnt:Person ;
    sh:rule ex:rule ;
    .
'''

data_graph = '''
# prefix: ex

@prefix ex: <http://datashapes.org/shasf/tests/expression/sparql-rule.test.data#> .
@prefix exOnt: <http://datashapes.org/shasf/tests/expression/sparql-rule.test.ont#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Kate
  a exOnt:Person ;
  rdfs:label "Kate Jones" ;
  exOnt:firstName "Kate" ;
  exOnt:lastName "Jones" ;
.
'''

def test_sparql_rule():
    dataset = Dataset()
    dataset.graph().parse(data=data_graph, format="turtle")
    s = Graph().parse(data=shacl_file, format="turtle")
    validate(dataset, shacl_graph=s, advanced=True, debug=False, inplace=True)
    assert (
        URIRef("http://datashapes.org/shasf/tests/expression/sparql-rule.test.data#Kate"),
        RDFS.label,
        Literal("Kate Jones"),
    ) in dataset.default_context


if __name__ == "__main__":
    exit(test_sparql_rule())
