# -*- coding: utf-8 -*-
#
import pytest
from os import path, walk, environ
import glob
import pyshacl
from pyshacl.errors import ReportableRuntimeError

here_dir = path.abspath(path.dirname(__file__))
dash_files_dir = path.join(here_dir, 'resources', 'dash_tests')
dash_core_files = []
dash_sparql_files = []
dash_rules_files = []
dash_target_files = []

for x in walk(path.join(dash_files_dir, 'core')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_core_files.append((y, None))


# There are some tests we know will fail, but we don't want to stop deployment
# if we hit them. List them here:
ALLOWABLE_FAILURES = [  # empty
]

DEB_BUILD_ARCH = environ.get('DEB_BUILD_ARCH', None)
DEB_HOST_ARCH = environ.get('DEB_HOST_ARCH', None)
if DEB_HOST_ARCH is not None or DEB_BUILD_ARCH is not None:
    # When running under debian deployment testing conditions, there are
    # some more tests that are known to fail, due to the use of an
    # older version of RDFLib shipped with debian.
    MORE_ALLOWABLE_FAILURES = [
        "/sparql/component/nodeValidator-001",
        "/sparql/component/propertyValidator-select-001",
        "/sparql/component/validator-001",
        "/sparql/component/optional-001"
    ]
    ALLOWABLE_FAILURES.extend(MORE_ALLOWABLE_FAILURES)

@pytest.mark.parametrize('target_file, shacl_file', dash_core_files)
def test_dash_validate_all_core(target_file, shacl_file):
    test_id = str(target_file).replace("file://", "").replace(".test.ttl", "")
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    print(v_text)
    try:
        assert val
    except AssertionError as ae:
        for af in ALLOWABLE_FAILURES:
            if test_id.endswith(af):
                print("Allowing failure in test: {}".format(test_id))
                break
        else:
            raise ae
    return True


for x in walk(path.join(dash_files_dir, 'sparql')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        dash_sparql_files.append((y, None))

@pytest.mark.parametrize('target_file, shacl_file', dash_sparql_files)
def test_dash_validate_all_sparql(target_file, shacl_file):
    test_id = str(target_file).replace("file://", "").replace(".test.ttl", "")
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_graph=shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    print(v_text)
    try:
        assert val
    except AssertionError as ae:
        for af in ALLOWABLE_FAILURES:
            if test_id.endswith(af):
                print("Allowing failure in test: {}".format(test_id))
                break
        else:
            raise ae
    return True

# Skip these, because sh:rule is not part of the SPARQL spec and support is not implemented
# for x in walk(path.join(dash_files_dir, 'rules')):
#     for y in glob.glob(path.join(x[0], '*.test.ttl')):
#         dash_rules_files.append((y, None))
# @pytest.mark.parametrize('target_file, shacl_file', dash_rules_files)
# def test_dash_validate_all_rules(target_file, shacl_file):
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

# Skip these, because sh:target is not part of the SPARQL spec and support is not implemented
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
