# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/40

"""
from pyshacl import validate
from pyshacl.rdfutil import load_from_source


with open("./test/issues/test_040/sample-network.ttl", "r") as f:
    data_graph = load_from_source(f)

shacl_graph = load_from_source("./test/issues/test_040/03-Network.ttl")


def test_040():
    conforms, g, s = validate(data_graph=data_graph, shacl_graph=shacl_graph, ont_graph=shacl_graph, inference='rdfs')
    assert conforms


if __name__ == "__main__":
    test_040()
