# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/154
"""

import rdflib

from pyshacl import validate

shacl_file = """\
@prefix ex: <urn:ex#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix schema: <http://schema.org/> .

schema:Organization
    a rdfs:Class, sh:NodeShape ;
    sh:property
    [
        sh:path schema:name ;
        sh:label "name" ;
        sh:description "The official name of the entity being described." ;
        sh:datatype xsd:string ;
        sh:minCount 1;
    ],
    [
        sh:path schema:subOrganization ;
        sh:label "contained organization" ;
        sh:description "An organization contained within a parent organization." ;
        sh:node schema:Organization ;
    ] ;
.
"""

data_file = """\
{
    "@context": "http://schema.org",
    "@id": "http://www.illinoiscourts.gov/Circuit",
    "@type":"http://schema.org/Organization",
    "name": "State of Illinois Circuit Court",
    "subOrganization":  {
        "@context": "http://schema.org/",
        "@id": "http://www.illinoiscourts.gov/Circuit#Circuit1",
        "name": "State of Illinois Circuit 1",
        "subOrganization":  {
            "@id": "http://www.illinoiscourts.gov/Circuit#Circuit1District1",
            "notname": "State of Illinois Circuit 1 District 1"
        }
    }
}
"""


def test_154() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file, format="json-ld")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    res = validate(data_g, shacl_graph=shapes, debug=False)
    conforms, graph, string = res
    assert not conforms
    assert "Constraint Violation in NodeConstraintComponent" in string


if __name__ == "__main__":
    test_154()
