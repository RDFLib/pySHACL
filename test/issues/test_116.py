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
https://github.com/RDFLib/pySHACL/issues/116
"""

import rdflib

from pyshacl import validate


shacl_file_base = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/issue/116#> .

<http://example.org/issue/116>
  rdf:type owl:Ontology ;
  sh:declare [
    sh:prefix "ex" ;
    sh:namespace "http://example.org/issue/116#"^^xsd:anyURI ;
    ] .

ex:ThingWithAStringProperty
	a owl:Class ;
	a sh:NodeShape ;
	sh:property [
		sh:datatype xsd:string ;
		%s
		sh:path ex:someString ;
	] .
'''

shacl_file_with_nodekind = shacl_file_base % "sh:nodeKind sh:Literal ;"
shacl_file_without_nodekind = shacl_file_base % ""

data_file_base = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/issue/116#> .
@prefix kb: <http://example.org/kb/> .

kb:someIndividual
	a ex:ThingWithAStringProperty ;
"""

data_file_PASS1 = data_file_base + """	ex:someString "A string with a language"@en ."""
data_file_PASS2 = data_file_base + """	ex:someString "A string without a language" ."""


def _test_116_template(shacl_file_text, data_file_text):
    data = rdflib.Graph()
    data.parse(data=data_file_text, format="turtle")
    res = validate(
        data,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        debug=True,
    )
    conforms, graph, string = res
    assert conforms


def test_116_positive1():
    _test_116_template(shacl_file_without_nodekind, data_file_PASS1)


def test_116_positive2():
    _test_116_template(shacl_file_without_nodekind, data_file_PASS2)


def test_116_positive3():
    _test_116_template(shacl_file_with_nodekind, data_file_PASS1)


def test_116_positive4():
    _test_116_template(shacl_file_with_nodekind, data_file_PASS2)


if __name__ == "__main__":
    test_116_positive1()
    test_116_positive2()
    test_116_positive3()
    test_116_positive4()
