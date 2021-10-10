# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/96
"""
from pyshacl import validate

mixed_file_text = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <urn:ex#> .

:Class0 a owl:Class .

:Class1 a owl:Class ;
    rdfs:subClassOf :Class0 .

:Class2 a owl:Class ;
    rdfs:subClassOf :Class1 .

:Class3 a owl:Class ;
    rdfs:subClassOf :Class2 .

:prop  a   owl:DatatypeProperty .

:shape a sh:NodeShape ;
    sh:targetClass :Class0 ;
    sh:property [
        sh:path :prop ;
        sh:hasValue "test" ;
        sh:minCount 1 ;
    ] .

:s2 a :Class2 ;
    :prop "fail" .

:s3 a :Class3 ;
    :prop "fail" .
"""

def test_96():
    res1 = validate(mixed_file_text, data_graph_format='turtle', shacl_graph_format='turtle', debug=True)
    conforms, _, _ = res1
    assert not conforms
