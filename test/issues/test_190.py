# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/190
"""

import rdflib
from pyshacl import validate
from rdflib.namespace import RDF
from rdflib.namespace import SH

shacl_file = """\
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:    <http://www.semanticweb.org/shacltest#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .


ex:multipleSPARQLResults
    a sh:NodeShape ;
    sh:targetClass ex:Class1;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "{?Class2Instance} does not have a related Class3 Instance" ;
        sh:select  '''
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX ex: <http://www.semanticweb.org/shacltest#>
            select * where {
                ?this a ex:Class1 .
                ?Class2Instance a ex:Class2 .
                ?this ex:has_relation ?Class2Instance .
                OPTIONAL {
                    ?Class2Instance ex:has_relation ?Class3Instance .
                    ?Class3Instance a ex:Class3 .
                }
                FILTER (!bound(?Class3Instance))
            }
        ''' ;
        ] .
"""

data_file1 = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix ex:    <http://www.semanticweb.org/shacltest#> .

ex:has_relation rdf:type owl:ObjectProperty .

ex:Class1 rdf:type owl:Class .

ex:Class2 rdf:type owl:Class .

ex:Class3 rdf:type owl:Class .

ex:instance1Class1 rdf:type owl:NamedIndividual ,
                          ex:Class1 ;
                ex:has_relation ex:instance1Class2 ;
                ex:has_relation ex:instance2Class2 ;
                ex:has_relation ex:instance3Class2 .

ex:instance1Class2 rdf:type owl:NamedIndividual ,
                          ex:Class2 ;
                ex:has_relation ex:instance1Class3 .

ex:instance2Class2 rdf:type owl:NamedIndividual ,
                          ex:Class2 .

ex:instance3Class2 rdf:type owl:NamedIndividual ,
                          ex:Class2 .

ex:instance1Class3 rdf:type owl:NamedIndividual ,
                          ex:Class3 .
"""

data_file2 = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix ex:    <http://www.semanticweb.org/shacltest#> .

ex:has_relation rdf:type owl:ObjectProperty .

ex:Class1 rdf:type owl:Class .

ex:Class2 rdf:type owl:Class .

ex:Class3 rdf:type owl:Class .

ex:instance1Class1 rdf:type owl:NamedIndividual ,
                          ex:Class1 ;
                ex:has_relation ex:instance1Class2 ;
                ex:has_relation ex:instance2Class2 ;
                ex:has_relation ex:instance3Class2 .

ex:instance1Class2 rdf:type owl:NamedIndividual ,
                          ex:Class2 ;
                ex:has_relation ex:instance1Class3 .

ex:instance2Class2 rdf:type owl:NamedIndividual ,
                          ex:Class2 ;
                ex:has_relation ex:instance2Class3 .

ex:instance3Class2 rdf:type owl:NamedIndividual ,
                          ex:Class2 ;
                ex:has_relation ex:instance3Class3 .

ex:instance1Class3 rdf:type owl:NamedIndividual ,
                          ex:Class3 .

ex:instance2Class3 rdf:type owl:NamedIndividual ,
                          ex:Class3 .

ex:instance3Class3 rdf:type owl:NamedIndividual ,
                          ex:Class3 .
"""


def test_190_1() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file1, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")

    conforms, report, message = validate(data_g, shacl_graph=shapes, debug=False)
    result_list = []
    for s, p, o in report.triples((None, RDF.type, SH.ValidationResult)):
        result_list.append(s)

    assert len(result_list) == 2


def test_190_2() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file2, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")

    conforms, report, message = validate(data_g, shacl_graph=shapes, debug=False)
    result_list = []
    for s, p, o in report.triples((None, RDF.type, SH.ValidationResult)):
        result_list.append(s)

    assert conforms


if __name__ == "__main__":
    test_190_1()
    test_190_2()
