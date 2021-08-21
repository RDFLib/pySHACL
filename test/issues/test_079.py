# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/79
"""
import rdflib
import pyshacl
shapes_data = """\
@prefix ex: <https://example.com#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:AAA a owl:Class.
ex:BBB a owl:Class.
ex:CCC a owl:Class.

ex:Shape a sh:NodeShape ;
  sh:targetClass ex:AAA;
  sh:not [
    sh:or (
      [sh:class ex:BBB]
      [sh:class ex:CCC]
    )
  ].
"""


def test_079():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data="""
    @prefix ex: <https://example.com#> .

    ex:aaa a ex:AAA.
    ex:aaa a ex:BBB.
    ex:aaa a ex:CCC.
    """, format='turtle')

    conforms, results_graph, results_text = pyshacl.validate(
        data_g, shacl_graph=shape_g, debug=True,
    )
    assert not conforms


if __name__ == "__main__":
    exit(test_079())
