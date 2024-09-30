# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/227
"""
import sys

import rdflib

import pyshacl

shapes_data = '''\
@prefix ex-sh-rl: <http://otl.example.eu/ex/def/shape-rule/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .


ex-sh-rl:bothOrsAtOnce a sh:NodeShape ;
	sh:targetClass rdfs:Class ;
	sh:message "Wrong because neither object of sh:class or subject of sh:property" ;
	sh:or
		(
			[

				sh:path ( [ sh:inversePath [ sh:zeroOrMorePath rdfs:subClassOf ] ] sh:property ) ;
				sh:minCount 1 ;
			]
			[
				sh:path ( [ sh:inversePath [ sh:zeroOrMorePath rdfs:subClassOf ] ] [sh:inversePath sh:class ] ) ;
				sh:minCount 1 ;
			]
		) .



ex-sh-rl:Or1 a sh:NodeShape ;
	sh:targetClass rdfs:Class ;
	sh:message "Wrong because not subject sh:property" ;
	sh:property [
		sh:path ( [ sh:inversePath [ sh:zeroOrMorePath rdfs:subClassOf ] ] sh:property ) ;
				sh:minCount 1 ;
	].

ex-sh-rl:Or2 a sh:NodeShape ;
	sh:targetClass rdfs:Class ;
	sh:message "Wrong because not object of sh:class" ;
	sh:property [
				sh:path ( [ sh:inversePath [ sh:zeroOrMorePath rdfs:subClassOf ] ] [sh:inversePath sh:class ] ) ;
				sh:minCount 1 ;
			]
		.
'''

data_g_text = '''\
@prefix ex-sh-rl: <http://otl.example.eu/ex/def/shape-rule/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .


ex-sh-rl:CorrectSuperClass a rdfs:Class.
ex-sh-rl:CorrectClass a rdfs:Class ;
	rdfs:subClassOf ex-sh-rl:CorrectSuperClass.

ex-sh-rl:something sh:class ex-sh-rl:CorrectClass.

ex-sh-rl:WrongClass a rdfs:Class .
'''


def test_227():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shape_g,
        debug=True,
        inference='none',
        advanced=False,
        meta_shacl=False,
    )
    assert not conforms


if __name__ == "__main__":
    sys.exit(test_227())
