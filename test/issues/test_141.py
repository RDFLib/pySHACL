# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/141
"""

import rdflib

from pyshacl import validate


shacl_file = r"""@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix ex: <http://example.org/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:Dog
	a owl:Class , sh:NodeShape ;
	sh:property [
		a sh:PropertyShape ;
		sh:minCount 1 ;
		sh:nodeKind sh:BlankNodeOrIRI ;
		sh:path ex:hasIdentifier
	] ;
	sh:targetClass ex:Dog ;
	.

ex:Cat
	a owl:Class , sh:NodeShape	;
	sh:property [
		a sh:PropertyShape ;
		sh:minCount 1 ;
		sh:nodeKind sh:BlankNodeOrIRI ;
		sh:path ex:hasCharacteristic
	] ;
	sh:targetClass ex:Cat ;
	.

ex:hasIdentifier a owl:ObjectProperty ;
	.

ex:hasCharacteristic a owl:ObjectProperty ;
	.

ex:hasName a owl:ObjectProperty ;
	rdfs:subPropertyOf ex:hasIdentifier , ex:hasCharacteristic ;
	.

ex:hasLabel a owl:ObjectProperty ;
	rdfs:subPropertyOf ex:hasIdentifier ;
	.
"""


data_file = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .


ex:hasIdentifier a owl:ObjectProperty ;
	.

ex:hasCharacteristic a owl:ObjectProperty ;
	.

ex:hasName a owl:ObjectProperty ;
	rdfs:subPropertyOf ex:hasIdentifier , ex:hasCharacteristic ;
	.

ex:hasLabel a owl:ObjectProperty ;
	rdfs:subPropertyOf ex:hasIdentifier ;
	.

kb:dog_with_identifier
	a ex:Dog ;
	rdfs:comment "PASS" ;
	ex:hasIdentifier kb:dogidentifier1 ;
	.

kb:dog_with_name
	a ex:Dog ;
	rdfs:comment "PASS" ;
	ex:hasName [ rdf:value "Rover" ] ;
	.

kb:dog_with_characteristic
	a ex:Dog ;
	rdfs:comment "XFAIL" ;
	ex:hasCharacteristic [ rdf:value "Brown" ] ;
	.

kb:cat_with_identifier
	a ex:Cat ;
	rdfs:comment "XFAIL" ;
	ex:hasIdentifier kb:catidentifier1 ;
	.

kb:cat_with_name
	a ex:Cat ;
	rdfs:comment "PASS" ;
	ex:hasName [ rdf:value "Mittens" ] ;
	.

kb:cat_with_characteristic
	a ex:Cat ;
	rdfs:comment "PASS" ;
	ex:hasCharacteristic [ rdf:value "Green" ] ;
	.

kb:dog_with_label
	a ex:Dog ;
	rdfs:comment "PASS" ;
	ex:hasLabel [ rdf:value "Dopey" ] ;
	.
"""


def test_me() -> None:
    my_json = """\
    {
  "@context": {
    "@vocab": "http://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "MonetaryAmount",
  "value": {
    "@type": "xsd:float",
    "@value": "100000"
  }
}
    """
    shapes_json = """\
    {
  "@context": {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "prov": "http://www.w3.org/ns/prov#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "sh": "http://www.w3.org/ns/shacl#",
    "shsh": "http://www.w3.org/ns/shacl-shacl#",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "http://schema.org/",
    "rescs": "http://rescs.org/"
  },
  "@graph": [
    {
      "@id": "rescs:dash/monetaryamount/MonetaryAmountShape",
      "@type": "sh:NodeShape",
      "rdfs:comment": {
        "@type": "xsd:string",
        "@value": "A monetary value or range. This type can be used to describe an amount of money such as $50 USD, or a range as in describing a bank account being suitable for a balance between £1,000 and £1,000,000 GBP, or the value of a salary, etc. It is recommended to use [[PriceSpecification]] Types to describe the price of an Offer, Invoice, etc."
      },
      "rdfs:label": {
        "@type": "xsd:string",
        "@value": "Monetary amount"
      },
      "sh:property": {
        "sh:datatype": {
          "@id": "xsd:float"
        },
        "sh:description": "The value of the quantitative value or property value node.\\\\n\\\\n* For [[QuantitativeValue]] and [[MonetaryAmount]], the recommended type for values is 'Number'.\\\\n* For [[PropertyValue]], it can be 'Text;', 'Number', 'Boolean', or 'StructuredValue'.\\\\n* Use values from 0123456789 (Unicode 'DIGIT ZERO' (U+0030) to 'DIGIT NINE' (U+0039)) rather than superficially similiar Unicode symbols.\\\\n* Use '.' (Unicode 'FULL STOP' (U+002E)) rather than ',' to indicate a decimal point. Avoid using these symbols as a readability separator.",
        "sh:maxCount": {
          "@type": "xsd:integer",
          "@value": 1
        },
        "sh:minCount": {
          "@type": "xsd:integer",
          "@value": 1
        },
        "sh:minExclusive": 0,
        "sh:name": "value",
        "sh:path": {
          "@id": "schema:value"
        }
      },
      "sh:targetClass": {
        "@id": "schema:MonetaryAmount"
      }
    }
  ]
}
    """
    g = rdflib.Graph()
    g.parse(data=shapes_json, format="json-ld")
    d = rdflib.Graph()
    d.parse(data=my_json, format="json-ld")
    validate(d, shacl_graph=g, debug=True)


def test_141() -> None:
    data = rdflib.Graph()
    data.parse(data=data_file, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    res = validate(
        data,
        shacl_graph=shapes,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        debug=True,
        inference="rdfs",
    )

    conforms, graph, string = res


if __name__ == "__main__":
    test_141()
