# -*- coding: utf-8 -*-
#
import pytest
from os import path, walk
import glob
import pyshacl
from pyshacl.errors import ReportableRuntimeError

here_dir = path.abspath(path.dirname(__file__))
dash_files_dir = path.join(here_dir, 'resources', 'dash_tests')
dash_core_files = []
dash_sparql_files = []
dash_triple_rules_files = []
dash_sparql_rules_files = []
dash_expression_files = []
dash_target_files = []
dash_fn_files = []

# There are some tests we know will fail, but we don't want to stop deployment
# if we hit them. List them here:
ALLOWABLE_NOT_IMPLEMENTED = []

# This one relies on owl_imports to be turned on
# and also needs this file, but its missing: http://datashapes.org/shasf/tests/rules/triple/person
ALLOWABLE_FAILURES = ["/rules/triple/person2schema.test.ttl"]

for x in walk(path.join(dash_files_dir, 'core')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_core_files.append((y, None))

@pytest.mark.parametrize('target_file, shacl_file', dash_core_files)
def test_dash_validate_all_core(target_file, shacl_file):
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    assert val
    print(v_text)



for x in walk(path.join(dash_files_dir, 'sparql')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_sparql_files.append((y, None))

@pytest.mark.parametrize('target_file, shacl_file', dash_sparql_files)
def test_dash_validate_all_sparql(target_file, shacl_file):
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
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
            target_file, shacl_graph=shacl_file, advanced=True, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
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
            target_file, shacl_graph=shacl_file, advanced=True, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
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
            target_file, shacl_graph=shacl_file, advanced=True, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
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
            target_file, shacl_graph=shacl_file, advanced=True, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
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

# Get all SHACLFunction tests
for x in walk(path.join(dash_files_dir, 'function')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_fn_files.append((y, None))
@pytest.mark.parametrize('target_file, shacl_file', dash_fn_files)
def test_dash_validate_functions(target_file, shacl_file):
    test_name = shacl_file or target_file
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, advanced=True, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
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
