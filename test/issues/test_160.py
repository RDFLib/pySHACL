# -*- coding: utf-8 -*-
#

# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to title 17 Section 105 of the
# United States Code this software is not subject to copyright
# protection and is in the public domain. NIST assumes no
# responsibility whatsoever for its use by other parties, and makes
# no guarantees, expressed or implied, about its quality,
# reliability, or any other characteristic.
#
# We would appreciate acknowledgement if the software is used.

"""
https://github.com/RDFLib/pySHACL/issues/160
"""

from typing import Set

from rdflib import SH, URIRef

from pyshacl import validate


mixed_file_text = """\
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://example.org/kb>
  rdf:type owl:Ontology ;
  rdfs:label "Test of inversePath" ;
.
kb:thing-a-1
  rdf:type ex:ThingA ;
  ex:propertyOfA "1" ;
.
kb:thing-b-1
  rdf:type ex:ThingB ;
  ex:propertyOfA "1" ;
.
ex:propertyOfA-shape
  rdf:type sh:PropertyShape ;
  sh:class ex:ThingA ;
  sh:path [
    sh:inversePath ex:propertyOfA ;
  ] ;
  sh:targetSubjectsOf ex:propertyOfA ;
.
"""


def test_160() -> None:
    (conforms, conformance_graph, conformance_text,) = validate(
        mixed_file_text,
        shacl_graph=mixed_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        debug=True,
    )

    assert not conforms

    # Find set of nodes expected to be foci of validation results.
    expected: Set[URIRef] = {URIRef("http://example.org/thing-b-1")}
    computed: Set[URIRef] = set()
    for triple in conformance_graph.triples((None, SH.focusNode, None)):
        assert isinstance(triple[2], URIRef)
        computed.add(triple[2])
    assert expected == computed
