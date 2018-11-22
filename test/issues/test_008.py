# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/8
"""
from pyshacl import validate

mixed_file_text = '''
# baseURI: http://semanticprocess.x10host.com/Ontology/Testsparql
# imports: http://datashapes.org/dash
# prefix: Testsparql

@prefix Testsparql: <http://semanticprocess.x10host.com/Ontology/Testsparql#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://semanticprocess.x10host.com/Ontology/Testsparql>
  rdf:type owl:Ontology ;
  owl:imports <http://datashapes.org/dash> ;
  owl:versionInfo "Created with TopBraid Composer" ;
  sh:declare Testsparql:PrefixDeclaration ;
.
Testsparql:Crane
  rdf:type rdfs:Class ;
  rdfs:subClassOf owl:Class ;
.
Testsparql:Crane_1
  rdf:type Testsparql:Crane ;
  Testsparql:Cranecapacity "500"^^xsd:decimal ;
.
Testsparql:Crane_2
  rdf:type Testsparql:Crane ;
  Testsparql:Cranecapacity "5000"^^xsd:decimal ;
.
Testsparql:Cranecapacity
  rdf:type owl:DatatypeProperty ;
  rdfs:domain Testsparql:Crane ;
  rdfs:range xsd:decimal ;
  rdfs:subPropertyOf owl:topDataProperty ;
.
Testsparql:Module
  rdf:type rdfs:Class ;
  rdfs:subClassOf owl:Class ;
.
Testsparql:Module_1
  rdf:type Testsparql:Module ;
  Testsparql:Moduleweight "800"^^xsd:decimal ;
.
Testsparql:Moduleweight
  rdf:type owl:DatatypeProperty ;
  rdfs:domain Testsparql:Module ;
  rdfs:range xsd:decimal ;
  rdfs:subPropertyOf owl:topDataProperty ;
.
Testsparql:PrefixDeclaration
  rdf:type sh:PrefixDeclaration ;
  sh:namespace "http://semanticprocess.x10host.com/Ontology/Testsparql#"^^xsd:anyURI ;
  sh:prefix "Testsparql" ;
.
Testsparql:Process
  rdf:type rdfs:Class ;
  rdf:type sh:NodeShape ;
  rdfs:subClassOf owl:Class ;
  sh:sparql [
      sh:message "Invalid process" ;
      sh:prefixes <http://semanticprocess.x10host.com/Ontology/Testsparql> ;
      sh:select """SELECT $this 
        WHERE {
			 $this  rdf:type Testsparql:Process.
			$this Testsparql:hasResource ?crane.
			$this Testsparql:hasAssociation ?module.
			?crane Testsparql:Cranecapacity ?cc.
			?module Testsparql:Moduleweight ?mw.
					FILTER (?cc <= ?mw).

     }""" ;
    ] ;
.
Testsparql:ProcessID
  rdf:type owl:DatatypeProperty ;
  rdfs:domain Testsparql:Process ;
  rdfs:range xsd:string ;
  rdfs:subPropertyOf owl:topDataProperty ;
.
Testsparql:Process_1
  rdf:type Testsparql:Process ;
  Testsparql:ProcessID "P1" ;
  Testsparql:hasAssociation Testsparql:Module_1 ;
  Testsparql:hasResource Testsparql:Crane_1 ;
.
Testsparql:Process_2
  rdf:type Testsparql:Process ;
  Testsparql:ProcessID "P2" ;
  Testsparql:hasAssociation Testsparql:Module_1 ;
  Testsparql:hasResource Testsparql:Crane_2 ;
.
Testsparql:hasAssociation
  rdf:type owl:ObjectProperty ;
  rdfs:domain Testsparql:Process ;
  rdfs:range Testsparql:Module ;
  rdfs:subPropertyOf owl:topObjectProperty ;
.
Testsparql:hasResource
  rdf:type owl:ObjectProperty ;
  rdfs:domain Testsparql:Process ;
  rdfs:range Testsparql:Crane ;
  rdfs:subPropertyOf owl:topObjectProperty ;
.

'''

shacl_file_text = '''
@prefix Testsparql: <http://semanticprocess.x10host.com/Ontology/Testsparql#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://semanticprocess.x10host.com/Ontology/Testsparql>
  rdf:type owl:Ontology ;
  owl:imports <http://datashapes.org/dash> ;
  owl:versionInfo "Created with TopBraid Composer" ;
  sh:declare Testsparql:PrefixDeclaration ;
.

Testsparql:PrefixDeclaration
  rdf:type sh:PrefixDeclaration ;
  sh:namespace "http://semanticprocess.x10host.com/Ontology/Testsparql#"^^xsd:anyURI ;
  sh:prefix "Testsparql" ;
.

Testsparql:Process
  rdf:type rdfs:Class ;
  rdf:type sh:NodeShape ;
  rdfs:subClassOf owl:Class ;
  sh:sparql [
      sh:message "Invalid process" ;
      sh:prefixes <http://semanticprocess.x10host.com/Ontology/Testsparql> ;
      sh:select """SELECT $this 
        WHERE {
			$this  rdf:type Testsparql:Process.
			$this Testsparql:hasResource ?crane.
			$this Testsparql:hasAssociation ?module.
			?crane Testsparql:Cranecapacity ?cc.
			?module Testsparql:Moduleweight ?mw.
					FILTER (?cc <= ?mw).

     }""" ;
    ] ;
.
'''

data_file_text = '''
@prefix Testsparql: <http://semanticprocess.x10host.com/Ontology/Testsparql#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

Testsparql:Crane
  rdf:type rdfs:Class ;
  rdfs:subClassOf owl:Class ;
.
Testsparql:Crane_1
  rdf:type Testsparql:Crane ;
  Testsparql:Cranecapacity "500"^^xsd:decimal ;
.
Testsparql:Crane_2
  rdf:type Testsparql:Crane ;
  Testsparql:Cranecapacity "5000"^^xsd:decimal ;
.
Testsparql:Cranecapacity
  rdf:type owl:DatatypeProperty ;
  rdfs:domain Testsparql:Crane ;
  rdfs:range xsd:decimal ;
  rdfs:subPropertyOf owl:topDataProperty ;
.
Testsparql:Module
  rdf:type rdfs:Class ;
  rdfs:subClassOf owl:Class ;
.
Testsparql:Module_1
  rdf:type Testsparql:Module ;
  Testsparql:Moduleweight "800"^^xsd:decimal ;
.
Testsparql:Moduleweight
  rdf:type owl:DatatypeProperty ;
  rdfs:domain Testsparql:Module ;
  rdfs:range xsd:decimal ;
  rdfs:subPropertyOf owl:topDataProperty ;

.
Testsparql:Process
  rdf:type rdfs:Class ;
  
  rdfs:subClassOf owl:Class ;
  .
Testsparql:ProcessID
  rdf:type owl:DatatypeProperty ;
  rdfs:domain Testsparql:Process ;
  rdfs:range xsd:string ;
  rdfs:subPropertyOf owl:topDataProperty ;
.
Testsparql:Process_1
  rdf:type Testsparql:Process ;
  Testsparql:ProcessID "P1" ;
  Testsparql:hasAssociation Testsparql:Module_1 ;
  Testsparql:hasResource Testsparql:Crane_1 ;
.
Testsparql:Process_2
  rdf:type Testsparql:Process ;
  Testsparql:ProcessID "P2" ;
  Testsparql:hasAssociation Testsparql:Module_1 ;
  Testsparql:hasResource Testsparql:Crane_2 ;
.
Testsparql:hasAssociation
  rdf:type owl:ObjectProperty ;
  rdfs:domain Testsparql:Process ;
  rdfs:range Testsparql:Module ;
  rdfs:subPropertyOf owl:topObjectProperty ;
.
Testsparql:hasResource
  rdf:type owl:ObjectProperty ;
  rdfs:domain Testsparql:Process ;
  rdfs:range Testsparql:Crane ;
  rdfs:subPropertyOf owl:topObjectProperty ;
.
'''

def test_008():
    res1 = validate(mixed_file_text, data_graph_format='turtle', shacl_graph_format='turtle', inference='both', debug=True)
    conforms, graph, string = res1
    assert not conforms
    res2 = validate(data_file_text, shacl_graph=shacl_file_text, data_graph_format='turtle', shacl_graph_format='turtle', inference='both', debug=True)
    conforms, graph, string = res2
    assert not conforms

