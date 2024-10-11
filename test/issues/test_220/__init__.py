# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/220

"""
from pyshacl import validate
from pyshacl.rdfutil import load_from_source

data_graph1 = load_from_source("./test/issues/test_220/kb-REPRODUCTION-1.ttl")
shacl_graph1 = load_from_source("./test/issues/test_220/sh-REPRODUCTION-1.ttl")
data_graph2 = load_from_source("./test/issues/test_220/kb-REPRODUCTION-2.ttl")
shacl_graph2 = load_from_source("./test/issues/test_220/sh-REPRODUCTION-2.ttl")
ont_graph = load_from_source("./test/issues/test_220/owl-REPRODUCTION.ttl")


def test_220_1():
    conforms, g, s = validate(data_graph=data_graph1, shacl_graph=shacl_graph1, ont_graph=ont_graph, inference='none')
    assert conforms


def test_220_2():
    conforms, g, s = validate(data_graph=data_graph2, shacl_graph=shacl_graph2, ont_graph=ont_graph, inference='none')
    assert not conforms
    assert "Results (2)" in s


if __name__ == "__main__":
    test_220_1()
    test_220_2()
