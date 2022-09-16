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
Test that values declared as the various XSD integer types are confirmed to be in their value spaces.

_PASS and _XFAIL name portions on tests in this script denote whether the input data graph should have a True or False conformance result.
"""

from typing import Set, Tuple

from rdflib import Graph, Literal, Namespace, RDF, SH, URIRef, XSD
from pyshacl import validate

EX_ONT = Namespace("http://example.com/exOnt#")

ontology_file_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .

<http://example.com/exOnt> a owl:Ontology ;
    rdfs:label "An example extra-ontology file."@en .

exOnt:NumberHolder a owl:Class .

exOnt:propInteger a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:integer .
	
exOnt:propNegativeInteger a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:negativeInteger .
	
exOnt:propNonNegativeInteger a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:nonNegativeInteger .
	
exOnt:propNonPositiveInteger a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:nonPositiveInteger .
	
exOnt:propPositiveInteger a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:positiveInteger .
"""

shacl_file_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exShape: <http://example.com/exShape#> .
@prefix exOnt: <http://example.com/exOnt#> .

<http://example.com/exShape> a owl:Ontology ;
    rdfs:label "Example Shapes File"@en .

exShape:NumberHolderShape
    sh:property
        [
            sh:datatype xsd:integer ;
            sh:path exOnt:propInteger ;
        ],
        [
            sh:datatype xsd:negativeInteger ;
            sh:path exOnt:propNegativeInteger ;
        ],
        [
            sh:datatype xsd:nonNegativeInteger ;
            sh:path exOnt:propNonNegativeInteger
        ],
        [
            sh:datatype xsd:nonPositiveInteger ;
            sh:path exOnt:propNonPositiveInteger ;
        ],
        [
            sh:datatype xsd:positiveInteger ;
            sh:path exOnt:propPositiveInteger ;
        ] ;
    sh:targetClass exOnt:NumberHolder ;
    .
"""

data_file_text_PASS = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:holder0 a exOnt:NumberHolder ;
    exOnt:propInteger -1 ;
    exOnt:propInteger 0 ;
    exOnt:propInteger 1 ;
    exOnt:propNegativeInteger "-1"^^xsd:negativeInteger ;
    exOnt:propNonNegativeInteger "0"^^xsd:nonNegativeInteger ;
    exOnt:propNonNegativeInteger "1"^^xsd:nonNegativeInteger ;
    exOnt:propNonPositiveInteger "-1"^^xsd:nonPositiveInteger ;
    exOnt:propNonPositiveInteger "0"^^xsd:nonPositiveInteger ;
    exOnt:propPositiveInteger "1"^^xsd:positiveInteger ;
    .
"""


def test_validate_with_ontology() -> None:
    g = Graph().parse(data=data_file_text_PASS, format='turtle')
    e = Graph().parse(data=ontology_file_text, format='turtle')
    g_len = len(g)
    res = validate(
        g, shacl_graph=shacl_file_text, shacl_graph_format='turtle', ont_graph=e, inference='both', debug=True
    )
    conforms, graph, string = res
    g_len2 = len(g)
    assert conforms
    assert g_len2 == g_len


data_file_text_XFAIL_sh_datatypes = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:holder1 a exOnt:NumberHolder ;
    rdfs:comment "Each property except propInteger has an error.  All properties except propInteger use the wrong datatype, as Turtle infers xsd:integer on unannotated integer lexical values when none is specified."@en ;
    rdfs:seeAlso <https://www.w3.org/TR/turtle/#abbrev> ;
    exOnt:propInteger -1 ;
    exOnt:propInteger 0 ;
    exOnt:propInteger 1 ;
    exOnt:propNegativeInteger -1 ;
    exOnt:propNonNegativeInteger 0 ;
    exOnt:propNonNegativeInteger 1 ;
    exOnt:propNonPositiveInteger -1 ;
    exOnt:propNonPositiveInteger 0 ;
    exOnt:propPositiveInteger 1 ;
    .
"""


def test_validate_with_ontology_XFAIL_sh_datatypes() -> None:
    res = validate(
        data_file_text_XFAIL_sh_datatypes,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference='both',
        debug=True,
    )
    conforms, graph, string = res
    validation_result_tally = 0
    for triple in graph.triples((None, RDF.type, SH.ValidationResult)):
        validation_result_tally += 1
    assert not conforms
    assert validation_result_tally == 6


data_file_text_XFAIL_spaces = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:holder2 a exOnt:NumberHolder ;
    rdfs:comment "Each property has an error with the object-position node's datatype.  propInteger's has a lexical-space error.  Each other has a value-space error when considering the datatype declaration in the Literal."@en ;
    exOnt:propInteger "zero"^^xsd:integer ;
    exOnt:propNegativeInteger "0"^^xsd:negativeInteger ;
    exOnt:propNegativeInteger "1"^^xsd:negativeInteger ;
    exOnt:propNonNegativeInteger "-1"^^xsd:nonNegativeInteger ;
    exOnt:propNonPositiveInteger "1"^^xsd:nonPositiveInteger ;
    exOnt:propPositiveInteger "-1"^^xsd:positiveInteger ;
    exOnt:propPositiveInteger "0"^^xsd:positiveInteger ;
    .
"""


def test_validate_with_ontology_XFAIL_spaces() -> None:
    res = validate(
        data_file_text_XFAIL_spaces,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference='both',
        debug=True,
    )
    conforms, graph, string = res

    expected_path_values: Set[Tuple[URIRef, Literal]] = {
        (EX_ONT.propInteger, Literal("zero", datatype=XSD.integer)),
        (EX_ONT.propNegativeInteger, Literal("0", datatype=XSD.negativeInteger)),
        (EX_ONT.propNegativeInteger, Literal("1", datatype=XSD.negativeInteger)),
        (EX_ONT.propNonNegativeInteger, Literal("-1", datatype=XSD.nonNegativeInteger)),
        (EX_ONT.propNonPositiveInteger, Literal("1", datatype=XSD.nonPositiveInteger)),
        (EX_ONT.propPositiveInteger, Literal("-1", datatype=XSD.positiveInteger)),
        (EX_ONT.propPositiveInteger, Literal("0", datatype=XSD.positiveInteger)),
    }
    computed_path_values: Set[Tuple[URIRef, Literal]] = set()

    # .triples() is used somewhat redundantly instead of using SPARQL, to avoid the possibility of any extra interpretation steps with SPARQL conversion.
    for triple0 in graph.triples((None, RDF.type, SH.ValidationResult)):
        n_validation_result = triple0[0]
        for triple1 in graph.triples((n_validation_result, SH.resultPath, None)):
            n_path = triple1[2]
            for triple2 in graph.triples((n_validation_result, SH.value, None)):
                l_value: Literal = triple2[2]
                assert isinstance(l_value, Literal)
                computed_path_values.add((n_path, l_value))
    assert not conforms
    assert expected_path_values == computed_path_values
