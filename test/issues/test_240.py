# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/240
"""
import sys

import rdflib

import pyshacl

shapes_data = '''\
@prefix dash: <http://datashapes.org/dash#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/ns#> .

schema:PersonShape
    a sh:NodeShape ;
    sh:targetClass schema:Family;
sh:property schema:family-familyname.

schema:family-familyname
        rdf:type     sh:PropertyShape ;
        sh:path      schema:CorrectfamilyName ;
        sh:name      "familyname" ;
        sh:sparql    schema:onefamilyname ;
        sh:nodeKind  sh:Literal .

schema:onefamilyname
        rdfs:label  "onefamilyname " ;
        rdf:type    sh:SPARQLConstraint ;
        sh:message  "{?this} {?person}" ;
        sh:select   """prefix dash: <http://datashapes.org/dash#>
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix schema: <http://schema.org/>
        prefix sh: <http://www.w3.org/ns/shacl#>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        prefix ex: <http://example.org/ns#>

        SELECT ?this ?person
        WHERE {
          ?this a schema:Family.
          ?person schema:family ?this.
        }""" .

'''

data_g_text = '''\
@prefix ex: <http://example.org/ns#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Bob
    a schema:Person ;
    schema:givenName "Robert" ;
    schema:familyName "Junior" ;
	schema:family ex:JuniorFamily .

ex:Molly
    a schema:Person ;
    schema:givenName "Molly" ;
    schema:familyName "Junior2" ;
	schema:family ex:JuniorFamily .

ex:John
    a schema:Person ;
    schema:givenName "John" ;
    schema:familyName "Junior3" ;
	schema:family ex:JuniorFamily .


ex:JuniorFamily
	a schema:Family;
	schema:CorrectfamilyName "Junior" .
'''


def test_240():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shape_g,
        debug=True,
        inference='none',
        advanced=True,
        meta_shacl=False,
    )
    assert not conforms
    assert "Results (3)" in results_text


if __name__ == "__main__":
    sys.exit(test_240())
