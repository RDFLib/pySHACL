# -*- coding: utf-8 -*-
"""
https://w3c.github.io/data-shapes/data-shapes-test-suite/#submitting-implementation-reports
"""
import platform
from collections import defaultdict, OrderedDict
from os import path
from datetime import datetime
import pyshacl
from pyshacl.errors import ReportableRuntimeError
import rdflib
from rdflib.namespace import Namespace, RDF, XSD

from test.helpers import load_manifest, flatten_manifests

EARL = Namespace("http://www.w3.org/ns/earl#")
DOAP = Namespace("http://usefulinc.com/ns/doap#")
PASSED = EARL.passed
FAILED = EARL.failed
PARTIAL = EARL.partial


TEST_PREFIX = "urn:x-shacl-test:"
PYSHACL_URI = rdflib.URIRef("https://github.com/RDFLib/pySHACL")
DEVELOPER_URI = rdflib.URIRef("https://github.com/ashleysommer")


here_dir = path.abspath(path.dirname(__file__))
sht_files_dir = path.join(here_dir, 'resources', 'sht_tests')
sht_main_manifest = path.join(sht_files_dir, 'manifest.ttl')


main_manifest = load_manifest(sht_main_manifest)
manifests_with_entries = flatten_manifests(main_manifest, True)

tests_found_in_manifests = defaultdict(lambda: [])

for m in manifests_with_entries:
    tests = m.collect_tests()
    tests_found_in_manifests[m.base].extend(tests)

tests_found_in_manifests = OrderedDict(sorted(tests_found_in_manifests.items()))

tests_base_index = [
    (base, i)
    for base, tests in tests_found_in_manifests.items()
    for i, t in enumerate(tests)
]


"""
[
  rdf:type earl:Assertion ;
  earl:assertedBy <https://github.com/ashleysommer> ;
  earl:result [
      rdf:type earl:TestResult ;
      earl:mode earl:automatic ;
      earl:outcome earl:passed ;
    ] ;
  earl:subject <https://github.com/RDFLib/pySHACL> ;
  earl:test <urn:x-shacl-test:/core/complex/personexample> ;
].
"""

assertions = {}

def make_assertion(base, index):
    assertion = list()
    assertion_node = rdflib.BNode()
    result_node = rdflib.BNode()
    assertion.append((assertion_node, RDF.type, EARL.Assertion))
    assertion.append((assertion_node, EARL.assertedBy, DEVELOPER_URI))
    assertion.append((assertion_node, EARL.subject, PYSHACL_URI))
    assertion.append((assertion_node, EARL.result, result_node))
    assertion.append((result_node, RDF.type, EARL.TestResult))
    assertion.append((result_node, EARL.mode, EARL.automatic))
    tests = tests_found_in_manifests[base]
    t = tests[index]
    test_uri_string = str(t.node)
    if platform.system() == "Windows":
        if test_uri_string.startswith("file:///"):
            test_uri_string = test_uri_string[8:]
    else:
        if test_uri_string.startswith("file://"):
            test_uri_string = test_uri_string[7:]
    test_uri_string = test_uri_string.replace(sht_files_dir, TEST_PREFIX)
    test_uri = rdflib.URIRef(test_uri_string)
    assertion.append((assertion_node, EARL.test, test_uri))

    label = t.label
    data_file = t.data_graph
    shacl_file = t.shapes_graph
    sht_validate = (t.sht_graph, t.sht_result)
    if label and len(label) > 0:
        print("testing: {}".format(label))
    try:
        val, _, v_text = pyshacl.validate(
            data_file, shacl_graph=shacl_file, inference='rdfs',
            check_sht_result=True, sht_validate=sht_validate,
            debug=True, meta_shacl=False)
    except (NotImplementedError, ReportableRuntimeError) as e:
        print(e)
        info_text = rdflib.Literal(str(e.args[0]), lang="en")
        assertion.append((result_node, EARL.info, info_text))
        val = False
        v_text = info_text
    print(v_text)
    if v_text.startswith("Validation Failure"):
        info_text = rdflib.Literal(v_text, lang="en")
        assertion.append((result_node, EARL.info, info_text))
    if val is True:
        assertion.append((result_node, EARL.outcome, PASSED))
    else:
        print("FAILED {}".format(test_uri))
        assertion.append((result_node, EARL.outcome, FAILED))
    return assertion


"""
<https://github.com/RDFLib/pySHACL>
  rdf:type doap:Project ;
  rdf:type earl:Software ;
  rdf:type earl:TestSubject ;
  doap:developer <https://github.com/ashleysommer> ;
  doap:name "pySHACL" ;
.
"""
g = rdflib.Graph()
g.namespace_manager.bind("earl", str(EARL))
g.namespace_manager.bind("doap", str(DOAP))

g.add((PYSHACL_URI, RDF.type, DOAP.Project))
g.add((PYSHACL_URI, RDF.type, EARL.Software))
g.add((PYSHACL_URI, RDF.type, EARL.TestSubject))
g.add((PYSHACL_URI, DOAP.developer, DEVELOPER_URI))
g.add((PYSHACL_URI, DOAP.name, rdflib.Literal("pySHACL", datatype=XSD.string)))
version_node = rdflib.BNode()
g.add((version_node, RDF.type, DOAP.Version))
g.add((version_node, DOAP.created, rdflib.Literal(datetime.utcnow().date())))
g.add((version_node, DOAP.revision, rdflib.Literal(str(pyshacl.__version__))))
g.add((version_node, DOAP.name, rdflib.Literal("current", datatype=XSD.string)))
g.add((PYSHACL_URI, DOAP.release, version_node))


for arg in tests_base_index:
    triples = make_assertion(*arg)
    for t in iter(triples):
        g.add(t)

report_bytes = g.serialize(format='turtle')
print("REPORT: ------------------")
print(report_bytes.decode('utf-8'))
