# -*- coding: utf-8 -*-
#
from collections import defaultdict, OrderedDict
import sys
import pytest
from os import path, environ
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


tests_found_in_manifests = defaultdict(lambda: [])

for m in manifests_with_entries:
    tests = m.collect_tests()
    tests_found_in_manifests[m.base].extend(tests)

tests_found_in_manifests = OrderedDict(sorted(tests_found_in_manifests.items()))

# There are some tests we know will fail, but we don't want to stop deployment
# if we hit them. List them here:
ALLOWABLE_FAILURES = [
    "/core/property/datatype-ill-formed",
    "/sparql/pre-binding/shapesGraph-001"
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
        "/sparql/component/optional-001",
        "/sparql/pre-binding/pre-binding-001",
        "/sparql/pre-binding/pre-binding-003",
        "/sparql/pre-binding/pre-binding-004",
        "/sparql/pre-binding/pre-binding-005",
        "/sparql/pre-binding/pre-binding-007",
    ]
    ALLOWABLE_FAILURES.extend(MORE_ALLOWABLE_FAILURES)

@pytest.mark.parametrize(
    "base, index",
    [[base, i]
     for base,tests in tests_found_in_manifests.items()
     for i, t in enumerate(tests)]
)
def test_sht_all(base, index):
    tests = tests_found_in_manifests[base]
    t = tests[index]
    test_id = str(t.node).replace("file://", "")
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
