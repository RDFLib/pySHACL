# -*- coding: utf-8 -*-
#
# Extra tests which are not part of the SHT or DASH test suites,
# nor the discrete issues tests or the cmdline_test file.
# The need for these tests are discovered by doing converage checks and these
# are added as required.
from pyshacl import validate
from pyshacl.errors import ReportableRuntimeError

ontology_file_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:Animal a rdfs:Class ;
    rdfs:comment "The parent class for Humans and Pets"@en ;
    rdfs:subClassOf owl:Thing .

ex:Human a rdfs:Class ;
    rdfs:comment "A Human being"@en ;
    rdfs:subClassOf ex:Animal .

ex:Pet a rdfs:Class ;
    rdfs:comment "An animal owned by a human"@en ;
    rdfs:subClassOf ex:Animal .

ex:hasPet a rdf:Property ;
    rdfs:domain ex:Human ;
    rdfs:range ex:Pet .

ex:nlegs a rdf:Property ;
    rdfs:domain ex:Animal ;
    rdfs:range xsd:integer .

ex:Lizard a rdfs:Class ;
    rdfs:subClassOf ex:Pet .
"""

shacl_file_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:HumanShape a sh:NodeShape ;
    sh:property [
        sh:class ex:Pet ;
        sh:path ex:hasPet ;
    ] ;
    sh:property [
        sh:datatype xsd:integer ;
        sh:path ex:nLegs ;
        sh:maxInclusive 2 ;
        sh:minInclusive 2 ;
    ] ;
    sh:targetClass ex:Human .

ex:AnimalShape a sh:NodeShape ;
    sh:property [
        sh:datatype xsd:integer ;
        sh:path ex:nLegs ;
        sh:maxInclusive 4 ;
        sh:minInclusive 1 ;
    ] ;
    sh:targetClass ex:Animal .  
"""

data_file_text = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:Human1 rdf:type ex:Human ;
    rdf:label "Amy" ;
    ex:nLegs "2"^^xsd:integer ;
    ex:hasPet ex:Pet1 .

ex:Pet1 rdf:type ex:Lizard ;
    rdf:label "Sebastian" ;
    ex:nLegs "4"^^xsd:integer .
"""



def test_metashacl_pass():
    res = validate(data_file_text, shacl_graph=shacl_file_text,
                   meta_shacl=True, data_graph_format='turtle',
                   shacl_graph_format='turtle', ont_graph=ontology_file_text,
                   ont_graph_format="turtle", inference='both', debug=True)
    conforms, graph, string = res
    assert conforms

def test_metashacl_fail():
    bad_shacl_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ex#> .

ex:HumanShape a sh:NodeShape ;
    sh:property [
        sh:class ex:Pet ;
        sh:path "2"^^xsd:integer ;
    ] ;
    sh:property [
        sh:datatype xsd:integer ;
        sh:path ex:nLegs ;
        sh:maxInclusive 2 ;
        sh:minInclusive 2 ;
    ] ;
    sh:targetClass ex:Human .

ex:AnimalShape a sh:NodeShape ;
    sh:property [
        sh:datatype xsd:integer ;
        sh:path ex:nLegs ;
        sh:maxInclusive 4 ;
        sh:minInclusive 1 ;
    ] ;
    sh:targetClass ex:Animal .  
"""
    did_error = False
    try:
        res = validate(data_file_text, shacl_graph=bad_shacl_text,
                       meta_shacl=True, data_graph_format='turtle',
                       shacl_graph_format='turtle', ont_graph=ontology_file_text,
                       ont_graph_format="turtle", inference='both', debug=True)
        conforms, graph, string = res
        assert not conforms
    except ReportableRuntimeError as r:
        assert "Shacl Shapes Shacl file" in r.message
        did_error = True
    assert did_error

def test_serialize_report_graph():
    res = validate(data_file_text, shacl_graph=shacl_file_text,
                   data_graph_format='turtle', serialize_report_graph=True,
                   shacl_graph_format='turtle', ont_graph=ontology_file_text,
                   ont_graph_format="turtle", inference='both', debug=True)
    conforms, graph, string = res
    assert isinstance(graph, (str, bytes))

def test_web_retrieve():
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    res = validate(data_file_text, shacl_graph=shacl_file, data_graph_format='turtle',
                   shacl_graph_format='turtle', ont_graph=ont_file,
                   ont_graph_format="turtle", inference='both', debug=True)
    conforms, graph, string = res
    assert conforms

if __name__ == "__main__":
    test_metashacl_pass()
    test_metashacl_fail()
    test_web_retrieve()
    test_serialize_report_graph()
