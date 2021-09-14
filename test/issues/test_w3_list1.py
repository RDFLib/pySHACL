# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/79
"""
import rdflib
import pyshacl
shapes_data = """\
@prefix ex: <https://example.com#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:ParentTypeRestriction
  a sh:NodeShape ;
  sh:targetClass ex:Cls1 ;
  sh:property [
    sh:path ex:parent ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
    sh:property [
      sh:path ( rdf:type [ sh:zeroOrMorePath rdfs:subClassOf ] ) ;
      sh:minCount 1 ;
      sh:qualifiedMinCount 1 ;
      sh:qualifiedMaxCount 1 ;
      sh:qualifiedValueShape [
        sh:or (
          [ sh:hasValue ex:P_cls1 ]
          [ sh:hasValue ex:P_cls2 ]
          [ sh:hasValue ex:P_cls3 ]
        )
      ] ;
      sh:not [ sh:in ( ex:P_clsInvalid_a ex:P_clsInvalid_b ) ] ;
    ] ;
    sh:message "parent type for ex:Cls1 is not in x:P_cls{1, 2, 3}" ;
  ] ;
.
"""
# rdf:type/rdfs:subClassOf*
target_data = """\
@prefix ex: <https://example.com#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:Child1
  a ex:Cls1 ;
  ex:parent ex:Parent1 ;
.
ex:Parent1
  a ex:P_cls1, ex:P_cls4 ;
.
"""


def test_w3_list1():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=target_data, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_g, shacl_graph=shape_g, debug=False,
    )
    print(results_text)
    assert conforms


if __name__ == "__main__":
    exit(test_w3_list1())
