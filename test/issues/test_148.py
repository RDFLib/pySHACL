# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/148
"""

import rdflib

from pyshacl import validate


shacl_file = """\
@prefix ex: <urn:ex#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Class a owl:Class .
ex:FailedRule a sh:NodeShape ;
    sh:targetClass ex:Class ;
    sh:rule [
        a sh:TripleRule ;
        sh:object ex:Inferred ;
        sh:predicate ex:hasProperty ;
        sh:subject sh:this ;
    ] .
"""
ont_file = """\
@prefix ex: <urn:ex#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Class a owl:Class .
ex:SubClass a owl:Class ;
    rdfs:subClassOf ex:Class .
ex:SubSubClass a owl:Class ;
    rdfs:subClassOf ex:SubClass .

"""

data_file = """\
@prefix ex: <urn:ex#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:A a ex:SubSubClass .
"""


def test_148() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file, format="turtle").parse(data=ont_file)
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    res = validate(data_g, shacl_graph=shapes, advanced=True)
    assert (
        rdflib.URIRef("urn:ex#A"),
        rdflib.URIRef("urn:ex#hasProperty"),
        rdflib.URIRef("urn:ex#Inferred"),
    ) not in data_g

    conforms, graph, string = res
    assert conforms


if __name__ == "__main__":
    test_148()
