# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/199
"""
import rdflib
from rdflib.namespace import SH
import pyshacl


shapes_data = '''\
@prefix ex: <https://example.com#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .


ex:TestConstraintComponent
  a sh:ConstraintComponent ;
  sh:parameter [
    sh:path ex:theValue ;
  ] ;
  sh:validator [
    a sh:SPARQLAskValidator ;
    sh:message "{$this}: {$theValue}" ;
    sh:ask """
      ASK {
        FILTER ($this != $this)  # Always create a validation report for this constraint component
      }""" ;
  ] .

ex:TestClass1
  a owl:Class ;
  a sh:NodeShape ;
  ex:theValue "Literal" .
ex:TestClass2
  a owl:Class ;
  a sh:NodeShape ;
  ex:theValue ex:SomeURI .
ex:TestClass3
  a owl:Class ;
  a sh:NodeShape ;
  ex:theValue _:bnode .
'''


def test_199():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data="""
    @prefix ex: <https://example.com#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:A a ex:TestClass1 .
    ex:B a ex:TestClass2 .
    ex:C a ex:TestClass3 .
    """, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_g, shacl_graph=shape_g, debug=True,
    )
    assert not conforms
    assert len(list(results_graph[:SH.result])) == 3


if __name__ == "__main__":
    exit(test_199())
