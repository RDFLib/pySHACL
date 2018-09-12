# -*- coding: utf-8 -*-
from pyshacl import validate
from os import path

target_ttl_file = \
    '../tests/resources/tests/core/complex/personexample.test.ttl'
target_ttl_file = path.abspath(target_ttl_file)

conforms, v_graph, v_text = validate(target_ttl_file, shacl_graph=None, inference='rdfs',
                                     serialize_report_graph=True)
print(conforms)
print(v_graph)
print(v_text)
