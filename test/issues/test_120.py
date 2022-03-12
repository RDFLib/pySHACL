# -*- coding: utf-8 -*-

"""
https://github.com/RDFLib/pySHACL/issues/120
"""

import rdflib

from pyshacl import validate


shacl_file = r'''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
@prefix : <http://example.org/shape/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://example.org/shape>
  rdf:type owl:Ontology ;
  sh:declare [
      rdf:type sh:PrefixDeclaration ;
      sh:namespace "http://example.org/"^^xsd:anyURI ;
      sh:prefix "ex" ;
    ] ;
.

:exShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [ a sh:PropertyShape;
        sh:path ( ex:i ex:name ) ;
        sh:sparql [
            sh:prefixes <http://example.org/shape> ;
            sh:message "{$this} nome does not match {?name}" ;
            sh:select """
            SELECT $this ?name
            WHERE {
                $this $PATH ?name .
                FILTER NOT EXISTS {
                    $this ex:i/ex:nome ?name .
                }
            }
        """ ] ;
    ] ;
.
'''


data_file = """
@prefix geo: <http://www.opengis.net/ont/geosparql#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <http://example.org/> .

ex:intermediate1 a ex:Intermediate ;
  ex:name "Intermediate1" ;
  ex:nome "Intermediate1" .

ex:intermediate2 a ex:Intermediate ;
  ex:name "Intermediate2" ;
  ex:nome "BadNome" .

ex:goodPerson a ex:Person ;
  ex:i ex:intermediate1 .

ex:badPerson a ex:Person ;
  ex:i ex:intermediate2 .

"""


def test_120() -> None:
    data = rdflib.Graph()
    data.parse(data=data_file, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    res = validate(
        data,
        shacl_graph=shapes,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        debug=True,
    )
    conforms, graph, string = res
    assert False == conforms
    assert "ex:badPerson" in string
    assert "ex:goodPerson" not in string
    assert "nome does not match Intermediate2" in string


if __name__ == "__main__":
    test_120()
