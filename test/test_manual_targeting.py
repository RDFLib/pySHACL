# -*- coding: utf-8 -*-
#
# Extra tests which are not part of the SHT or DASH test suites,
# nor the discrete issues tests or the cmdline_test file.
# The need for these tests are discovered by doing coverage checks and these
# are added as required.


from pyshacl import validate

ontology_file_text = """
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

exOnt:nlegs a rdf:Property ;
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

exOnt:Turtle a rdfs:Class ;
    rdfs:subClassOf exOnt:Pet .

exOnt:Goanna a rdfs:Class ;
    rdfs:subClassOf exOnt:Lizard .

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

ex:Human2 rdf:type exOnt:PreschoolTeacher ;
    rdf:label "JoAnne" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet ex:Pet2 .

ex:Pet2 rdf:type exOnt:Turtle ;
    rdf:label "Terrance" ;
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

ex:Human2 rdf:type exOnt:PreschoolTeacher ;
    rdf:label "JoAnne" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet "Terrance"^^xsd:string .

ex:Pet2 rdf:type exOnt:Turtle ;
    rdf:label "Terrance" ;
    exOnt:nLegs "four"^^xsd:string .

"""


def test_validate_pass_manual_targeting_focus():
    res = validate(
        data_file_text,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference='both',
        focus_nodes=["ex:Human1"],
        debug=True,
    )
    conforms, graph, string = res
    assert "Results (1)" not in string
    assert conforms


def test_validate_fail_manual_targeting_focus():
    res = validate(
        data_file_text_bad,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference='both',
        focus_nodes=["ex:Human1"],
        debug=True,
    )
    conforms, graph, string = res
    assert "Results (1)" in string
    assert not conforms


def test_validate_fail_manual_targeting_shape():
    res = validate(
        data_file_text_bad,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference='both',
        use_shapes=["exShape:HumanShape"],
        debug=True,
    )
    conforms, graph, string = res
    assert "Results (2)" in string
    assert not conforms


def test_validate_fail_manual_targeting_focus_with_shape():
    res = validate(
        data_file_text_bad,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        ont_graph=ontology_file_text,
        ont_graph_format="turtle",
        inference='both',
        focus_nodes=["ex:Human1"],
        use_shapes=["exShape:HumanShape"],
        debug=True,
    )
    conforms, graph, string = res
    assert "Results (1)" in string
    assert not conforms
