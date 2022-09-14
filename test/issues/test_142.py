# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/142
"""

import rdflib

from pyshacl import validate


shacl_file = """\
@prefix owl:    <http://www.w3.org/2002/07/owl#> .
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:     <http://www.w3.org/ns/shacl#> .
@prefix ex:     <http://example.com/ns#> .

ex:PersonShape
    a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path     ex:hasPet ;
        sh:class    ex:Animal ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
.
"""
ont_file = """\
@prefix owl:    <http://www.w3.org/2002/07/owl#> .
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:     <http://example.com/ns#> .

ex:Person a owl:Class .
ex:Animal a owl:Class .
ex:Dog    a owl:Class ; rdfs:subClassOf ex:Animal .
"""

data_file = """\
@prefix ex: <http://example.com/ns#> .
ex:Brutus a ex:Dog .
ex:Jane a ex:Person ; ex:hasPet ex:Brutus .
"""


def test_142() -> None:
    data = rdflib.Graph()
    data.parse(data=data_file, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    ont = rdflib.Graph()
    ont.parse(data=ont_file, format="turtle")
    res = validate(data, shacl_graph=shapes, ont_graph=ont)

    conforms, graph, string = res
    print(string)


if __name__ == "__main__":
    test_142()
