import pytest
from os import path, walk
import glob
import pyshacl


here_dir = path.abspath(path.dirname(__file__))
test_files_dir = path.join(here_dir, 'resources', 'tests')
test_core_files = []
test_rules_files = []

for x in walk(path.join(test_files_dir, 'core')):
    for y in glob.glob(path.join(x[0], '*.ttl')):
        test_core_files.append((y, None))

for x in walk(path.join(test_files_dir, 'rules')):
    for y in glob.glob(path.join(x[0], '*.ttl')):
        test_rules_files.append((y, None))

def test_validate():
    simple_file = path.join(test_files_dir, 'core/node/class-001.test.ttl')
    assert pyshacl.validate(simple_file, None)
    return True

# @pytest.mark.parametrize('target_file, shacl_file', test_core_files)
# def test_validate_all_core(target_file, shacl_file):
#     assert pyshacl.validate(target_file, shacl_file)
#     return True

# @pytest.mark.parametrize('target_file, shacl_file', test_rules_files)
# def test_validate_all_rules(target_file, shacl_file):
#     assert pyshacl.validate(target_file, shacl_file)
#     return True
