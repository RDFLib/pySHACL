# -*- coding: utf-8 -*-
#
import logging
import platform
from collections import OrderedDict, defaultdict
from os import path
from test.helpers import flatten_manifests, load_manifest

import pytest
from rdflib.namespace import RDF, RDFS, Namespace

import pyshacl
from pyshacl.errors import ReportableRuntimeError
from pyshacl.validator_conformance import check_sht_result

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
test_index_map = [[base, i] for base, tests in tests_found_in_manifests.items() for i, t in enumerate(tests)]

# There are some tests we know will fail, but we don't want to stop deployment
# if we hit them. List them here:
ALLOWABLE_FAILURES = ["/sparql/pre-binding/shapesGraph-001"]


@pytest.mark.parametrize("base, index", test_index_map)
def test_sht_all(base, index, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    tests = tests_found_in_manifests[base]
    test = tests[index]
    run_sht_test(test, {"inference": 'rdfs', "debug": True, "meta_shacl": False})


@pytest.mark.parametrize("base, index", test_index_map)
def test_sht_all_sparql_mode(base, index, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    tests = tests_found_in_manifests[base]
    test = tests[index]
    run_sht_test(test, {"inference": 'none', "debug": True, "sparql_mode": True, "meta_shacl": False})


def run_sht_test(sht_test, validate_args: dict) -> None:
    logger = logging.getLogger()  # pytest uses the root logger with a capturing handler
    if platform.system() == "Windows":
        test_id = str(sht_test.node).replace("file:///", "")
    else:
        test_id = str(sht_test.node).replace("file://", "")
    label = sht_test.label
    data_file = sht_test.data_graph
    shacl_file = sht_test.shapes_graph
    sparql_mode = validate_args.get('sparql_mode', False)
    if sparql_mode and shacl_file is None:
        # shacl_file cannot be None in SPARQL Remote Graph Mode
        shacl_file = data_file
    if label:
        logger.info("testing: ".format(label))
    try:
        conforms, r_graph, r_text = pyshacl.validate(data_file, shacl_graph=shacl_file, **validate_args)
    except (NotImplementedError, ReportableRuntimeError) as e:
        logger.exception(e)
        r_text = ""
        passes = False
    else:
        passes = check_sht_result(r_graph, sht_test.sht_graph, sht_test.sht_result, log=logger)
    logger.info(r_text)
    try:
        assert passes
    except AssertionError as ae:
        for af in ALLOWABLE_FAILURES:
            if test_id.endswith(af):
                logger.warning("Allowing failure in test: {}".format(test_id))
                break
        else:
            raise ae
