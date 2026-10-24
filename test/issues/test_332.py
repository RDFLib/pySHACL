"""Regression tests for https://github.com/RDFLib/pySHACL/issues/332."""

import pytest
from rdflib import RDF, RDFS, SH, Dataset, Graph, Literal, Namespace

from pyshacl import validate
from pyshacl import validator as validator_module
from pyshacl.graph_abstraction import DataGraph
from pyshacl.validator import Validator

EX = Namespace("urn:ex#")


@pytest.mark.parametrize("dataset", [False, True], ids=["graph", "dataset"])
@pytest.mark.parametrize("inplace", [False, True], ids=["clone", "inplace"])
@pytest.mark.parametrize("inference", ["none", "rdfs"])
@pytest.mark.parametrize("has_value", [False, True], ids=["missing-value", "has-value"])
@pytest.mark.parametrize("ontology_dataset", [False, True], ids=["ontology-graph", "ontology-dataset"])
def test_full_mixin_validation(monkeypatch, dataset, inplace, inference, has_value, ontology_dataset):
    monkeypatch.setattr(validator_module, "USE_FULL_MIXIN", True)
    data = Dataset() if dataset else Graph()
    data_graph = data.graph(EX.data) if dataset else data
    data_graph.add((EX.a, RDF.type, EX.C))
    if has_value:
        data_graph.add((EX.a, EX.value, Literal("present")))
    original = set(data.quads()) if dataset else set(data)
    ontology = Dataset() if ontology_dataset else Graph()
    ontology_graph = ontology.graph(EX.ontology) if ontology_dataset else ontology
    ontology_graph.add((EX.C, RDFS.subClassOf, EX.D))
    # Ordinary instance data must also be copied in full-mixin mode.
    ontology_graph.add((EX.source, EX.value, Literal("ontology")))
    shapes = Graph().parse(
        data="""
        @prefix ex: <urn:ex#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        ex:S a sh:NodeShape ; sh:targetClass ex:D ;
            sh:property [ sh:path ex:value ; sh:minCount 1 ] .
        """,
        format="turtle",
    )

    conforms, report, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, inference=inference, inplace=inplace)

    assert conforms is has_value
    if not conforms:
        assert set(report.objects(None, SH.focusNode)) == {EX.a}
        assert set(report.objects(None, SH.sourceConstraintComponent)) == {SH.MinCountConstraintComponent}
    if inplace:
        assert (EX.source, EX.value, Literal("ontology")) in data_graph
    else:
        assert (set(data.quads()) if dataset else set(data)) == original


@pytest.mark.parametrize("dataset", [False, True], ids=["graph", "dataset"])
@pytest.mark.parametrize("inplace", [False, True], ids=["clone", "inplace"])
def test_full_mixin_preserves_graph_abstraction(monkeypatch, dataset, inplace):
    monkeypatch.setattr(validator_module, "USE_FULL_MIXIN", True)
    data = Dataset() if dataset else Graph()
    data_graph = data.graph(EX.data) if dataset else data
    data_graph.add((EX.a, RDF.type, EX.C))
    ontology = Graph()
    ontology.add((EX.source, EX.value, Literal("ontology")))
    validator = Validator(
        DataGraph.from_rdflib(data), shacl_graph=Graph(), ont_graph=ontology, options={"inplace": inplace}
    )

    mixed = validator.mix_in_ontology()

    assert isinstance(mixed, DataGraph)
    assert mixed.is_multigraph() is dataset
    target = mixed.get_context(EX.data) if dataset else mixed
    assert (EX.a, RDF.type, EX.C) in target
    assert (EX.source, EX.value, Literal("ontology")) in target
    assert ((EX.source, EX.value, Literal("ontology")) in data_graph) is inplace
