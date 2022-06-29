import rdflib
import pyshacl

model_data = """
@prefix ex: <urn:ex#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:A a ex:SubSubClass .
"""

shapes_and_ontology_data = """
@prefix ex: <urn:ex#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Class a owl:Class .
ex:SubClass a owl:Class ;
    rdfs:subClassOf ex:Class .
ex:SubSubClass a owl:Class ;
    rdfs:subClassOf ex:SubClass .

ex:FailedRule a sh:NodeShape ;
    sh:targetClass ex:Class ;
    sh:rule [
        a sh:TripleRule ;
        sh:object ex:Inferred ;
        sh:predicate ex:hasProperty ;
        sh:subject sh:this ;
    ] .
"""


def test_ruleTargetClass_twograph():
    shape_g = rdflib.Graph().parse(data=shapes_and_ontology_data, format='turtle')
    data_g = rdflib.Graph().parse(data=model_data, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_g, shacl_graph=shape_g, advanced=True
    )
    assert conforms
    assert (rdflib.URIRef("urn:ex#A"), rdflib.URIRef("urn:ex#hasProperty"), rdflib.URIRef("urn:ex#Inferred")) in data_g

def test_ruleTargetClass_twograph_ontgraph():
    shape_g = rdflib.Graph().parse(data=shapes_and_ontology_data, format='turtle')
    data_g = rdflib.Graph().parse(data=model_data, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_g, ont_graph=shape_g, advanced=True
    )
    assert conforms
    assert (rdflib.URIRef("urn:ex#A"), rdflib.URIRef("urn:ex#hasProperty"), rdflib.URIRef("urn:ex#Inferred")) in data_g

def test_ruleTargetClass_twograph_ont_and_shape_graph():
    shape_g = rdflib.Graph().parse(data=shapes_and_ontology_data, format='turtle')
    data_g = rdflib.Graph().parse(data=model_data, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_g, shacl_graph=shape_g, ont_graph=shape_g, advanced=True
    )
    assert conforms
    assert (rdflib.URIRef("urn:ex#A"), rdflib.URIRef("urn:ex#hasProperty"), rdflib.URIRef("urn:ex#Inferred")) in data_g

def test_ruleTargetClass_onegraph():
    data_g = rdflib.Graph().parse(data=shapes_and_ontology_data, format='turtle').parse(data=model_data, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_g, advanced=True
    )
    assert conforms
    assert (rdflib.URIRef("urn:ex#A"), rdflib.URIRef("urn:ex#hasProperty"), rdflib.URIRef("urn:ex#Inferred")) in data_g
