# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/26
"""
from pyshacl import validate

shacl_file_text = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix : <http://example.com/issue/026#> .

:PersonShape a sh:NodeShape ;
    sh:property [ rdfs:comment "Person Name" ;
            sh:datatype xsd:string ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:minLength 1 ;
            sh:path foaf:name ] ;
    sh:targetClass foaf:Person .
"""

data_file_text_trig = """
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://example.org/foaf-graph> prov:generatedAtTime "2012-04-09T00:00:00"^^xsd:dateTime .

<http://example.org/foaf-graph> {
  <http://manu.sporny.org/about#manu> a foaf:Person;
     foaf:name "Manu Sporny";
     foaf:knows <https://greggkellogg.net/foaf#me> .

  <https://greggkellogg.net/foaf#me> a foaf:Person;
     foaf:name "";
     foaf:knows <http://manu.sporny.org/about#manu> .
     
  <https://greggkellogg.net/foaf#unknown> a foaf:Person;
     foaf:name "";
     foaf:knows <https://greggkellogg.net/foaf#me> .
}
"""

data_file_text_jsonld = """
{
  "@context": {
    "generatedAt": {
      "@id": "http://www.w3.org/ns/prov#generatedAtTime",
      "@type": "http://www.w3.org/2001/XMLSchema#dateTime"
    },
    "Person": "http://xmlns.com/foaf/0.1/Person",
    "name": "http://xmlns.com/foaf/0.1/name",
    "knows": {"@id": "http://xmlns.com/foaf/0.1/knows", "@type": "@id"}
  },
  "@id": "http://example.org/foaf-graph",
  "generatedAt": "2012-04-09T00:00:00",
  "@graph": [
    {
      "@id": "http://manu.sporny.org/about#manu",
      "@type": "Person",
      "name": "Manu Sporny",
      "knows": "https://greggkellogg.net/foaf#me"
    }, {
      "@id": "https://greggkellogg.net/foaf#me",
      "@type": "Person",
      "name": "",
      "knows": "http://manu.sporny.org/about#manu"
    }, {
      "@id": "https://greggkellogg.net/foaf#unknown",
      "@type": "Person",
      "knows": "https://greggkellogg.net/foaf#me"
    }
  ]
}
"""

def test_026_trig():
    res = validate(data_file_text_trig, shacl_graph=shacl_file_text,
                   data_graph_format='trig', shacl_graph_format='turtle',
                   inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms

def test_026_jsonld():
    res = validate(data_file_text_jsonld, shacl_graph=shacl_file_text,
                   data_graph_format='json-ld', shacl_graph_format='turtle',
                   inference='both', debug=True)
    conforms, graph, string = res
    assert not conforms


if __name__ == "__main__":
    test_026_trig()
    test_026_jsonld()
