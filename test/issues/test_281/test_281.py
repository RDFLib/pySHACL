# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/281
"""
import sys

import rdflib

import pyshacl

# Tests are always run from project root, even nested issues tests.
BASE_DIR = "./test/issues/test_281"

def test_281_a():
    conforms, results_graph, results_text = pyshacl.validate(
        f"file:{BASE_DIR}/data.ttl",
        shacl_graph=f"file:{BASE_DIR}/policies.ttl",
        debug=True,
        inference='none',
        advanced=False,
        meta_shacl=False,
        do_owl_imports=True,
    )
    assert not conforms

def test_281_b():
    from pyshacl.rdfutil.load import load_from_source
    with open(f"{BASE_DIR}/data.ttl") as data_f:
        data_g = load_from_source(data_f, rdf_format="turtle", do_owl_imports=False)
    with open(f"{BASE_DIR}/policies.ttl") as policy_f:
        policy_g = load_from_source(policy_f, rdf_format="turtle", do_owl_imports=True)

    conforms, results_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=policy_g,
        debug=True,
        inference='none',
        advanced=False,
        meta_shacl=False,
        do_owl_imports=True,
    )
    assert not conforms


if __name__ == "__main__":
    test_281_a()
    sys.exit(test_281_b())
