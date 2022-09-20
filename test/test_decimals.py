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
Test that values declared as XSD decimal type are confirmed to be conformant with datatype constraints.

_PASS and _XFAIL name portions on tests in this script denote whether the input data graph should have a True or False conformance result.
"""

from rdflib import Graph, RDF, SH

from pyshacl import validate

ontology_file_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .

<http://example.com/exOnt> a owl:Ontology ;
    rdfs:label "An example extra-ontology file."@en .

exOnt:NumberHolder a owl:Class .

exOnt:propBoolean a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:boolean .

exOnt:propDecimal a owl:DatatypeProperty ;
    rdfs:domain exOnt:NumberHolder ;
    rdfs:range xsd:decimal .
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
            sh:datatype xsd:boolean ;
            sh:path exOnt:propBoolean ;
        ] ,
        [
            sh:datatype xsd:decimal ;
            sh:path exOnt:propDecimal ;
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
    exOnt:propDecimal
      "1"^^xsd:decimal ,
      "2."^^xsd:decimal ,
      "3.4"^^xsd:decimal ,
      "5.6666666666666666667"^^xsd:decimal ,
      "-8"^^xsd:decimal ,
      "-9."^^xsd:decimal ,
      "-0."^^xsd:decimal ;
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


data_file_text_XFAIL_unrelated = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:holder1 a exOnt:NumberHolder ;
    exOnt:propBoolean
      "Not boolean" ;
    exOnt:propDecimal
      "1"^^xsd:decimal ,
      "2."^^xsd:decimal ,
      "3.4"^^xsd:decimal ,
      "5.67"^^xsd:decimal ,
      "-8"^^xsd:decimal ,
      "-9."^^xsd:decimal ,
      "-0."^^xsd:decimal ;
    .
"""


def test_validate_with_ontology_XFAIL_unrelated() -> None:
    res = validate(
        data_file_text_XFAIL_unrelated,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference="both",
        debug=True,
    )
    conforms, graph, string = res
    validation_result_tally = 0
    for triple in graph.triples((None, RDF.type, SH.ValidationResult)):
        validation_result_tally += 1
    assert not conforms
    assert validation_result_tally == 1


data_file_text_XFAIL_lexical_space = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:holder2 a exOnt:NumberHolder ;
    rdfs:comment "Each value has an error.  All values use an invalid lexical value."@en ;
    rdfs:seeAlso <https://www.w3.org/TR/turtle/#abbrev> ;
    exOnt:propDecimal
      "1.."^^xsd:decimal ,
      "2.3."^^xsd:decimal ,
      "4a"^^xsd:decimal ,
      "5x"^^xsd:decimal ,
      "6y."^^xsd:decimal ;
    .
"""


def test_validate_with_ontology_XFAIL_lexical_space() -> None:
    # TODO A runtime error is raised if the inference value is 'owlrl' or 'both', but 'none' and 'rdfs' do not raise a runtime error.  Discuss how to flag this test case.
    res = validate(
        data_file_text_XFAIL_lexical_space,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        # inference="both",
        debug=True,
    )
    conforms, graph, string = res
    validation_result_tally = 0
    for triple in graph.triples((None, RDF.type, SH.ValidationResult)):
        validation_result_tally += 1
    assert not conforms
    assert validation_result_tally == 5
