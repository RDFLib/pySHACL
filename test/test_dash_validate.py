# -*- coding: utf-8 -*-
#
import glob
from os import path, walk

import pytest
import rdflib

import pyshacl
from pyshacl.errors import ReportableRuntimeError
from pyshacl.validator_conformance import DASH

here_dir = path.abspath(path.dirname(__file__))
dash_files_dir = path.join(here_dir, 'resources', 'dash_tests')
dash_core_files = []
dash_sparql_files = []
dash_triple_rules_files = []
dash_sparql_rules_files = []
dash_expression_files = []
dash_target_files = []
dash_fn_files = []
dash_query_files = []
# There are some tests we know will fail, but we don't want to stop deployment
# if we hit them. List them here:
ALLOWABLE_NOT_IMPLEMENTED = []

# This one relies on owl_imports to be turned on
# and also needs this file, but its missing: http://datashapes.org/shasf/tests/rules/triple/person
ALLOWABLE_FAILURES = ["/rules/triple/person2schema.test.ttl"]

for x in walk(path.join(dash_files_dir, 'core')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        if "node/datatype-002" in y:
            dash_core_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_core_files)
def test_dash_validate_all_core(target_file, shacl_file):
    # Literals in the data graph should be exactly the same as literals in the shapes graph
    # When the validator parses the shapes graph, it does it with NORMALIZE_LITERALS disabled
    # So we must also disable NORMALIZE_LITERALS when parsing the data graph
    rdflib.NORMALIZE_LITERALS = False
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False
        )
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    assert val
    print(v_text)


@pytest.mark.parametrize('target_file, shacl_file', dash_core_files)
def test_dash_validate_all_core_sparql_mode(target_file, shacl_file):
    # Literals in the data graph should be exactly the same as literals in the shapes graph
    # When the validator parses the shapes graph, it does it with NORMALIZE_LITERALS disabled
    # So we must also disable NORMALIZE_LITERALS when parsing the data graph
    rdflib.NORMALIZE_LITERALS = False
    try:
        if shacl_file is None:
            # shacl_file cannot be None in SPARQL Remote Graph Mode
            shacl_file = target_file
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            inference='none',
            check_dash_result=True,
            debug=True,
            sparql_mode=True,
            meta_shacl=False,
        )
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    print(v_text)
    assert val


for x in walk(path.join(dash_files_dir, 'sparql')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_sparql_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_sparql_files)
def test_dash_validate_all_sparql(target_file, shacl_file):
    # Literals in the data graph should be exactly the same as literals in the shapes graph
    # When the validator parses the shapes graph, it does it with NORMALIZE_LITERALS disabled
    # So we must also disable NORMALIZE_LITERALS when parsing the data graph
    rdflib.NORMALIZE_LITERALS = False
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False
        )
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    assert val
    print(v_text)


@pytest.mark.parametrize('target_file, shacl_file', dash_sparql_files)
def test_dash_validate_all_sparql_sparql_mode(target_file, shacl_file):
    # Literals in the data graph should be exactly the same as literals in the shapes graph
    # When the validator parses the shapes graph, it does it with NORMALIZE_LITERALS disabled
    # So we must also disable NORMALIZE_LITERALS when parsing the data graph
    rdflib.NORMALIZE_LITERALS = False
    try:
        if shacl_file is None:
            # shacl_file cannot be None in SPARQL Remote Graph Mode
            shacl_file = target_file
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            inference='none',
            check_dash_result=True,
            debug=True,
            sparql_mode=True,
            meta_shacl=False,
        )
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    assert val
    print(v_text)


# Tests for SHACL Advanced Features: https://www.w3.org/TR/shacl-af

# Skip these, because sh:target is not part of the SPARQL core spec and support is not implemented
# for x in walk(path.join(dash_files_dir, 'target')):
#     for y in glob.glob(path.join(x[0], '*.test.ttl')):
#         dash_target_files.append((y, None))
# @pytest.mark.parametrize('target_file, shacl_file', dash_target_files)
# def test_dash_validate_all_target(target_file, shacl_file):
#     try:
#         val, _, v_text = pyshacl.validate(
#             target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
#     except (NotImplementedError, ReportableRuntimeError) as e:
#         print(e)
#         val = False
#         v_text = ""
#     assert val
#     print(v_text)
#     return True

# Get all sparql-rules tests.
for x in walk(path.join(dash_files_dir, 'rules', 'sparql')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_sparql_rules_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_sparql_rules_files)
def test_dash_validate_all_sparql_rules(target_file, shacl_file):
    try:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
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


# Get all triple-rules tests.
for x in walk(path.join(dash_files_dir, 'rules', 'triple')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_triple_rules_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_triple_rules_files)
def test_dash_validate_all_triple_rules(target_file, shacl_file):
    test_name = shacl_file or target_file
    try:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
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


# Get all SHACL-AF sh:target tests.
for x in walk(path.join(dash_files_dir, 'target')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_target_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_target_files)
def test_dash_validate_target(target_file, shacl_file):
    test_name = shacl_file or target_file
    try:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
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


@pytest.mark.parametrize('target_file, shacl_file', dash_target_files)
def test_dash_validate_target_sparql_mode(target_file, shacl_file):
    test_name = shacl_file or target_file
    try:
        if shacl_file is None:
            # shacl_file cannot be None in SPARQL Remote Graph Mode
            shacl_file = target_file
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='none',
            check_dash_result=True,
            debug=True,
            sparql_mode=True,
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


# Get all SHACL-AF sh:expression tests.
for x in walk(path.join(dash_files_dir, 'expression')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_expression_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_expression_files)
def test_dash_validate_expression(target_file, shacl_file):
    test_name = shacl_file or target_file
    try:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
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


def test_extract_query_and_expected_result_valid_query():
    import rdflib
    from rdflib.namespace import RDF
    from rdflib.query import Result

    from pyshacl.validator_conformance import extract_query_and_expected_result

    g = rdflib.Graph()
    g.parse(path.join(dash_files_dir, "query", "passing-001.test.ttl"), format="turtle")
    test_case_uri = g.value(None, RDF.type, DASH.QueryTestCase)
    assert test_case_uri is not None, "Can't find test case in graph"
    query_str, result = extract_query_and_expected_result(test_case_uri, g)
    assert "name" in query_str and "age" in query_str

    assert isinstance(result, Result)
    # Check variables
    assert {str(var) for var in result.vars} == {"name", "age"}
    # Check bindings
    expected_bindings = [
        {"name": rdflib.Literal("Alice"), "age": rdflib.Literal(30)},
        {"name": rdflib.Literal("Bob"), "age": rdflib.Literal(25)},
    ]
    # Convert result bindings to comparable dicts
    actual_bindings = [row.asdict() for row in result]
    assert actual_bindings == expected_bindings


for x in walk(path.join(dash_files_dir, 'query')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_query_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_query_files)
def test_evaluate_query_testcase(target_file, shacl_file):
    import rdflib
    from rdflib.namespace import RDF, SH

    from pyshacl.validator_conformance import evaluate_query_testcase

    g = rdflib.Graph()
    g.parse(target_file, format="turtle")
    test_case_uri = g.value(None, RDF.type, DASH.QueryTestCase)
    assert test_case_uri is not None, "Can't find test case in graph"

    conforms = g.value(test_case_uri, SH.conforms)
    severity = g.value(test_case_uri, SH.severity)
    # Check for conformance if the test case says it should pass or fail
    if conforms is not None:
        result, _ = evaluate_query_testcase(g, test_case_uri)
        assert result == conforms.value
    # Check for exception if the test case says it should raise an exception
    elif severity == SH.Violation:
        with pytest.raises(Exception):
            evaluate_query_testcase(g, test_case_uri)
    # Otherwise, don't know what to do
    else:
        assert False, f"Don't know what to expect for {target_file}"


@pytest.mark.parametrize('target_file, shacl_file', dash_query_files)
def test_dash_validate_query_cases(target_file, shacl_file):
    import rdflib
    from rdflib.namespace import RDF, SH

    g = rdflib.Graph()
    g.parse(target_file, format="turtle")
    test_case_uri = g.value(None, RDF.type, DASH.QueryTestCase)
    assert test_case_uri is not None, "Can't find test case in graph"

    conforms = g.value(test_case_uri, SH.conforms)
    severity = g.value(test_case_uri, SH.severity)
    # Check for conformance if the test case says it should pass or fail
    if conforms is not None:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
            check_dash_result=True,
            debug=True,
            meta_shacl=False,
        )
        assert val == conforms.value
    # Check for a failing validation if the test case says it should raise an exception
    elif severity == SH.Violation:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
            check_dash_result=True,
            debug=True,
            meta_shacl=False,
        )
        assert val is False
    # Otherwise, don't know what to do
    else:
        assert False, f"Don't know what to expect for {target_file}"


# Get all SHACLFunction tests
for x in walk(path.join(dash_files_dir, 'function')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_fn_files.append((y, None))


@pytest.mark.parametrize('target_file, shacl_file', dash_fn_files)
def test_dash_validate_functions(target_file, shacl_file):
    test_name = shacl_file or target_file
    try:
        val, _, v_text = pyshacl.validate(
            target_file,
            shacl_graph=shacl_file,
            advanced=True,
            inference='rdfs',
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
