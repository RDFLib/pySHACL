import pytest
from os import path, walk
import glob
import pyshacl
from pyshacl.errors import ReportableRuntimeError

here_dir = path.abspath(path.dirname(__file__))
test_files_dir = path.join(here_dir, 'resources', 'tests')
test_core_files = []
test_sparql_files = []
test_rules_files = []

for x in walk(path.join(test_files_dir, 'core')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        test_core_files.append((y, None))

for x in walk(path.join(test_files_dir, 'sparql')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        test_sparql_files.append((y, None))

for x in walk(path.join(test_files_dir, 'rules')):
    for y in glob.glob(path.join(x[0], '*.test.ttl')):
        test_rules_files.append((y, None))

# def test_validate_class1():
#     simple_file = path.join(test_files_dir, 'core/node/class-001.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_class2():
#     simple_file = path.join(test_files_dir, 'core/node/class-002.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
#
# def test_validate_datatype1():
#     simple_file = path.join(test_files_dir, 'core/node/datatype-001.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_datatype2():
#     simple_file = path.join(test_files_dir, 'core/node/datatype-002.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_nodekind1():
#     simple_file = path.join(test_files_dir, 'core/node/nodeKind-001.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_minCount1():
#     simple_file = path.join(test_files_dir, 'core/property/minCount-001.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_minCount2():
#     simple_file = path.join(test_files_dir, 'core/property/minCount-002.test.ttl')
#     assert pyshacl.validate(simple_file, None)
#     return True
#
# def test_validate_maxCount1():
#     simple_file = path.join(test_files_dir, 'core/property/maxCount-001.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_maxCount2():
#     simple_file = path.join(test_files_dir, 'core/property/maxCount-002.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_property1():
#     simple_file = path.join(test_files_dir, 'core/property/property-001.test.ttl')
#     assert pyshacl.validate(simple_file, None)
#     return True
#
# def test_validate_property_node1():
#     simple_file = path.join(test_files_dir, 'core/property/node-001.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True
#
# def test_validate_property_node2():
#     simple_file = path.join(test_files_dir, 'core/property/node-002.test.ttl')
#     assert pyshacl.validate(simple_file, None, check_expected_result=True)
#     return True

@pytest.mark.parametrize('target_file, shacl_file', test_core_files)
def test_validate_all_core(target_file, shacl_file):
    try:
        val, _, v_text = pyshacl.validate(target_file, shacl_file, inference='rdfs', check_expected_result=True, meta_shacl=False)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    assert val
    print(v_text)
    print(v_text)
    return True

@pytest.mark.parametrize('target_file, shacl_file', test_sparql_files)
def test_validate_all_sparql(target_file, shacl_file):
    try:
        val, _, v_text = pyshacl.validate(
            target_file, shacl_file, inference='rdfs', check_expected_result=True, debug=True)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    assert val
    print(v_text)
    return True

# @pytest.mark.parametrize('target_file, shacl_file', test_rules_files)
# def test_validate_all_rules(target_file, shacl_file):
#     assert pyshacl.validate(target_file, shacl_file)
#     return True
