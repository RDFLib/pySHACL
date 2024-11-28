# -*- coding: utf-8 -*-
#
# Extra tests which are not part of the SHT or DASH test suites,
# nor the discrete issues tests or the cmdline_test file.
# The need for these tests are discovered by doing coverage checks and these
# are added as required.
import os
import re

from rdflib import Graph, Dataset

from pyshacl import validate
from pyshacl.errors import ReportableRuntimeError

ontology_graph_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .

<http://example.com/exOnt> a owl:Ontology ;
    rdfs:label "An example extra-ontology file."@en .

exOnt:Animal a rdfs:Class ;
    rdfs:comment "The parent class for Humans and Pets"@en ;
    rdfs:subClassOf owl:Thing .

exOnt:Human a rdfs:Class ;
    rdfs:comment "A Human being"@en ;
    rdfs:subClassOf exOnt:Animal .

exOnt:Pet a rdfs:Class ;
    rdfs:comment "An animal owned by a human"@en ;
    rdfs:subClassOf exOnt:Animal .

exOnt:hasPet a rdf:Property ;
    rdfs:domain exOnt:Human ;
    rdfs:range exOnt:Pet .

exOnt:nLegs a rdf:Property ;
    rdfs:domain exOnt:Animal ;
    rdfs:range xsd:integer .

exOnt:Teacher a rdfs:Class ;
    rdfs:comment "A Human who is a teacher."@en ;
    rdfs:subClassOf exOnt:Human .

exOnt:PreschoolTeacher a rdfs:Class ;
    rdfs:comment "A Teacher who teaches preschool."@en ;
    rdfs:subClassOf exOnt:Teacher .

exOnt:Lizard a rdfs:Class ;
    rdfs:subClassOf exOnt:Pet .

exOnt:Goanna a rdfs:Class ;
    rdfs:subClassOf exOnt:Lizard .

"""

ontology_ds_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
# This is a TRIG file.

<http://example.com/exOnt-graph> {
<http://example.com/exOnt> a owl:Ontology ;
    rdfs:label "An example extra-ontology file."@en .

exOnt:Animal a rdfs:Class ;
    rdfs:comment "The parent class for Humans and Pets"@en ;
    rdfs:subClassOf owl:Thing .

exOnt:Human a rdfs:Class ;
    rdfs:comment "A Human being"@en ;
    rdfs:subClassOf exOnt:Animal .

exOnt:Pet a rdfs:Class ;
    rdfs:comment "An animal owned by a human"@en ;
    rdfs:subClassOf exOnt:Animal .

exOnt:hasPet a rdf:Property ;
    rdfs:domain exOnt:Human ;
    rdfs:range exOnt:Pet .

exOnt:nLegs a rdf:Property ;
    rdfs:domain exOnt:Animal ;
    rdfs:range xsd:integer .

exOnt:Teacher a rdfs:Class ;
    rdfs:comment "A Human who is a teacher."@en ;
    rdfs:subClassOf exOnt:Human .

exOnt:PreschoolTeacher a rdfs:Class ;
    rdfs:comment "A Teacher who teaches preschool."@en ;
    rdfs:subClassOf exOnt:Teacher .

exOnt:Lizard a rdfs:Class ;
    rdfs:subClassOf exOnt:Pet .

exOnt:Goanna a rdfs:Class ;
    rdfs:subClassOf exOnt:Lizard .
}
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

exShape:HumanShape a sh:NodeShape ;
    sh:property [
        sh:class exOnt:Pet ;
        sh:path exOnt:hasPet ;
    ] ;
    sh:property [
        sh:datatype xsd:integer ;
        sh:path exOnt:nLegs ;
        sh:maxInclusive 2 ;
        sh:minInclusive 2 ;
    ] ;
    sh:targetClass exOnt:Human .

exShape:AnimalShape a sh:NodeShape ;
    sh:property [
        sh:datatype xsd:integer ;
        sh:path exOnt:nLegs ;
        sh:maxInclusive 4 ;
        sh:minInclusive 1 ;
    ] ;
    sh:targetClass exOnt:Animal .
"""

data_file_text = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:Human1 rdf:type exOnt:PreschoolTeacher ;
    rdf:label "Amy" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet ex:Pet1 .

ex:Pet1 rdf:type exOnt:Goanna ;
    rdf:label "Sebastian" ;
    exOnt:nLegs "4"^^xsd:integer .
"""

data_file_text_bad = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:Human1 rdf:type exOnt:PreschoolTeacher ;
    rdf:label "Amy" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet "Sebastian"^^xsd:string .

ex:Pet1 rdf:type exOnt:Goanna ;
    rdf:label "Sebastian" ;
    exOnt:nLegs "four"^^xsd:string .
"""


def test_validate_ds_with_graph_ontology():
    ds = Dataset()
    ds.parse(data=data_file_text_bad, format='turtle')
    extra_g = Graph()
    extra_g.parse(data=ontology_graph_text, format='turtle')

    ds_len = len(ds)
    res = validate(
        ds, shacl_graph=shacl_file_text, shacl_graph_format='turtle', ont_graph=extra_g, inference='rdfs', debug=True
    )
    conforms, graph, string = res
    assert not conforms
    # Assert that the dataset is unchanged
    ds_len2 = len(ds)
    assert ds_len2 == ds_len

def test_validate_ds_with_ds_ontology():
    ds = Dataset()
    ds.parse(data=data_file_text_bad, format='turtle')
    extra_ds = Dataset()
    extra_ds.parse(data=ontology_ds_text, format='trig')

    ds_len = len(ds)
    res = validate(
        ds, shacl_graph=shacl_file_text, shacl_graph_format='turtle', ont_graph=extra_ds, inference='rdfs', debug=True
    )
    conforms, graph, string = res
    assert not conforms
    # Assert that the dataset is unchanged
    ds_len2 = len(ds)
    assert ds_len2 == ds_len

def test_validate_ds_with_ds_ontology_inplace():
    ds = Dataset()
    ds.parse(data=data_file_text_bad, format='turtle')
    extra_ds = Dataset()
    extra_ds.parse(data=ontology_ds_text, format='trig')

    ds_len = len(ds)
    res = validate(
        ds,
        shacl_graph=shacl_file_text,
        shacl_graph_format='turtle',
        ont_graph=extra_ds,
        inference='rdfs',
        debug=True,
        inplace=True
    )
    conforms, graph, string = res
    assert not conforms
    # Assert that the dataset is changed
    ds_len2 = len(ds)
    assert ds_len2 != ds_len
    a = ds.serialize(format='trig')
    print(a)

