# -*- coding: utf-8 -*-
from pyshacl import validate
from os import path

data_ttl_file = \
    '../test/resources/dash_tests/core/complex/personexample.test.ttl'
data_ttl_file = path.abspath(data_ttl_file)

conforms, v_graph, v_text = validate(data_ttl_file, shacl_graph=None, inference='rdfs',
                                     serialize_report_graph=True)
print(conforms)
print(v_graph)
print(v_text)
