# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/162
"""

import rdflib
from pyshacl import validate

shacl_file = """\
@prefix exShapes: <urn:exShapes#> .
@prefix exOnt: <urn:exOnt#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix schema: <http://schema.org/> .

exShapes:Example-shape
	a sh:NodeShape ;
	sh:targetClass exOnt:Dataset ;
	sh:property [ a sh:PropertyShape ;
		sh:maxCount "1"^^xsd:integer ;
		sh:minCount "1"^^xsd:integer ;
		sh:path dcat:contactPoint ;
		sh:qualifiedMaxCount 1;
		sh:qualifiedMinCount 1;
		sh:qualifiedValueShape [ a sh:NodeShape ;
			sh:class vcard:Contact ;
			sh:property [ a sh:PropertyShape ;
				sh:maxCount 1;
				sh:minCount 1;
				sh:path vcard:hasEmail ;
			] ,
			[ a sh:PropertyShape ;
				sh:maxCount 1;
				sh:path vcard:fn ;
			] ;
		] ;
	] .
"""

ont_file1 = """\
@prefix exOnt: <urn:exOnt#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:exOnt> a owl:Ontology .

exOnt:Dataset a owl:Class .

exOnt:contact-0
	a vcard:Contact ,
	 vcard:Individual ,
	 owl:NamedIndividual ;
	rdfs:comment "This named individual is provided as a stand-in default"@en ;
	vcard:fn "NOT ENCODED" ;
	vcard:hasEmail <mailto:null@example.org> .

exOnt:canBeNamed a owl:Class ;
    exOnt:mightHave exOnt:contact-0 .
"""

ont_file2 = """\
@prefix exOnt: <urn:exOnt#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:exOnt> a owl:Ontology .

exOnt:Dataset a owl:Class .

exOnt:contact-0
	a vcard:Contact ,
	 vcard:Individual ;
	rdfs:comment "This named individual is provided as a stand-in default"@en ;
	vcard:fn "NOT ENCODED" ;
	vcard:hasEmail <mailto:null@example.org> .
"""
data_file = """\
@prefix ex: <urn:ex#> .
@prefix exOnt: <urn:exOnt#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix schema: <http://schema.org/> .

ex:test_dataset a exOnt:Dataset ;
    dcat:contactPoint exOnt:contact-0 .
"""


def test_170() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file, format="turtle")
    ont_g = rdflib.Graph()
    ont_g.parse(data=ont_file1, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")

    conforms, report, message = validate(data_g, shacl_graph=shapes, ont_graph=ont_g, inference="rdfs", debug=False)
    assert conforms

    ont_g2 = rdflib.Graph()
    ont_g2.parse(data=ont_file2, format="turtle")
    conforms, report, message = validate(data_g, shacl_graph=shapes, ont_graph=ont_g2, inference="rdfs", debug=True)
    assert not conforms


shacl_file_sparql_prefixes = '''# baseURI: urn:exShapes
@prefix exShapes: <urn:exShapes#> .
@prefix exOnt: <urn:exOnt#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix schema: <http://schema.org/> .

<urn:exShapes>  rdf:type owl:Ontology ;
    sh:declare [
      rdf:type sh:PrefixDeclaration ;
      sh:namespace "http://www.w3.org/2006/vcard/ns#"^^xsd:anyURI ;
      sh:prefix "vcard" ;
    ] ;
    sh:declare [
      rdf:type sh:PrefixDeclaration ;
      sh:namespace "http://www.w3.org/ns/dcat#"^^xsd:anyURI ;
      sh:prefix "dcat" ;
    ] ;
    sh:declare [
      rdf:type sh:PrefixDeclaration ;
      sh:namespace "urn:exOnt#"^^xsd:anyURI ;
      sh:prefix "exOnt" ;
    ] ;
    .

exShapes:Example-shape
	a sh:NodeShape ;
	sh:targetClass exOnt:Dataset ;
  sh:sparql [
      rdfs:comment "Test using prefixes in sparql" ;
      sh:prefixes <urn:exShapes> ;
      sh:select """SELECT $this
WHERE {
	$this dcat:contactPoint ?c .
	FILTER NOT EXISTS {
		?c vcard:fn ?fn .
    }
}""" ;
    ] ;
    .
'''

def test_170_2() -> None:
    data_g = rdflib.Graph()
    data_g.parse(data=data_file, format="turtle")
    ont_g = rdflib.Graph()
    ont_g.parse(data=ont_file1, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file_sparql_prefixes, format="turtle")

    conforms, report, message = validate(data_g, shacl_graph=shapes, ont_graph=ont_g, inference="rdfs", debug=True)
    assert conforms
    ont_2 = rdflib.Graph()
    ont_2.parse(data=ont_file2, format="turtle")
    conforms, report, message = validate(data_g, shacl_graph=shapes, ont_graph=ont_2, inference="rdfs", debug=True)
    assert not conforms

shacl_file_no_sparql_prefixes = '''# baseURI: urn:exShapes
@prefix exShapes: <urn:exShapes#> .
@prefix exOnt: <urn:exOnt#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix schema: <http://schema.org/> .

<urn:exShapes>  rdf:type owl:Ontology .

exShapes:Example-shape
	a sh:NodeShape ;
	sh:targetClass exOnt:Dataset ;
  sh:sparql [
      rdfs:comment "Test using prefixes in sparql" ;
      sh:select """SELECT $this
WHERE {
	$this dcat:contactPoint ?c .
	FILTER NOT EXISTS {
		?c vcard:fn ?fn .
    }
}""" ;
    ] ;
    .
'''
def test_170_3() -> None:
    # The vcard prefix does not exist in the DataFile, only in the Ontology file.
    # It is defacto behaviour that PySHACL now copies any unknown prefixes from the ontology file into the data file.
    data_g = rdflib.Graph()
    data_g.parse(data=data_file, format="turtle")
    ont_g = rdflib.Graph()
    ont_g.parse(data=ont_file1, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file_no_sparql_prefixes, format="turtle")
    conforms, report, message = validate(data_g, shacl_graph=shapes, ont_graph=ont_g, inference="rdfs", debug=True)
    assert conforms
    ont_2 = rdflib.Graph()
    ont_2.parse(data=ont_file2, format="turtle")
    conforms, report, message = validate(data_g, shacl_graph=shapes, ont_graph=ont_2, inference="rdfs", debug=True)
    assert not conforms

if __name__ == "__main__":
    test_170()
    test_170_2()
    test_170_3()
