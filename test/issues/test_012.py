# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/12
"""
from pyshacl import validate

shacl_file_text = """
@prefix hei: <http://hei.org/customer/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

hei:HeiAddressShape a sh:NodeShape ;
    sh:property [ rdfs:comment "Street constraint" ;
            sh:datatype xsd:string ;
            sh:minLength 30 ;
            sh:path hei:Ship_to_street ] ;
    sh:targetClass hei:Hei_customer .
"""

data_file_text = """
@prefix hei: <http://hei.org/customer/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
hei:hei_cust_1281 a hei:Hei_customer ;
    rdfs:label "XYZHorecagroothandel" ;
    hei:Klant_nummer 1281 ;
    hei:Ship_to_City "Middenmeer" ;
    hei:Ship_to_postcode "1799 AB" ;
    hei:Ship_to_street "Industrieweg" .
"""

def test_012_text():
    res = validate(data_file_text, shacl_graph=shacl_file_text,
                   data_graph_format='turtle', shacl_graph_format='turtle',
                   inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms

def test_012_graph():
    from rdflib import Graph
    g = Graph()
    g.parse(data=data_file_text, format='turtle')
    sg = Graph()
    sg.parse(data=shacl_file_text, format='turtle')
    res = validate(g, shacl_graph=sg, inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms
