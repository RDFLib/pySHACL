# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/47

import rdflib
from pyshacl import validate
"""
import rdflib
from pyshacl import validate
graph_data = """
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sch:  <http://schema.org/> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix ex:  <http://example.org/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

ex:JohnDoe a ex:XXXX .
ex:JohnDoe ex:name "hello.txt" .
"""

shape_data = """
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sch:  <http://schema.org/> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix ex:   <http://example.org/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

ex:PersonShape
  a sh:NodeShape ;
  sh:targetClass ex:XXXX ;
  sh:property ex:PersonShape-name .

ex:PersonShape-name
  a sh:PropertyShape ;
  sh:path ex:name ;
  sh:minCount 1 ;
  sh:pattern  ".*\\.txt" .
"""

data = rdflib.Graph().parse(data=graph_data, format='ttl')
shape = rdflib.Graph().parse(data=shape_data, format='ttl')
def test_047():
    conforms, g, s = validate(data, shacl_graph=shape, abort_on_error=False, meta_shacl=False, debug=True, advanced=True)
    assert conforms


if __name__ == "__main__":
    test_047()
