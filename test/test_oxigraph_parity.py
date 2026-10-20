# -*- coding: utf-8 -*-
"""\
Parity and performance regressions for validation against an Oxigraph-backed DataGraph.

1. Plain string literals coming back from Oxigraph carry an explicit xsd:string datatype
   (RDF 1.1). They must compare equal to the plain literals in the shapes graph, otherwise
   constraints such as sh:in and sh:hasValue report false violations.
2. Building a validation result must not compute len() of the whole data graph. The
   expressions `datagraph or sg` triggered DataGraph.__len__, which on Oxigraph is a
   COUNT query over the entire store, once per validation result.
"""

import pytest
from rdflib import XSD, Graph, Literal

import pyshacl
from pyshacl.graph_abstraction import has_oxigraph

pytestmark = pytest.mark.skipif(not has_oxigraph, reason="pyoxigraph is not installed")

SHAPES = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .

ex:OpShape a sh:NodeShape ;
    sh:targetClass ex:Comparison ;
    sh:property [
        sh:path ex:operator ;
        sh:in ( "=" "<" ">" ) ;
    ] ;
    sh:property [
        sh:path ex:kind ;
        sh:hasValue "atomic" ;
    ] .
"""

DATA = """\
@prefix ex: <http://example.org/> .

ex:c1 a ex:Comparison ; ex:operator "=" ; ex:kind "atomic" .
ex:c2 a ex:Comparison ; ex:operator "<" ; ex:kind "atomic" .
"""


def _ox_store(ttl: str):
    from pyoxigraph import RdfFormat, Store

    store = Store()
    store.bulk_load(ttl.encode("utf-8"), format=RdfFormat.TURTLE)
    return store


def test_plain_string_literals_match_shapes_on_oxigraph():
    shapes = Graph().parse(data=SHAPES, format="turtle")
    conforms_rdflib, _, _ = pyshacl.validate(
        Graph().parse(data=DATA, format="turtle"), shacl_graph=shapes
    )
    conforms_ox, _, text = pyshacl.validate(_ox_store(DATA), shacl_graph=shapes)
    assert conforms_rdflib
    assert conforms_ox, text


def test_to_rdf_maps_xsd_string_to_plain_literal():
    from pyoxigraph import Literal as OxLiteral
    from pyoxigraph import NamedNode as OxNamedNode

    from pyshacl.graph_abstraction import to_rdf

    converted = to_rdf(OxLiteral("="))
    assert converted == Literal("=")
    assert converted.datatype is None
    typed = to_rdf(OxLiteral("1", datatype=OxNamedNode(str(XSD.integer))))
    assert typed.datatype == XSD.integer


def test_validation_results_do_not_compute_data_graph_length(monkeypatch):
    from pyshacl import graph_abstraction

    calls = []
    original_len = graph_abstraction.OxigraphDataGraph.__len__

    def counting_len(self, *args, **kwargs):
        calls.append(1)
        return original_len(self, *args, **kwargs)

    monkeypatch.setattr(graph_abstraction.OxigraphDataGraph, "__len__", counting_len)
    shapes = Graph().parse(data=SHAPES, format="turtle")
    bad = DATA.replace('ex:operator "<"', 'ex:operator "!="')
    conforms, results, _ = pyshacl.validate(_ox_store(bad), shacl_graph=shapes)
    assert not conforms
    assert calls == []
