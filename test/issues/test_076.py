# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/76
"""
import rdflib

from pyshacl import validate


shacl_file_text = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix : <http://example.com/issue/076#> .

<http://example.com/issue/076>
  rdf:type owl:Ontology ;
  owl:sameAs : .

<http://example.com/issue/076#>
  rdf:type owl:Ontology ;
  owl:imports <http://datashapes.org/dash> ;
  sh:declare [
    sh:prefix "skos_p" ;
    sh:namespace "http://www.w3.org/2004/02/skos/core#"^^xsd:anyURI ;
    ] ;
  sh:declare [
    sh:prefix "" ;
    sh:namespace "http://example.com/issue/076#"^^xsd:anyURI ;
    ] .

:TopConceptRule
	a sh:NodeShape ;
	sh:property [
		sh:path skos:topConceptOf ;
		sh:minCount 1 ;
	] .

:DepthRule
	a sh:NodeShape ;
	sh:targetClass skos:Concept ;
	sh:rule [
		a sh:SPARQLRule ;
		sh:prefixes : ;
		sh:order 1 ;
		sh:condition :TopConceptRule ;
		sh:construct """
		    CONSTRUCT {
				$this :hasDepth 0 .
			}
			WHERE {
			}
		""" ;
	] ;
	sh:rule [
		a sh:SPARQLRule ;
		sh:prefixes : ;
		sh:order 2 ;
		sh:construct """
		    CONSTRUCT {
				$this :hasDepth ?plusOne .
			}
			WHERE {
				$this skos_p:broader ?parent .
				?parent :hasDepth ?depth .
				bind(?depth + 1 as ?plusOne)
			}
		""" ;
	] .
'''

data_file_text = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com#> .

ex:animalsVocabulary rdf:type skos:ConceptScheme;
  dct:title "Animals Vocabulary"@en;
  skos:hasTopConcept ex:animals .

ex:animals rdf:type skos:Concept;
  skos:prefLabel "animals"@en;
  skos:inScheme ex:animalsVocabulary;
  skos:topConceptOf ex:animalsVocabulary .

ex:cat rdf:type skos:Concept;
  skos:prefLabel "cat"@en;
  skos:broader ex:animals ;
  skos:inScheme ex:animalsVocabulary.

ex:wildcat a skos:Concept;
  skos:inScheme ex:animalsVocabulary;
  skos:broader ex:cat .

ex:europeanWildcat a skos:Concept;
  skos:inScheme ex:animalsVocabulary;
  skos:broader ex:wildcat .
"""


def test_076_positive():
    data = rdflib.Graph()
    data.parse(data=data_file_text, format="turtle")
    res = validate(
        data,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        inference='rdfs',
        inplace=True,
        advanced=True,
        iterate_rules=True,
        debug=True,
    )
    conforms, graph, string = res
    find_s = rdflib.URIRef("http://example.com#europeanWildcat")
    find_p = rdflib.URIRef("http://example.com/issue/076#hasDepth")
    find_o = rdflib.Literal(3)
    assert (find_s, find_p, find_o) in data


def test_076_negative():
    data = rdflib.Graph()
    data.parse(data=data_file_text, format="turtle")
    res = validate(
        data,
        shacl_graph=shacl_file_text,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        inference='rdfs',
        inplace=True,
        advanced=True,
        iterate_rules=False,
        debug=True,
    )
    conforms, graph, string = res
    find_s = rdflib.URIRef("http://example.com#europeanWildcat")
    find_p = rdflib.URIRef("http://example.com/issue/076#hasDepth")
    find_o = rdflib.Literal(3)
    assert (find_s, find_p, find_o) not in data


if __name__ == "__main__":
    test_076_positive()
    test_076_negative()
