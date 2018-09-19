from collections import defaultdict

import pytest
from os import path, walk
import glob
import pyshacl
from pyshacl.errors import ReportableRuntimeError
import rdflib
from rdflib.namespace import Namespace, RDF, RDFS

here_dir = path.abspath(path.dirname(__file__))
sht_files_dir = path.join(here_dir, 'resources', 'sht_tests')
sht_main_manifest = path.join(sht_files_dir, 'manifest.ttl')
MF = Namespace('http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#')
SHT = Namespace('http://www.w3.org/ns/shacl-test#')
manifests_with_entries = []


class SHTValidate(object):
    def __init__(self, sht_graph, result_node, data_graph, shapes_graph, label=None, status=None):
        """

        :param sht_graph:
        :type sht_graph: rdflib.Graph
        :param data_graph:
        :type data_graph: rdflib.Graph
        :param shapes_graph:
        :type shapes_graph: rdflib.Graph
        :param label:
        """
        self.sht_graph = sht_graph
        self.sht_result = result_node
        self.data_graph = data_graph
        self.shapes_graph = shapes_graph
        self.label = label
        self.status = status

class Manifest(object):
    def __init__(self, base, sht_graph, node, includes, entries=None, label=None):
        """

        :param sht_graph:
        :type sht_graph: rdflib.Graph
        :param node:
        :type node: rdflib.term.Identifier
        :param includes:
        :type includes: list(TestManifest)
        :param entries:
        :type entries: list | None
        :param label:
        """
        self.base = base
        self.sht_graph = sht_graph
        self.node = node
        self.includes = includes
        self.entries = entries
        self.label = label

    @property
    def has_entries(self):
        return self.entries is not None and len(self.entries) > 0

    def collect_tests(self):
        if not self.has_entries:
            return []
        tests = []
        g = self.sht_graph
        for entry in self.entries:
            test_types = set(g.objects(entry, RDF.type))
            if SHT.Validate not in test_types:
                continue
            try:
                label = next(iter(g.objects(entry, RDFS.label)))
                label = str(label)
            except StopIteration:
                label = None
            try:
                action = next(iter(g.objects(entry, MF.action)))
            except StopIteration:
                raise RuntimeError("MF Validate has no value for mf:action")
            try:
                result = next(iter(g.objects(entry, MF.result)))
            except StopIteration:
                raise RuntimeError("MF Validate has no value for mf:result")
            try:
                data_graph = next(iter(g.objects(action, SHT.dataGraph)))
            except StopIteration:
                raise RuntimeError("mf:action has no value for sht:dataGraph")
            try:
                shapes_graph = next(iter(g.objects(action, SHT.shapesGraph)))
            except StopIteration:
                raise RuntimeError("mf:action has no value for sht:shapesGraph")
            try:
                status = next(iter(g.objects(entry, MF.status)))
            except StopIteration:
                raise RuntimeError("MF Validate has no value for mf:status")
            if str(shapes_graph) == str(data_graph):
                shapes_graph = None
            if str(data_graph) == self.base:
                data_graph = self.sht_graph
            test = SHTValidate(self.sht_graph, result, data_graph, shapes_graph, label=label, status=status)
            tests.append(test)
        return tests


def load_manifest(filename, recursion=0):
    if recursion >= 10:
        return None
    graph = rdflib.Graph()
    with open(filename, 'rb') as manifest_file:
        base = "file://{}".format(path.abspath(manifest_file.name))
        graph.parse(file=manifest_file, format='turtle', publicID=base)
    try:
        manifest = next(iter(graph.subjects(RDF.type, MF.Manifest)))
    except StopIteration:
        raise RuntimeError("Test cannot run. mf:Manifest not found in the manifest file: {}.".format(filename))
    try:
        label = next(iter(graph.objects(manifest, RDFS.label)))
        label = str(label)
    except StopIteration:
        label = None
    include_manifests = []
    include_objects = list(graph.objects(manifest, MF.include))
    for i in iter(include_objects):
        if isinstance(i, rdflib.URIRef):
            href = str(i)
            if href.startswith("file://"):
                child_mf = load_manifest(href[7:], recursion=recursion+1)
            else:
                raise RuntimeError("Manifest include chain is too deep!")
            include_manifests.append(child_mf)
    try:
        entries_list = next(iter(graph.objects(manifest, MF.entries)))
        entries = []
        for i in graph.items(entries_list):
            entries.append(i)
    except StopIteration:
        entries = None
    mf = Manifest(base, graph, manifest, include_manifests, entries=entries, label=label)
    if entries and len(entries) > 0:
        manifests_with_entries.append(mf)
    return mf

main_manifest = load_manifest(sht_main_manifest)

print(main_manifest)

tests_found_in_manifests = defaultdict(lambda: [])

for m in manifests_with_entries:
    tests = m.collect_tests()
    tests_found_in_manifests[m.base].extend(tests)

@pytest.mark.parametrize("base, index", [[base, i] for base,tests in tests_found_in_manifests.items() for i,t in enumerate(tests)])
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
    #
#
#
#
# @pytest.mark.parametrize('target_file, shacl_file', dash_core_files)
# def test_dash_validate_all_core(target_file, shacl_file):
#     try:
#         val, _, v_text = pyshacl.validate(
#             target_file, shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
#     except (NotImplementedError, ReportableRuntimeError) as e:
#         print(e)
#         val = False
#         v_text = ""
#     assert val
#     print(v_text)
#     print(v_text)
#     return True
# #
#
# for x in walk(path.join(dash_files_dir, 'sparql')):
#     for y in glob.glob(path.join(x[0], '*.test.ttl')):
#         dash_sparql_files.append((y, None))
#
# @pytest.mark.parametrize('target_file, shacl_file', dash_sparql_files)
# def test_dash_validate_all_sparql(target_file, shacl_file):
#     try:
#         val, _, v_text = pyshacl.validate(
#             target_file, shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
#     except (NotImplementedError, ReportableRuntimeError) as e:
#         print(e)
#         val = False
#         v_text = ""
#     assert val
#     print(v_text)
#     return True

# Skip these, because sh:rule is not part of the SPARQL spec and support is not implemented
# for x in walk(path.join(dash_files_dir, 'rules')):
#     for y in glob.glob(path.join(x[0], '*.test.ttl')):
#         dash_rules_files.append((y, None))
# @pytest.mark.parametrize('target_file, shacl_file', dash_rules_files)
# def test_dash_validate_all_rules(target_file, shacl_file):
#     try:
#         val, _, v_text = pyshacl.validate(
#             target_file, shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
#     except (NotImplementedError, ReportableRuntimeError) as e:
#         print(e)
#         val = False
#         v_text = ""
#     assert val
#     print(v_text)
#     return True

# Skip these, because sh:target is not part of the SPARQL spec and support is not implemented
# for x in walk(path.join(dash_files_dir, 'target')):
#     for y in glob.glob(path.join(x[0], '*.test.ttl')):
#         dash_target_files.append((y, None))
# @pytest.mark.parametrize('target_file, shacl_file', dash_target_files)
# def test_dash_validate_all_target(target_file, shacl_file):
#     try:
#         val, _, v_text = pyshacl.validate(
#             target_file, shacl_file, inference='rdfs', check_dash_result=True, debug=True, meta_shacl=False)
#     except (NotImplementedError, ReportableRuntimeError) as e:
#         print(e)
#         val = False
#         v_text = ""
#     assert val
#     print(v_text)
#     return True
