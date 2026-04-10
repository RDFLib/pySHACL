# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/316
"""

import warnings

import rdflib

from pyshacl import validate

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

DATA_TTL = """\
@prefix ex: <http://example.com/> .

ex:node1 a ex:Thing .
"""


def test_316_dataset_validation_avoids_rdflib_deprecations() -> None:
    data_graph = rdflib.Dataset()
    data_graph.default_graph.parse(data=DATA_TTL, format="turtle")

    shapes_graph = rdflib.Dataset()
    shapes_graph.default_graph.parse(data=SHAPES_TTL, format="turtle")

    with warnings.catch_warnings(record=True) as warning_context:
        warnings.simplefilter("always")
        conforms, _report_graph, _report_text = validate(data_graph, shacl_graph=shapes_graph)

    assert conforms is False
    pyshacl_deprecations = [
        (str(w.message), w.filename)
        for w in warning_context
        if issubclass(w.category, DeprecationWarning)
        and (
            "Dataset.default_context is deprecated" in str(w.message)
            or "Dataset.identifier is deprecated" in str(w.message)
        )
        and "/pyshacl/" in w.filename.lower()
        and "/site-packages/" not in w.filename.lower()
    ]
    assert pyshacl_deprecations == []
