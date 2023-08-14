# -*- coding: utf-8 -*-
#

# Portions of this file contributed by NIST are governed by the following
# statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to Title 17 Section 105 of the
# United States Code, this software is not subject to copyright
# protection within the United States. NIST assumes no responsibility
# whatsoever for its use by other parties, and makes no guarantees,
# expressed or implied, about its quality, reliability, or any other
# characteristic.
#
# We would appreciate acknowledgement if the software is used.

"""
https://github.com/RDFLib/pySHACL/issues/160

This test demonstrates two styles of using a shape focused on a
Predicate to review the class of nodes that are Subjects for that
Predicate, using the sh:class constraint.

shacl_file_1_text uses a NodeShape and sh:targetSubjectsOf.

shacl_file_2_text uses a PropertyShape and an sh:inversePath.

The motivation for these tests was to clarify how to use sh:inversePath
and a sh:targetXOf selector; sh:targetSubjectsOf turns out to lead to
incorrect behavior.

Note that depending on the style used, sh:ValidationResults will link
the "focus" node as either sh:focusNode, or sh:value.
"""

from typing import Set

from rdflib import Graph, SH, URIRef

from pyshacl import validate


data_ontology_file_text = """\
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
"""

shacl_file_1_text = """\
@prefix ex: <http://example.org/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:propertyOfA-nodeshape
  rdf:type sh:NodeShape ;
  sh:class ex:ThingA ;
  sh:targetSubjectsOf ex:propertyOfA ;
  .
"""

shacl_file_2_text = """\
@prefix ex: <http://example.org/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:propertyOfA-propertyshape
  rdf:type sh:PropertyShape ;
  sh:class ex:ThingA ;
  sh:path [
    sh:inversePath ex:propertyOfA ;
  ] ;
  sh:targetObjectsOf ex:propertyOfA ;
  .
"""


def _test_160_template(
    shacl_file_text: str,
    n_validation_result_property: URIRef,
) -> None:
    (
        conforms,
        conformance_graph,
        conformance_text,
    ) = validate(
        data_ontology_file_text,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        debug=True,
        metashacl=True,
    )

    assert not conforms
    assert isinstance(conformance_graph, Graph)

    # Find set of nodes expected to be foci of validation results.
    expected: Set[URIRef] = {URIRef("http://example.org/kb/thing-b-1")}
    computed: Set[URIRef] = set()
    for triple in conformance_graph.triples((None, n_validation_result_property, None)):
        assert isinstance(triple[2], URIRef)
        computed.add(triple[2])
    assert expected == computed


def test_160_1() -> None:
    _test_160_template(shacl_file_1_text, SH.focusNode)


def test_160_2() -> None:
    _test_160_template(shacl_file_2_text, SH.value)
