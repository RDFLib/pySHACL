# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/301
"""
import sys

import rdflib

import pyshacl

DATA_TTL = """\
@prefix ex: <http://example.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:myVariable
    a ex:Variable, owl:NamedIndividual ;
    ex:name "test_variable" ;
    ex:datatype xsd:integer ;
    ex:allowedValues ( "1"^^xsd:integer "test"^^xsd:string "5"^^xsd:integer) .
"""

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:TestShape
    a sh:NodeShape ;
    sh:targetClass ex:Variable ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "Test constraint" ;
        sh:select '''
            PREFIX ex: <http://example.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT $this WHERE {
                $this ex:allowedValues ?list .
                ?list rdf:rest/rdf:first ?val .
            }
        ''' ;
    ] .
"""


def test_301():
    data_g = rdflib.Graph().parse(data=DATA_TTL, format="turtle")
    shapes_g = rdflib.Graph().parse(data=SHAPES_TTL, format="turtle")
    conforms, report_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shapes_g,
        advanced=True,
        debug=False,
    )
    assert not conforms
    assert not isinstance(report_graph, pyshacl.errors.ValidationFailure)
    assert "Test constraint" in results_text


if __name__ == "__main__":
    sys.exit(test_301())
