# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/9
"""
from pyshacl import validate

shacl_file_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:Parent a rdfs:Class ;
    rdfs:isDefinedBy ex: ;
    rdfs:comment "The parent class"@en ;
    rdfs:subClassOf owl:Thing .

ex:ParentShape a sh:NodeShape ;
    rdfs:isDefinedBy ex: ;
    sh:property [
        sh:datatype xsd:string ;
        sh:path ex:name ;
        sh:maxCount 1 ;
        sh:minCount 1 ;
    ] ;
    sh:closed true ;
    sh:ignoredProperties ( rdf:type ) ;
    sh:targetClass ex:Parent .
"""

data_file_text = """
{
    "@context": {
        "@vocab": "http://example.com/ex#"
    },
    "@type": "Parent",
    "name": "Father",
    "dummy": "Dummy value"
}
"""

def test_009():
    res = validate(data_file_text, shacl_graph=shacl_file_text, data_graph_format='json-ld', shacl_graph_format='turtle', inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms

