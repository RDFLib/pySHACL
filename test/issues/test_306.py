# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/306
Tests double inverse path
"""
import sys
import rdflib
import pyshacl

shapes_data = '''\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix : <https://w3id.org/example#> .

:Shape0 a sh:NodeShape ;
  sh:targetNode :a0 ;
  sh:property [
    sh:path [ sh:inversePath [ sh:inversePath :r0 ] ] ;
    sh:minCount 1
  ] .
'''

data_g_text = '''\
@prefix : <https://w3id.org/example#> .

:a0 :r0 :a1 .
'''


def test_306():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shape_g,
        debug=True,
        inference='none',
        advanced=False,
        meta_shacl=False,
    )
    assert conforms

if __name__ == "__main__":
    sys.exit(test_306())
