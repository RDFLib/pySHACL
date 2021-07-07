from pyshacl import validate
from io import BytesIO

"""
https://github.com/RDFLib/pySHACL/issues/62
"""

data = b"""\
{
  "@context": {
    "ex": "http://example.com/ex#",
    "exOnt": "http://example.com/exOnt#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@graph": [
    {
      "@id": "ex:Pet1",
      "@type": "exOnt:Lizard",
      "exOnt:nLegs": 4,
      "rdf:label": "Sebastian"
    },
    {
      "@id": "ex:Human1",
      "@type": "exOnt:Human",
      "exOnt:hasPet": {
        "@id": "ex:Pet1"
      },
      "exOnt:nLegs": 2,
      "rdf:label": "Amy"
    }
  ]
}
"""

ont_data = b"""\
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
    rdfs:range exOnt:integer .

exOnt:Lizard a rdfs:Class ;
    rdfs:subClassOf exOnt:Pet .
"""

shacl_data = b"""\
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

def test_062():
    data_fp = BytesIO(data)
    shacl_fp = BytesIO(shacl_data)
    ont_fp = BytesIO(ont_data)
    try:
        conforms, g, s = validate(data_fp, shacl_graph=shacl_fp, ont_graph=ont_fp, data_graph_format="json-ld",
                                  shacl_graph_format="turtle", ont_graph_format="turtle", abort_on_first=False,
                                  meta_shacl=False, debug=True, advanced=True)
    except Exception as e:
        print(e)
        raise
    assert conforms

if __name__ == "__main__":
    test_062()
