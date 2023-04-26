# -*- coding: utf-8 -*-
#
# Extra tests which are not part of the SHT or DASH test suites,
# nor the discrete issues tests or the cmdline_test file.
# The need for these tests are discovered by doing coverage checks and these
# are added as required.
import os
import re
from rdflib import Graph
from pyshacl import validate
from pyshacl.errors import ReportableRuntimeError

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

def test_validate_with_ontology():
    g = Graph().parse(data=data_file_text, format='turtle')
    e = Graph().parse(data=ontology_file_text, format='turtle')
    g_len = len(g)
    res = validate(g, shacl_graph=shacl_file_text,
                   shacl_graph_format='turtle',
                   ont_graph=e, inference='both', debug=True)
    conforms, graph, string = res
    g_len2 = len(g)
    assert conforms
    assert g_len2 == g_len

def test_validate_with_ontology_inplace():
    g = Graph().parse(data=data_file_text, format='turtle')
    e = Graph().parse(data=ontology_file_text, format='turtle')
    g_len = len(g)
    res = validate(g, shacl_graph=shacl_file_text,
                   shacl_graph_format='turtle',
                   ont_graph=e, inference='both', debug=True, inplace=True)
    conforms, graph, string = res
    g_len2 = len(g)
    assert conforms
    assert g_len2 != g_len

def test_validate_with_ontology_fail1():
    res = validate(data_file_text_bad, shacl_graph=shacl_file_text,
                   data_graph_format='turtle', shacl_graph_format='turtle',
                   ont_graph=ontology_file_text,  ont_graph_format="turtle",
                   inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms

def test_validate_with_ontology_fail2():
    res = validate(data_file_text_bad, shacl_graph=shacl_file_text,
                   data_graph_format='turtle', shacl_graph_format='turtle',
                   ont_graph=ontology_file_text, ont_graph_format="turtle",
                   inference=None, debug=True)
    conforms, graph, string = res
    assert not conforms

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
        assert "Shapes SHACL (MetaSHACL) file." in r.message
        did_error = True
    assert did_error

data_file_text_bn = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:Student1 exOnt:hasTeacher [
    rdf:type exOnt:PreschoolTeacher ;
    rdf:label "Amy" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet ex:Pet1 ]
.

ex:Pet1 rdf:type exOnt:Goanna ;
    rdf:label "Sebastian" ;
    exOnt:nLegs "4"^^xsd:integer .
"""

data_file_text_bad_bn = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:Student1 exOnt:hasTeacher [
    rdf:type exOnt:PreschoolTeacher ;
    rdf:label "Amy" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet "Sebastian"^^xsd:string ]
.

ex:Pet1 rdf:type exOnt:Goanna ;
    rdf:label "Sebastian" ;
    exOnt:nLegs "four"^^xsd:string .
"""

def test_blank_node_string_generation():

    res = validate(data_file_text_bad_bn, shacl_graph=shacl_file_text,
                   data_graph_format='turtle', shacl_graph_format='turtle',
                   ont_graph=ontology_file_text,  ont_graph_format="turtle",
                   inference='rdfs', debug=True)
    conforms, graph, string = res
    assert not conforms
    rx = r"^\s*Focus Node\:\s+\[.+rdf:type\s+.+exOnt\:PreschoolTeacher.*\]$"
    matches = re.search(rx, string, flags=re.MULTILINE)
    assert matches


def test_serialize_report_graph():
    res = validate(data_file_text, shacl_graph=shacl_file_text,
                   data_graph_format='turtle', serialize_report_graph=True,
                   shacl_graph_format='turtle', ont_graph=ontology_file_text,
                   ont_graph_format="turtle", inference='both', debug=True)
    conforms, graph, string = res
    assert isinstance(graph, (str, bytes))

shacl_file_property_shapes_text = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exShape: <http://example.com/exShape#> .
@prefix exOnt: <http://example.com/exOnt#> .

<http://example.com/exShape> a owl:Ontology ;
    rdfs:label "Example Shapes File"@en .

exShape:HumanHasPetShape a sh:PropertyShape ;
    sh:class exOnt:Pet ;
    sh:path exOnt:hasPet ;
    sh:targetClass exOnt:Human .

exShape:HumanHasLegsShape a sh:PropertyShape ;
    sh:datatype xsd:integer ;
    sh:path exOnt:nLegs ;
    sh:maxInclusive 2 ;
    sh:minInclusive 2 ;
    sh:targetClass exOnt:Human .

exShape:PetHasLegsShape a sh:PropertyShape ;
    sh:datatype xsd:integer ;
    sh:path exOnt:nLegs ;
    sh:maxInclusive 4 ;
    sh:minInclusive 1 ;
    sh:targetClass exOnt:Animal .
"""

def test_property_shape_focus():
    res = validate(data_file_text, shacl_graph=shacl_file_property_shapes_text,
                   data_graph_format='turtle', shacl_graph_format='turtle',
                   ont_graph=ontology_file_text,  ont_graph_format="turtle",
                   inference='rdfs', debug=True)
    conforms, graph, string = res
    assert conforms

def test_property_shape_focus_fail1():
    res = validate(data_file_text_bad, shacl_graph=shacl_file_property_shapes_text,
                   data_graph_format='turtle', shacl_graph_format='turtle',
                   ont_graph=ontology_file_text,  ont_graph_format="turtle",
                   inference='rdfs', debug=True)
    conforms, graph, string = res
    assert not conforms

web_d1_ttl = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:Human1 rdf:type exOnt:Human ;
    rdf:label "Amy" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet ex:Pet1 .

ex:Pet1 rdf:type exOnt:Lizard ;
    rdf:label "Sebastian" ;
    exOnt:nLegs "4"^^xsd:integer .
"""
web_d2_ttl = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix exOnt: <http://example.com/exOnt#> .
@prefix ex: <http://example.com/ex#> .

ex:Human1 rdf:type exOnt:Human ;
    rdf:label "Amy" ;
    exOnt:nLegs "2"^^xsd:integer ;
    exOnt:hasPet "Sebastian"^^xsd:string .

ex:Pet1 rdf:type exOnt:Lizard ;
    rdf:label "Sebastian" ;
    exOnt:nLegs "g"^^xsd:string .
"""

def test_web_retrieve():
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run web requests in debhelper tests.")
        assert True
        return True
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    res = validate(web_d1_ttl, shacl_graph=shacl_file, data_graph_format='turtle',
                   shacl_graph_format='turtle', ont_graph=ont_file,
                   ont_graph_format="turtle", inference='both', debug=True)
    conforms, graph, string = res
    assert conforms


def test_web_retrieve_fail():
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run web requests in debhelper tests.")
        assert True
        return True
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    res = validate(web_d2_ttl, shacl_graph=shacl_file, data_graph_format='turtle',
                   shacl_graph_format='turtle', ont_graph=ont_file,
                   ont_graph_format="turtle", inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms


my_partial_shapes_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.com/ex1#> .

<http://example.com/ex1> a owl:Ontology ;
    owl:imports <https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl> .
"""

my_partial_ont_text = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.com/ex2#> .

<http://example.com/ex2> a owl:Ontology ;
    owl:imports <https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl> .
"""


def test_owl_imports():
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run owl:imports in debhelper tests.")
        assert True
        return True
    res = validate(web_d1_ttl, shacl_graph=my_partial_shapes_text, data_graph_format='turtle',
                   shacl_graph_format='turtle', ont_graph=my_partial_ont_text,
                   ont_graph_format="turtle", inference='both', debug=True, do_owl_imports=True)
    conforms, graph, string = res
    print(string)
    assert conforms


def test_owl_imports_fail():
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run owl:imports in debhelper tests.")
        assert True
        return True

    res = validate(web_d2_ttl, shacl_graph=my_partial_shapes_text, data_graph_format='turtle',
                   shacl_graph_format='turtle', ont_graph=my_partial_ont_text,
                   ont_graph_format=None, inference='both', debug=True, do_owl_imports=True)
    conforms, graph, string = res
    print(string)
    assert not conforms

def test_sparql_message_subst():
    df = '''@prefix ex: <http://datashapes.org/sh/tests/#> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    ex:ValidResource1
      rdf:type rdfs:Resource ;
    .
    ex:InvalidResource1
      rdf:type rdfs:Resource ;
      rdfs:label "Invalid resource 1" ;
    .
    ex:InvalidResource2
      rdf:type rdfs:Resource ;
      rdfs:label "Invalid label 1" ;
      rdfs:label "Invalid label 2" ;
    .
    ex:TestShape
      rdf:type sh:NodeShape ;
      rdfs:label "Test shape" ;
      sh:sparql ex:TestShape-sparql ;
      sh:targetNode ex:InvalidResource1 ;
      sh:targetNode ex:InvalidResource2 ;
      sh:targetNode ex:ValidResource1 ;
    .
    ex:TestShape-sparql
      sh:message "{$this} cannot have a {$path} of {$value}" ;
      sh:prefixes <http://datashapes.org/sh/tests/sparql/node/sparql-001.test> ;
      sh:select """
        SELECT $this ?path ?value
        WHERE {
            $this ?path ?value .
            FILTER (?path = <http://www.w3.org/2000/01/rdf-schema#label>) .
        }""" ;
    .'''
    res = validate(df, data_graph_format='turtle', inference=None, debug=True,)
    conforms, graph, s = res
    assert "#InvalidResource1 cannot have a http://www.w3.org/2000/01/rdf-schema#label of Invalid resource 1" in s
    assert "#InvalidResource2 cannot have a http://www.w3.org/2000/01/rdf-schema#label of Invalid label 1" in s
    assert "#InvalidResource2 cannot have a http://www.w3.org/2000/01/rdf-schema#label of Invalid label 2" in s
    assert not conforms

if __name__ == "__main__":
    test_validate_with_ontology()
    test_validate_with_ontology_fail1()
    test_validate_with_ontology_fail2()
    test_metashacl_pass()
    test_metashacl_fail()
    test_blank_node_string_generation()
    test_property_shape_focus()
    test_property_shape_focus_fail1()
    test_web_retrieve()
    test_serialize_report_graph()
    test_owl_imports()
    test_owl_imports_fail()
    test_sparql_message_subst()

