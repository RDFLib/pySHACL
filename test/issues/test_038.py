# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/38

I think this is duplicate of test test_029.py
"""
from rdflib import Graph
from pyshacl import validate

shapes = Graph()
shapes.parse(data="""
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix ex: <http://example.org/ns#> .

    ex:Person
          a owl:Class ;
          a sh:NodeShape ;
          sh:property ex:NameConstraint ;
    .

    ex:NameConstraint
          a sh:PropertyShape ;
          sh:path ex:name ;
          sh:minCount 1 ;
        .
""",format="ttl")

data = Graph()
data.parse(data="""
    @prefix ex: <http://example.org/ns#> .

    ex:Bob
          a ex:Person ;
    .
""",format="ttl")



def test_038():
    conforms, g, s = validate(data_graph=data, shacl_graph=shapes, inference='rdfs')
    assert not conforms


if __name__ == "__main__":
    test_038()
