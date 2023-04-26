# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/162
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

ex:ExampleParentShape a sh:NodeShape ;
    sh:targetClass ex:test_class ;
    sh:node ex:nodeShape1,
        ex:nodeShape2 .

ex:nodeShape1 a sh:NodeShape ;
    sh:property [
        sh:path schema:name ;
        sh:class ex:test_class_1
    ] .

ex:nodeShape2 a sh:NodeShape ;
    sh:property [
        sh:path schema:subOrganization ;
        sh:class ex:test_class_1
    ] .
"""

data_file = """
@prefix ex: <urn:ex#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://schema.org/> .

# define ontology
ex:test_class a owl:Class .
ex:test_class_1 a owl:Class .
ex:test_class_2 a owl:Class .

# define model
ex:name_1 a ex:test_class_1 .
ex:org_1 a ex:test_class_2 . # this will cause test to fail

ex:test_entity a ex:test_class ;
    schema:name ex:name_1 ;
    schema:subOrganization ex:org_1 .

"""


def test_162() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    conforms, report, message = validate(data_g, shacl_graph=shapes, debug=True)
    assert not conforms
    # confirm that both nodeShapes are included in the error message
    assert "Value does not conform to every Shape in ('ex:nodeShape1', 'ex:nodeShape2')" in message


if __name__ == "__main__":
    test_162()
