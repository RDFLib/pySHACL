# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/108
"""
from pyshacl import validate

# from DASH
shacl_file_text = """
@prefix dash: <http://datashapes.org/dash#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

dash:toString a sh:JSFunction,
        sh:SPARQLFunction ;
    rdfs:label "to string" ;
    dash:cachable true ;
    rdfs:comment "Returns a literal with datatype xsd:string that has the input value as its string. If the input value is an (URI) resource then its URI will be used." ;
    sh:jsFunctionName "dash_toString" ;
    sh:jsLibrary dash:DASHJSLibrary ;
    sh:labelTemplate "Convert {$arg} to xsd:string" ;
    sh:parameter [ a sh:Parameter ;
            sh:description "The input value." ;
            sh:name "arg" ;
            sh:nodeKind sh:IRIOrLiteral ;
            sh:path dash:arg ] ;
    sh:prefixes <http://datashapes.org/dash> ;
    sh:returnType xsd:string ;
    sh:select "SELECT (xsd:string($arg) AS ?result) WHERE { }" .
"""

def test_108():
    res = validate(shacl_file_text, advanced=True, js=True)
    conforms, graph, string = res
    assert conforms
