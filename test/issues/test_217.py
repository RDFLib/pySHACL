# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/217
"""
import rdflib
import pyshacl
import sys

shapes_data = '''\
@prefix ex: <http://example.org/ontology/> .
@prefix sh-ex: <http://example.org/shapes/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

sh-ex:ClassC-shape
    a sh:NodeShape ;
    sh:not
        [
            a sh:NodeShape ;
            sh:class ex:ClassA ;
        ] ,
        [
            a sh:NodeShape ;
            sh:class ex:ClassB ;
        ]
        ;
    sh:targetClass ex:ClassC ;
    .
'''

data_g_text = '''\
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

kb:Thing-1
    a
        ex:ClassA ,
        ex:ClassB
        ;
    rdfs:comment "This individual is consistent per OWL and should validate with SHACL."@en ;
    .

kb:Thing-2
    a
        ex:ClassA ,
        ex:ClassC
        ;
    rdfs:comment "This individual is inconsistent per OWL and should not validate with SHACL."@en ;
    .

kb:Thing-3
    a
        ex:ClassB ,
        ex:ClassC
        ;
    rdfs:comment "This individual is inconsistent per OWL and should not validate with SHACL."@en ;
    .
'''


def test_217():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g, shacl_graph=shape_g, debug=True, meta_shacl=False,
    )
    assert not conforms
    assert "Node kb:Thing-2 conforms to shape" in results_text and "Node kb:Thing-3 conforms to shape" in results_text


if __name__ == "__main__":
    sys.exit(test_217())
