# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/213
"""
import rdflib
import pyshacl

shapes_data = '''\
@prefix ex: <http://example.org/ontology/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:MyShape
    a sh:NodeShape ;
    sh:targetClass ex:MyFirstClass ;
    sh:property [
        rdfs:comment "This triggers as expected."@en ;
        sh:path ex:myProperty ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        rdfs:comment "This does should also trigger, even when there are no myProperty values on path."@en ;
        sh:path ex:myProperty ;
        sh:qualifiedValueShape [
            sh:class ex:MySecondClass
        ] ;
        sh:qualifiedMinCount 1 ;
    ]
    .
'''

data_g_text = '''\
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .

kb:MyFirstClass-instance-not-ok
    a ex:MyFirstClass ;
    .

kb:MyFirstClass-instance-ok
    a ex:MyFirstClass ;
    ex:myProperty [
        a ex:MySecondClass ;
    ] ;
    .
'''


def test_213():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g, shacl_graph=shape_g, debug=True, meta_shacl=False,
    )
    assert not conforms
    assert "QualifiedValueShapeConstraintComponent" in results_text


if __name__ == "__main__":
    exit(test_213())
