# -*- coding: utf-8 -*-
#
from collections import defaultdict, OrderedDict
import sys
import pytest
from os import path, walk
import glob
import pyshacl
from pyshacl.errors import ReportableRuntimeError
import rdflib
from rdflib.namespace import Namespace, RDF, RDFS
print(sys.path)
from test.helpers import load_manifest, flatten_manifests

here_dir = path.abspath(path.dirname(__file__))
sht_files_dir = path.join(here_dir, 'resources', 'sht_tests')
sht_main_manifest = path.join(sht_files_dir, 'manifest.ttl')
MF = Namespace('http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#')
SHT = Namespace('http://www.w3.org/ns/shacl-test#')


main_manifest = load_manifest(sht_main_manifest)
manifests_with_entries = flatten_manifests(main_manifest, True)

print(main_manifest)

tests_found_in_manifests = defaultdict(lambda: [])

for m in manifests_with_entries:
    tests = m.collect_tests()
    tests_found_in_manifests[m.base].extend(tests)

tests_found_in_manifests = OrderedDict(sorted(tests_found_in_manifests.items()))


@pytest.mark.parametrize(
    "base, index",
    [[base, i]
     for base,tests in tests_found_in_manifests.items()
     for i, t in enumerate(tests)]
)
def test_sht_all(base, index):
    tests = tests_found_in_manifests[base]
    t = tests[index]
    label = t.label
    data_file = t.data_graph
    shacl_file = t.shapes_graph
    sht_validate = (t.sht_graph, t.sht_result)
    if label:
        print("testing: ".format(label))
    try:
        val, _, v_text = pyshacl.validate(
            data_file, shacl_graph=shacl_file, inference='rdfs', check_sht_result=True, sht_validate=sht_validate, debug=True, meta_shacl=False)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        val = False
        v_text = ""
    print(v_text)
    assert val
    return True
