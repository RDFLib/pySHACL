from pyshacl import validate

data_graph = """\
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:pyshacl:datagraph> {
   <http://example.org/s1> a <http://example.org/class/1> .
   <http://example.org/s1> <http://example.org/p0> "zero"^^<http://example.org/datatypes/one> .
   <http://example.org/s1> <http://example.org/p1> "one"^^xsd:string .
   <http://example.org/s1> <http://example.org/p2> "two"@en .
   <http://example.org/s1> <http://example.org/p2> 3 .
   <http://example.org/s1> <http://example.org/p3> "4"^^<http://example.org/another/type1> .
   <http://example.org/s2> a <http://example.org/class/2> .
   <http://example.org/s2> <http://example.org/p4> "five"^^<http://example.org/another/type2> .
}"""


shapes_graph = '''\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:pyshacl:shapes> {
    <urn:pyshacl:shapesOnt> a owl:Ontology ;
        sh:declare [
            sh:prefix "ex" ;
            sh:namespace "http://example.org/"^^xsd:anyURI ;
        ] ;
        sh:declare [
            sh:prefix "geo" ;
            sh:namespace "http://www.opengis.net/ont/geosparql#"^^xsd:anyURI ;
        ] ;
        sh:declare [
            sh:prefix "my-dt" ;
            sh:namespace "http://example.org/datatypes/"^^xsd:anyURI ;
        ] .

    <http://example.org/shapes/1> a sh:NodeShape ;
        sh:targetClass <http://example.org/class/1> , <http://example.org/class/2> ;
        sh:sparql [
            sh:prefixes <urn:pyshacl:shapesOnt> ;
            sh:select """
            SELECT DISTINCT $this ?value WHERE {
                {
                    SELECT $this ?value WHERE {
                        $this ?_p ?o .
                        FILTER (isLITERAL(?o))
                        BIND(DATATYPE(?o) as ?value)
                    }
                }
                FILTER(
                    !(
                        STRSTARTS(STR(?value), STR(xsd:)) ||
                        STRSTARTS(STR(?value), STR(rdf:)) ||
                        STRSTARTS(STR(?value), STR(my-dt:)) ||
                        STRSTARTS(STR(?value), STR(geo:))
                    )
                )
            }
            """ ;
        ] ;
        sh:message "Datatype must be from the Datatypes Namespace" .
}
'''

conforms, result_graph, result_text = \
    validate(data_graph, data_graph_format="trig", shacl_graph=shapes_graph, shacl_graph_format="trig")
print(result_text)
