# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/98
"""
import os

from pyshacl import validate


mixed_file_text = """\
# baseURI: http://datashapes.org/sh/tests/core/complex/personexample.test
# imports: http://datashapes.org/schema
# prefix: ex

@prefix dash: <http://datashapes.org/dash#> .
@prefix ex: <http://datashapes.org/sh/tests/core/complex/personexample.test#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://datashapes.org/sh/tests/core/complex/personexample.test>
  rdf:type owl:Ontology ;
  rdfs:label "Test of personexample" ;
  owl:imports <http://datashapes.org/schema> ;
.
ex:Alice
  rdf:type ex:Person ;
  ex:ssn "987-65-432A" ;
.
ex:Bob
  rdf:type ex:Person ;
  ex:ssn "123-45-6789" ;
  ex:ssn "124-35-6789" ;
.
ex:Calvin
  rdf:type ex:Person ;
  ex:birthDate "1999-09-09"^^xsd:date ;
  ex:worksFor ex:UntypedCompany ;
.

ex:PersonShape
  rdf:type sh:NodeShape ;
  sh:closed "true"^^xsd:boolean ;
  sh:ignoredProperties (
      rdf:type
    ) ;
  sh:property [
    sh:path ex:ssn ;
    sh:datatype xsd:string ;
    sh:maxCount 1 ;
    sh:pattern "^\\\\d{3}-\\\\d{2}-\\\\d{4}$" ;
    sh:message "SSN must be 3 digits - 2 digits - 4 digits."
  ] ;
  sh:property [
    sh:path ex:worksFor ;
    sh:class ex:Company ;
    sh:nodeKind sh:IRI
  ] ;
  sh:property [
      sh:path [
          sh:inversePath ex:worksFor ;
        ] ;
      sh:name "employee" ;
    ] ;
  sh:targetClass ex:Person ;
.

"""


def test_98():
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run owl:imports in debhelper tests.")
        assert True
        return True
    res1 = validate(
        mixed_file_text,
        shacl_graph=mixed_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        do_owl_imports=True,
        debug=True,
    )
    conforms, _, _ = res1
    assert not conforms
