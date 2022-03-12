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
https://github.com/RDFLib/pySHACL/issues/126
"""

from typing import Optional

from pyshacl import validate
from rdflib import Namespace, SH, URIRef

NS_EX = Namespace("http://example.org/ns#")

mixed_file_text = """
@prefix ex: <http://example.org/ns#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

ex:myProperty-datatype
	a sh:PropertyShape ;
	rdfs:comment "Violations of sh:datatype are produced as warnings"@en ;
	sh:datatype xsd:string ;
	sh:path ex:myProperty ;
	sh:severity sh:Warning ;
	.

ex:myProperty-maxLength
	a sh:PropertyShape ;
	rdfs:comment "The default severity here is sh:Info"@en ;
	sh:maxLength 10 ;
	sh:message "Too many characters"@en ;
	sh:path ex:myProperty ;
	sh:severity sh:Info ;
	.

ex:MyShape
	a sh:NodeShape ;
	rdfs:comment "This example was adapted from the example shapes and validation graph in the Severity section of the SHACL specification."@en ;
	rdfs:seeAlso "https://www.w3.org/TR/shacl/#severity" ;
	sh:property
		ex:myProperty-datatype ,
		ex:myProperty-maxLength
		;
	sh:targetNode ex:MyInstance ;
	.

ex:MyInstance
	rdfs:comment "This instance triggers one Info-level and one Warning-level violation."@en ;
	ex:myProperty "http://toomanycharacters"^^xsd:anyURI ;
	.
"""


def _test_126_template(expected_conformance: bool, allow_level: Optional[URIRef] = None) -> None:
    validate_kwargs: Dict[Any] = {"data_graph_format": "turtle", "shacl_graph_format": "turtle", "debug": True}
    if allow_level is None:
        pass
    elif allow_level == SH.Info:
        validate_kwargs["allow_infos"] = True
    elif allow_level == SH.Warning:
        validate_kwargs["allow_warnings"] = True
    else:
        raise NotImplementedError("allow_level=%r" % allow_level)

    res1 = validate(mixed_file_text, **validate_kwargs)
    conforms, graph, string = res1
    assert conforms == expected_conformance

    datatype_shape_reported = False
    maxlength_shape_reported = False

    # Confirm the report graph emits ValidationResults pertaining to each expected triggering property shape.
    for triple in graph.triples((None, SH.sourceShape, NS_EX["myProperty-datatype"])):
        datatype_shape_reported = True
    for triple in graph.triples((None, SH.sourceShape, NS_EX["myProperty-maxLength"])):
        maxlength_shape_reported = True

    assert datatype_shape_reported
    assert maxlength_shape_reported


def test_126_1() -> None:
    """
    With no severities allowed, expect non-conformance.
    """
    _test_126_template(False)


def test_126_2() -> None:
    """
    With Infos allowed, expect non-conformance.
    """
    _test_126_template(False, SH.Info)


def test_126_3() -> None:
    """
    With Warnings allowed, expect conformance.
    """
    _test_126_template(True, SH.Warning)
