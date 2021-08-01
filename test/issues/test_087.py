# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/87
"""
from pyshacl import validate

mixed_file_text = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <urn:ex#> .

:TargetClass a owl:Class .

:Class0 a owl:Class .

:Class1 a owl:Class ;
    rdfs:subClassOf :Class0 .

:Class2 a owl:Class ;
    rdfs:subClassOf :Class1 .

:Class3 a owl:Class ;
    rdfs:subClassOf :Class2 .

:prop  a   owl:ObjectProperty .

:shape a sh:NodeShape ;
    sh:targetClass :TargetClass ;
    sh:property :haspointshape .

:haspointshape a sh:PropertyShape ;
    sh:path :prop ;
    sh:class :Class0 .

:s0 a :Class0 .
:vav0 a :TargetClass ;
    :prop :s0 .

:s1 a :Class1 .
:vav1 a :TargetClass ;
    :prop :s1 .

:s2 a :Class2 .
:vav2 a :TargetClass ;
    :prop :s2 .

:s3 a :Class3 .
:vav3 a :TargetClass ;
    :prop :s3 .
"""

def test_087():
    res1 = validate(mixed_file_text, data_graph_format='turtle', shacl_graph_format='turtle', debug=True)
    conforms, graph, string = res1
    assert conforms

