# -*- coding: utf-8 -*-
"""Regression tests for concurrent reuse of a preloaded shapes graph (#314)."""

import threading
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from rdflib import Dataset, Graph, Literal, Namespace
from rdflib.namespace import RDF

from pyshacl import validate
from pyshacl.shapes_graph import ShapesGraph

EX = Namespace('http://example.org/')

SHAPES = """\
@prefix ex: <http://example.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [ sh:path ex:name ; sh:minCount 1 ] .
"""


class WatchedGraph(Graph):
    """Expose overlapping writes to pySHACL's helper triples deterministically."""

    def __init__(self):
        super().__init__()
        self._monitor = False
        self._active = 0
        self._guard = threading.Lock()
        self.system_writes = 0

    def add(self, triple):
        if not self._monitor or triple not in ShapesGraph.system_triples:
            return super().add(triple)
        with self._guard:
            self._active += 1
            self.system_writes += 1
            overlapping = self._active > 1
        try:
            # Deliberately enlarge the race window so a missing synchronization
            # fails reliably instead of depending on the timing of rdflib internals.
            sleep(0.005)
            assert not overlapping, 'concurrent writes to a shared shapes graph'
            return super().add(triple)
        finally:
            with self._guard:
                self._active -= 1


def test_concurrent_validations_share_shapes_without_writing_concurrently():
    shapes = WatchedGraph().parse(data=SHAPES, format='turtle')
    shapes._monitor = True
    start = threading.Barrier(8)

    def check(_index):
        data = Graph()
        data.add((EX.person, EX.name, Literal('Alice')))
        # Every request has its own data graph; only shapes are shared.
        data.add((EX.person, RDF.type, EX.Person))
        start.wait()
        conforms, _, _ = validate(data, shacl_graph=shapes)
        return conforms

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert all(pool.map(check, range(8)))

    # Each system triple is only written once despite eight constructors.
    assert shapes.system_writes == len(ShapesGraph.system_triples)
    assert all(triple in shapes for triple in ShapesGraph.system_triples)

    # Subsequent calls must not write the same triples again.
    data = Graph()
    data.add((EX.person, RDF.type, EX.Person))
    data.add((EX.person, EX.name, Literal('Alice')))
    assert validate(data, shacl_graph=shapes)[0]
    assert shapes.system_writes == len(ShapesGraph.system_triples)


def test_preloaded_helper_triples_are_not_reinserted():
    shapes = WatchedGraph().parse(data=SHAPES, format='turtle')
    for triple in ShapesGraph.system_triples:
        shapes.add(triple)
    shapes._monitor = True

    for _ in range(10):
        ShapesGraph(shapes)

    assert shapes.system_writes == 0


def test_dataset_uses_default_graph_without_modifying_named_graphs():
    shapes = Dataset()
    named = shapes.graph(EX.shapes)
    named.parse(data=SHAPES, format='turtle')
    before = set(named)

    ShapesGraph(shapes)

    assert all(triple in shapes.default_graph for triple in ShapesGraph.system_triples)
    assert set(named) == before
