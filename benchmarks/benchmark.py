# -*- coding: utf-8 -*-
import timeit

# set up code is not included in the benchmark
# this includes loading the SHACL file into a rdflib graph
# this is a benchmark of the validator, not of rdflib ttl parsing.
set_up_script = '''
import rdflib
from pyshacl import monkey
import pyshacl
from os import path
monkey.apply_patches()
target_ttl_file = \
    '../test/resources/dash_tests/core/complex/personexample.test.ttl'
target_ttl_file = path.abspath(target_ttl_file)
target_graph = rdflib.Graph("Memory")
with open(target_ttl_file, 'rb') as file:
    target_graph.parse(file=file, format='turtle')
'''

run_script_pre_none = '''
r = pyshacl.validate(target_graph, inference='none')
'''

run_script_pre_rdfs = '''
r = pyshacl.validate(target_graph, inference='rdfs')
'''

run_script_pre_owlrl = '''
r = pyshacl.validate(target_graph, inference='owlrl')
'''

run_script_pre_both = '''
r = pyshacl.validate(target_graph, inference='both')
'''

t1 = timeit.timeit(run_script_pre_none, set_up_script, number=200) / 200.0

t2 = timeit.timeit(run_script_pre_rdfs, set_up_script, number=200) / 200.0

t3 = timeit.timeit(run_script_pre_owlrl, set_up_script, number=200) / 200.0

t4 = timeit.timeit(run_script_pre_both, set_up_script, number=200) / 200.0


print("Benchmark completed. Validation took:\n"
      "With no inferencing: {} seconds\n"
      "With rdfs inferencing: {} seconds\n"
      "With owl-rl inferencing: {} seconds\n"
      "With both inferencing: {} seconds\n".format(t1, t2, t3, t4))
