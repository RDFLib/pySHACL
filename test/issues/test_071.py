# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/71
"""
import rdflib

from pyshacl import validate


shacl_file_text = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix geo: <http://example.org/geo/> .
@prefix ex: <http://example.com#> .
@prefix : <http://example.com/issue/071#> .


<http://example.com/issue/071>
  rdf:type owl:Ontology .

:PlaceShape
    a sh:NodeShape ;
    sh:targetClass ex:Place ;
    sh:property [
        sh:path geo:asWKT ;
        sh:nodeKind sh:Literal ;
        sh:datatype rdfs:Literal ;
    ] ;
    sh:property [
        sh:path geo:asWKT ;
        sh:nodeKind sh:Literal ;
        sh:datatype rdfs:Datatype ;
    ] ;
    sh:property [
        sh:path geo:asWKT ;
        sh:nodeKind sh:Literal ;
        sh:datatype geo:wktLiteral ;
    ] ;
.
"""

data_file_text = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix geo: <http://example.org/geo/> .
@prefix ex: <http://example.com#> .

geo:hasSerialization
    a rdfs:Property ;
    a owl:DatatypeProperty ;
    rdfs:domain geo:Geometry ;
    rdfs:range rdfs:Literal ;
.

geo:asWKT
    a rdfs:Property ;
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf geo:hasSerialization ;
    rdfs:domain geo:Geometry ;
    rdfs:range geo:wktLiteral ;
.

geo:wktLiteral
    a rdfs:Datatype ;
    dc:description "A Well-known Text serialization of a geometry object." ;
.

ex:Place
    a rdfs:Class ;
    rdfs:subClassOf geo:Geometry ;
.


ex:test1
    a ex:Place ;
    geo:asWKT "POINT(45.75 4.85)"^^geo:wktLiteral ;
    dc:title "test1" ;
.

"""


def test_071_positive():
    data = rdflib.Graph()
    data.parse(data=data_file_text, format="turtle")
    res = validate(
        data,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        inference='rdfs',
        debug=True,
    )
    conforms, graph, string = res
    assert conforms


if __name__ == "__main__":
    test_071_positive()
