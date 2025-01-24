# -*- coding: utf-8 -*-
#
import platform
from pathlib import Path

import rdflib
from rdflib.namespace import Namespace, RDF, RDFS

from pyshacl.rdfutil.load import path_from_uri

MF = Namespace('http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#')
SHT = Namespace('http://www.w3.org/ns/shacl-test#')


class SHTValidate(object):
    def __init__(self, node, sht_graph, result_node, data_graph, shapes_graph, label=None, status=None):
        """

        :param sht_graph:
        :type sht_graph: rdflib.Graph
        :param data_graph:
        :type data_graph: rdflib.Graph
        :param shapes_graph:
        :type shapes_graph: rdflib.Graph
        :param label:
        """
        self.node = node
        self.sht_graph = sht_graph
        self.sht_result = result_node
        self.data_graph = data_graph
        self.shapes_graph = shapes_graph
        self.label = label
        self.status = status


class Manifest(object):
    def __init__(self, base, sht_graph, node, includes, entries=None, label=None):
        """
        Manifest constructor
        :param base: string
        :type base: the "file:///x" location uri of the base manifest graph
        :param sht_graph:
        :type sht_graph: rdflib.Graph
        :param node: The Graph Node of the manifest itself. (unused)
        :type node: rdflib.term.Identifier
        :param includes:
        :type includes: list(Manifest)
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
            test = SHTValidate(entry, self.sht_graph, result, data_graph, shapes_graph, label=label, status=status)
            tests.append(test)
        return tests


def load_manifest(filename, recursion=0):
    """
    Load a testing Manifest from a file location, return a Manifest object
    :param filename: the filename of the manifest document.
    :type filename: string
    :param recursion: re-entry counter.
    :type recursion: int
    :return: the loaded Manifest object
    :rtype: Manifest
    """
    if recursion >= 10:
        return None
    graph = rdflib.Graph()
    base_mf: Path
    with open(filename, 'rb') as manifest_file:
        if manifest_file.name.startswith("./"):
            # Special handling for relative paths
            base_uri_str = f"file:{manifest_file.name}"
            base_mf = Path(manifest_file.name)
        else:
            # we need to make this absolute, before we can get the as_uri for it.
            base_mf = Path(manifest_file.name).absolute()
            base_uri_str: str = base_mf.as_uri()
        graph.parse(file=manifest_file, format='turtle', publicID=base_uri_str)
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
            if href.startswith("file:"):
                child_path = path_from_uri(href, relative_to=base_mf)
                child_mf = load_manifest(str(child_path), recursion=recursion + 1)
            else:
                raise RuntimeError("Manifest can only include file: uris")
            if child_mf is None:
                raise RuntimeError("Manifest include chain is too deep!")
            include_manifests.append(child_mf)
    try:
        entries_list = next(iter(graph.objects(manifest, MF.entries)))
        entries = []
        for i in graph.items(entries_list):
            entries.append(i)
    except StopIteration:
        entries = None
    mf = Manifest(base_uri_str, graph, manifest, include_manifests, entries=entries, label=label)
    # if entries and len(entries) > 0:
    #     manifests_with_entries.append(mf)
    return mf


def flatten_manifests(root_manifest, only_with_entries=False, recursion=0):
    """
    Convert a tree-structure Manifest into a flat list structured list of
    Manifests.
    :param root_manifest:
    :type root_manifest: Manifest
    :param only_with_entries: Switch to filter result to only those
    manifests with entries.
    :type only_with_entries: bool
    :param recursion: re-entry counter.
    :type recursion: int
    :return:
    :rtype: list
    """
    m_list = []
    if recursion >= 10:
        return m_list
    includes = root_manifest.includes
    entries = root_manifest.entries
    if only_with_entries:
        if entries is not None and len(entries) > 0:
            m_list.append(root_manifest)
    else:
        m_list.append(root_manifest)
    for i in includes:
        f = flatten_manifests(i, only_with_entries=only_with_entries, recursion=recursion + 1)
        m_list.extend(f)
    return m_list
