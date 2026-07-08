# -*- coding: utf-8 -*-
"""\
Tests for SHACL Rules (SPARQLRule, TripleRule) with an Oxigraph-backed DataGraph.

These tests reuse the DASH rule test cases from test/resources/dash_tests/rules/
and load the target data graph into a pyoxigraph Store so that pySHACL wraps it
in the OxigraphDataGraph proxy and exercises the Oxigraph code paths for rules.
"""

import glob
from os import path, walk

import pytest
from rdflib import RDF, URIRef

import pyshacl
from pyshacl.errors import ReportableRuntimeError
from pyshacl.graph_abstraction import DataGraph, has_oxigraph

pytestmark = pytest.mark.skipif(not has_oxigraph, reason="pyoxigraph is not installed")

here_dir = path.abspath(path.dirname(__file__))
dash_files_dir = path.join(here_dir, "resources", "dash_tests")

# RDFS pre-inferencing via owlrl on an Oxigraph store is not used here; the DASH rule
# test cases pass with inference='none' (see test_dash_validate.py parity).
ALLOWABLE_NOT_IMPLEMENTED = []
ALLOWABLE_FAILURES = ["/rules/triple/person2schema.test.ttl"]


def load_oxigraph_store_from_file(file_path: str):
    from pyoxigraph import RdfFormat, Store

    store = Store()
    with open(file_path, "rb") as f:
        store.bulk_load(f.read(), format=RdfFormat.TURTLE)
    return store


cmdline_files_dir = path.join(here_dir, "resources", "cmdline_tests")
rules_runner_data_file = path.join(cmdline_files_dir, "rules_d.ttl")
rules_runner_shacl_file = path.join(cmdline_files_dir, "rules_s.ttl")


dash_sparql_rules_files = []
for x in walk(path.join(dash_files_dir, "rules", "sparql")):
    for y in glob.glob(path.join(x[0], "*.test.ttl")):
        dash_sparql_rules_files.append((y, None))


@pytest.mark.parametrize("data_file, shacl_file", dash_sparql_rules_files)
def test_sparql_rules_oxigraph(data_file, shacl_file):
    """Run DASH SPARQLRule tests with the data graph backed by an Oxigraph store."""
    data_store = load_oxigraph_store_from_file(data_file)
    try:
        val, _, v_text = pyshacl.validate(
            data_store,
            shacl_graph=shacl_file or data_file,
            advanced=True,
            inference="none",
            check_dash_result=True,
            debug=True,
            meta_shacl=False,
        )
    except (NotImplementedError, ReportableRuntimeError) as e:
        import traceback

        print(e)
        traceback.print_tb(e.__traceback__)
        val = False
        v_text = ""
    assert val
    print(v_text)


dash_triple_rules_files = []
for x in walk(path.join(dash_files_dir, "rules", "triple")):
    for y in glob.glob(path.join(x[0], "*.test.ttl")):
        if "person2schema.test.ttl" in y:
            data_file = y.replace("person2schema.test.ttl", "person.ttl")
            dash_triple_rules_files.append((data_file, y))
        else:
            dash_triple_rules_files.append((y, None))


@pytest.mark.parametrize("data_file, shacl_file", dash_triple_rules_files)
def test_triple_rules_oxigraph(data_file, shacl_file):
    """Run DASH TripleRule tests with the data graph backed by an Oxigraph store."""
    test_name = shacl_file or data_file
    data_store = load_oxigraph_store_from_file(data_file)
    try:
        val, _, v_text = pyshacl.validate(
            data_store,
            shacl_graph=shacl_file or data_file,
            advanced=True,
            inference="none",
            check_dash_result=True,
            debug=True,
            meta_shacl=False,
        )
    except NotImplementedError as ne:
        for ani in ALLOWABLE_NOT_IMPLEMENTED:
            if test_name.endswith(ani):
                v_text = "Skipping not implemented feature in test: {}".format(test_name)
                print(v_text)
                val = True
                break
        else:
            print(ne)
            val = False
            v_text = ""
    except ReportableRuntimeError as e:
        import traceback

        print(e)
        traceback.print_tb(e.__traceback__)
        val = False
        v_text = ""
    try:
        assert val
    except AssertionError as ae:
        for af in ALLOWABLE_FAILURES:
            if test_name.endswith(af):
                v_text = "Allowing failure in test: {}".format(test_name)
                print(v_text)
                break
        else:
            raise ae

    print(v_text)


def test_rules_runner_oxigraph():
    """Run shacl_rules() with an Oxigraph-backed data graph (TripleRule + expressions)."""
    data_store = load_oxigraph_store_from_file(rules_runner_data_file)
    output_g = pyshacl.shacl_rules(
        data_store, shacl_graph=rules_runner_shacl_file, advanced=True, debug=False
    )
    person_classes = set(
        output_g.objects(
            URIRef("http://datashapes.org/shasf/tests/expression/rules.test.data#Jenny"),
            predicate=RDF.type,
        )
    )
    assert URIRef("http://datashapes.org/shasf/tests/expression/rules.test.ont#Administrator") in person_classes
    assert URIRef("http://datashapes.org/shasf/tests/expression/rules.test.ont#Person") in person_classes


def test_oxigraph_data_graph_wrapper_used():
    """Confirm that passing an ox.Store yields an OxigraphDataGraph wrapper."""
    from pyoxigraph import Store

    store = Store()
    dg = DataGraph.from_oxigraph_store(store)
    assert dg.is_oxigraph is True
    assert type(dg).__name__ == "OxigraphDataGraph"
