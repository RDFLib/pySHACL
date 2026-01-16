# -*- coding: utf-8 -*-
#
import pyshacl

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.com/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:ThingShape a sh:NodeShape ;
    sh:targetClass ex:Thing ;
    sh:property [
        sh:path ex:prop ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] .
"""

DATA_GRAPH_OK = """\
@prefix ex: <http://example.com/> .

ex:node1 a ex:Thing ;
    ex:prop "ok" .
"""

DATA_GRAPH_BAD = """\
@prefix ex: <http://example.com/> .

ex:node2 a ex:Thing .
"""


def test_validate_combine_multiple_graphs():
    conforms, results_graph, results_text = pyshacl.validate(
        [DATA_GRAPH_OK, DATA_GRAPH_BAD],
        shacl_graph=SHAPES_TTL,
    )
    assert not conforms
    assert isinstance(results_text, str)


def test_validate_each_multiple_graphs():
    results = pyshacl.validate_each(
        [DATA_GRAPH_OK, DATA_GRAPH_BAD],
        shacl_graph=SHAPES_TTL,
    )
    assert len(results) == 2
    assert results[DATA_GRAPH_OK][0] is True
    assert results[DATA_GRAPH_BAD][0] is False

def test_validate_each_multiple_graphs_via_mode():
    results = pyshacl.validate(
        [DATA_GRAPH_OK, DATA_GRAPH_BAD],
        shacl_graph=SHAPES_TTL,
        multi_data_graphs_mode="validate_each",
    )
    assert len(results) == 2
    assert results[DATA_GRAPH_OK][0] is True
    assert results[DATA_GRAPH_BAD][0] is False
