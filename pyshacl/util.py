# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
from io import IOBase, BytesIO

import rdflib
from rdflib.collection import Collection
from rdflib.namespace import NamespaceManager
from pyshacl.consts import SH, RDF_first, RDFS_Resource
from pyshacl.errors import ReportableRuntimeError


def stringify_blank_node(graph, bnode, ns_manager=None, recursion=0):
    assert isinstance(graph, rdflib.Graph)
    assert isinstance(bnode, rdflib.BNode)
    if recursion >= 10:
        return "Recursion too deep ..."
    stringed_cache_key = id(graph), str(bnode)
    if stringify_blank_node.stringed_cache is None:
        stringify_blank_node.stringed_cache = {}
    else:
        try:
            cached = stringify_blank_node.stringed_cache[stringed_cache_key]
            return cached
        except KeyError:
            pass
    if ns_manager is None:
        ns_manager = graph.namespace_manager
        ns_manager.bind("sh", SH)
    def stringify_list(node):
        item_texts = []
        for item in iter(graph.items(node)):
            item_text = stringify_node(graph, item, ns_manager=ns_manager,
                                       recursion=recursion+1)
            item_texts.append(item_text)
        # item_texts.sort()  ## Don't sort, to preserve list order
        return "( {} )".format(" ".join(item_texts))
    predicates = list(graph.predicates(bnode))
    if len(predicates) < 1:
        return "[ ]"
    if RDF_first in predicates:
        return stringify_list(bnode)
    p_string_map = {}
    for p in predicates:
        p_string = p.n3(namespace_manager=ns_manager)
        objs = list(graph.objects(bnode, p))
        if len(objs) < 1:
            continue
        o_texts = []
        for o in objs:
            o_text = stringify_node(graph, o, ns_manager=ns_manager,
                                    recursion=recursion+1)
            o_texts.append(o_text)
        if len(o_texts) > 1:
            o_texts.sort()
            o_text = ", ".join(o_texts)
        else:
            o_text = o_texts[0]
        p_string_map[p_string] = o_text
    if len(p_string_map) > 1:
        g = ["{} {}".format(p, o)
             for p, o in sorted(p_string_map.items())]
        blank_string = " ; ".join(g)
    else:
        p, o = next(iter(p_string_map.items()))
        blank_string = "{} {}".format(p, o)
    blank_string = "[ {} ]".format(blank_string)
    stringify_blank_node.stringed_cache[stringed_cache_key] = blank_string
    return blank_string
stringify_blank_node.stringed_cache = None

def stringify_literal(graph, node, ns_manager=None):
    lit_val_string = str(node.value)
    lex_val_string = str(node)
    if ns_manager is None:
        ns_manager = graph.namespace_manager
        ns_manager.bind("sh", SH)
    if lit_val_string != lex_val_string:
        val_string = "\"{}\" = {}".format(lex_val_string, lit_val_string)
    else:
        val_string = "\"{}\"".format(lex_val_string)
    if node.language:
        lang_string = ", lang={}".format(str(node.language))
    else:
        lang_string = ""
    if node.datatype:
        datatype_uri = stringify_node(graph, node.datatype,
                                      ns_manager=ns_manager)
        datatype_string = ", datatype={}".format(datatype_uri)
    else:
        datatype_string = ""
    node_string = "Literal({}{}{})" \
        .format(val_string,
                lang_string,
                datatype_string)
    return node_string

def stringify_node(graph, node, ns_manager=None, recursion=0):
    if ns_manager is None:
        ns_manager = graph.namespace_manager
        ns_manager.bind("sh", SH)
    if isinstance(node, rdflib.Literal):
        node_string = stringify_literal(graph, node, ns_manager=ns_manager)
    elif isinstance(node, rdflib.BNode):
        node_string = stringify_blank_node(
                      graph, node, ns_manager=ns_manager,
                      recursion=recursion+1)
    elif isinstance(node, rdflib.URIRef):
        node_string = node.n3(namespace_manager=ns_manager)
    else:
        node_string = str(node)
    return node_string

def match_blank_nodes(graph1, bnode1, graph2, bnode2):
    string_1 = stringify_blank_node(graph1, bnode1)
    string_2 = stringify_blank_node(graph2, bnode2)
    return string_1 == string_2

# baseURI: http://datashapes.org/sh/tests/sparql/property/sparql-001.test
def load_into_graph(target, rdf_format=None):
    if isinstance(target, rdflib.Graph):
        return target
    target_is_open = False
    target_is_file = False
    target_is_text = False
    filename = None
    public_id = None
    uri_prefix = None
    if isinstance(target, IOBase) and hasattr(target, 'read'):
        target_is_file = True
        target_is_open = True
        filename = target.name
        abs = os.path.abspath(filename)
        public_id = "file://{}#".format(abs)
    elif isinstance(target, str):
        if target.startswith('file://'):
            public_id = target
            target_is_file = True
            filename = target[7:]
        elif target.startswith('http:') or target.startswith('https:'):
            raise ReportableRuntimeError(
                "Cannot import graph files from the web using this function.")
        else:
            if target.startswith("/") or target.startswith("./"):
                target_is_file = True
                filename = target
            elif target.startswith("#") or target.startswith("@") \
                    or target.startswith("<"):
                target_is_file = False
            elif len(target) < 140:
                target_is_file = True
                filename = target
        if not target_is_file:
            target = target.encode('utf-8')
            target_is_text = True
    else:
        raise ReportableRuntimeError("Cannot determine the format of the input graph")
    if filename:
        if filename.endswith('.ttl'):
            rdf_format = rdf_format or 'turtle'
        if filename.endswith('.nt'):
            rdf_format = rdf_format or 'nt'
        elif filename.endswith('.xml'):
            rdf_format = rdf_format or 'xml'
        elif filename.endswith('.json'):
            rdf_format = rdf_format or 'json-ld'
    if target_is_file and filename and not target_is_open:
        filename = os.path.abspath(filename)
        if not public_id:
            public_id = "file://{}#".format(filename)
        target = open(filename, mode='rb')
        target_is_open = True
    if target_is_open:
        data = target.read()
        target.close()
        target = data
        target_is_text = True
    g = rdflib.Graph()
    if target_is_text:
        target = BytesIO(target)
        while True:
            try:
                l = target.readline()
                assert l is not None
            except:
                break
            l = l.lstrip(b" ")
            if not l.startswith(b"#"):
                break
            l = l.strip(b"# ")
            spl = l.split(b":", 1)
            if len(spl) < 1:
                continue
            if spl[0].lower() == b"baseuri":
                public_id = spl[1].strip(b" \n").decode('utf-8') + "#"
            elif spl[0].lower() == b"prefix":
                uri_prefix = spl[1].strip(b" \n").decode('utf-8')
        target.seek(0)
        g.parse(source=target, format=rdf_format, publicID=public_id)
    else:
        raise RuntimeError("Error opening graph from source.")

    if public_id:
        if uri_prefix:
            has_named_prefix = g.store.namespace(uri_prefix)
            if not has_named_prefix:
                g.namespace_manager.bind(uri_prefix, public_id)
        else:
            has_blank_prefix = g.store.namespace('')
            if not has_blank_prefix:
                g.namespace_manager.bind('', public_id)
    return g

def clone_graph(source_graph, identifier=None):
    """

    :param source_graph:
    :type source_graph: rdflib.Graph
    :param identifier:
    :type identifier: str | None
    :return:
    """
    g = rdflib.Graph(identifier=identifier)
    for p, n in source_graph.namespace_manager.namespaces():
        g.namespace_manager.bind(p, n)
    for t in iter(source_graph):
        g.add(t)
    return g


def clone_blank_node(graph, bnode, target_graph, recursion=0):
    assert isinstance(graph, rdflib.Graph)
    assert isinstance(bnode, rdflib.BNode)
    cloned_bnode = rdflib.BNode()
    if recursion >= 10:
        return cloned_bnode  # Cannot clone this deep

    def clone_list(l_node):
        cloned_node = rdflib.BNode()
        new_list = Collection(target_graph, cloned_node)
        for item in iter(graph.items(l_node)):
            cloned_item = clone_node(graph, item, target_graph, recursion=recursion+1)
            new_list.append(cloned_item)
        return cloned_node

    predicates = set(graph.predicates(bnode))
    if len(predicates) < 1:
        return cloned_bnode
    if RDF_first in predicates:
        return clone_list(bnode)
    for p in predicates:
        cloned_p = clone_node(graph, p, target_graph, recursion=recursion+1)
        objs = list(graph.objects(bnode, p))
        if len(objs) < 1:
            continue
        for o in objs:
            cloned_o = clone_node(graph, o, target_graph,
                                      recursion=recursion+1)
            target_graph.add((cloned_bnode, cloned_p, cloned_o))
    return cloned_bnode


def clone_literal(graph, node, target_graph):
    lex_val_string = str(node)
    lang = node.language
    datatype = node.datatype
    new_literal = rdflib.Literal(lex_val_string,
                                 lang, datatype)
    return new_literal


def clone_node(graph, node, target_graph, recursion=0):
    if isinstance(node, rdflib.Literal):
        new_node = clone_literal(graph, node, target_graph)
    elif isinstance(node, rdflib.BNode):
        new_node = clone_blank_node(
                   graph, node, target_graph,
                   recursion=recursion+1)
    elif isinstance(node, rdflib.URIRef):
        new_node = rdflib.URIRef(str(node))
    else:
        new_node = rdflib.term.Identifier(str(node))
    return new_node


def compare_blank_node(graph1, bnode1, graph2, bnode2, recursion=0):
    assert isinstance(graph1, rdflib.Graph)
    assert isinstance(graph2, rdflib.Graph)
    assert isinstance(bnode1, rdflib.BNode)
    assert isinstance(bnode2, rdflib.BNode)
    if recursion >= 10:
        return 1  # Cannot compare this deep

    def compare_list(l_node1, l_node2):
        # TODO, determine if lists must be ordered
        list_1_items = list(graph1.items(l_node1))
        list_2_items = list(graph2.items(l_node2))
        if len(list_1_items) > len(list_2_items):
            return 1
        elif len(list_2_items) > len(list_1_items):
            return -1
        eq = 0
        for i1 in list_1_items:
            found = None
            for i2 in list_2_items:
                eq = compare_node(graph1, i1, graph2, i2, recursion=recursion+1)
                if eq == 0:
                    found = i2
                    break
            if found is not None:
                list_2_items.remove(found)
            else:
                eq = 1
                break
        return eq


    predicates1 = set(graph1.predicates(bnode1))
    predicates2 = set(graph2.predicates(bnode2))
    in_ps1_but_not_in_ps2 = list()
    in_ps2_but_not_in_ps1 = list()
    pred_objs_in_bnode1_but_not_bnode2 = list()
    pred_objs_in_bnode2_but_not_bnode1 = list()
    def return_eq(direction):
        nonlocal in_ps2_but_not_in_ps1
        nonlocal in_ps1_but_not_in_ps2
        if direction == 0:
            return direction
        if recursion <= 1:
            if direction < 0:
                print("BNode1 is smaller.")
            else:
                print("BNode1 is larger.")
            print("BNode1:")
            print(stringify_node(graph1, bnode1))
            print("BNode2:")
            print(stringify_node(graph2, bnode2))
            if len(in_ps1_but_not_in_ps2) > 0:
                print("In predicates of BNode1, but not in predicates of BNode2:")
                for p in in_ps1_but_not_in_ps2:
                    print("predicate: {}".format(stringify_node(graph1, p)))
            if len(in_ps2_but_not_in_ps1) > 0:
                print("In predicates of BNode2, but not in predicates of BNode1:")
                for p in in_ps2_but_not_in_ps1:
                    print("predicate: {}".format(stringify_node(graph2, p)))
            if len(pred_objs_in_bnode1_but_not_bnode2) > 0:
                print("In predicate/objects of BNode1, but not in predicate/objects of BNode2:")
                for p, o in pred_objs_in_bnode1_but_not_bnode2:
                    print("predicate: {} object: {}".format(stringify_node(graph1, p), stringify_node(graph1, o)))
            if len(pred_objs_in_bnode2_but_not_bnode1) > 0:
                print("In predicate/objects of BNode2, but not in predicate/objects of BNode1:")
                for p, o in pred_objs_in_bnode2_but_not_bnode1:
                    print("predicate: {} object: {}".format(stringify_node(graph2, p), stringify_node(graph2, o)))
        return direction

    if len(predicates1) < 1 and len(predicates2) < 1:
        return return_eq(0)
    elif len(predicates1) < 1:
        return return_eq(-1)
    elif len(predicates2) < 1:
        return return_eq(1)

    if RDF_first in predicates1 and RDF_first in predicates2:
        return compare_list(bnode1, bnode2)
    elif RDF_first in predicates1:
        return return_eq(1)
    elif RDF_first in predicates2:
        return return_eq(-1)

    p1s_compared = set()
    p2s_compared = set()
    bnode1_eq = 0
    for p1 in predicates1:
        if isinstance(p1, rdflib.URIRef):
            if p1 in predicates2:
                o1_list = list(graph1.objects(bnode1, p1))
                o2_list = list(graph2.objects(bnode2, p1))

                for o1 in o1_list:
                    if o1 == RDFS_Resource:
                        continue
                    found = None
                    for o2 in o2_list:
                        eq = compare_node(graph1, o1, graph2, o2, recursion=recursion+1)
                        if eq == 0:
                            found = o2
                            break
                    if found is not None:
                        o2_list.remove(found)
                    else:
                        pred_objs_in_bnode1_but_not_bnode2.append((p1, o1))

                if len(pred_objs_in_bnode1_but_not_bnode2) > 0:
                    bnode1_eq = 1
            else:
                in_ps1_but_not_in_ps2.append(p1)
                bnode1_eq = 1
        else:
            raise NotImplementedError(
                "Don't know to compare non-uri predicates on a blank node.")
    bnode2_eq = 0
    for p2 in predicates2:
        if isinstance(p2, rdflib.URIRef):
            if p2 in predicates1:
                o1_list = list(graph1.objects(bnode1, p2))
                o2_list = list(graph2.objects(bnode2, p2))

                for o2 in o2_list:
                    if o2 == RDFS_Resource:
                        continue
                    found = None
                    for o1 in o1_list:
                        eq = compare_node(graph2, o2, graph1, o1,
                                          recursion=recursion + 1)
                        if eq == 0:
                            found = o1
                            break
                    if found is not None:
                        o1_list.remove(found)
                    else:
                        pred_objs_in_bnode2_but_not_bnode1.append((p2, o2))

                if len(pred_objs_in_bnode2_but_not_bnode1) > 0:
                    bnode2_eq = 1
            else:
                in_ps2_but_not_in_ps1.append(p2)
                bnode2_eq = 1
        else:
            raise NotImplementedError(
                "Don't know to compare non-uri predicates on a blank node.")

    if bnode1_eq == 0 and bnode2_eq == 0:
        return return_eq(0)
    if bnode1_eq == 1 and bnode2_eq == 1:
        return return_eq(2)
    if bnode1_eq == -1 and bnode2_eq == -1:
        return return_eq(-2)
    if bnode1_eq == 1 and bnode2_eq == 0:
        return return_eq(1)
    if bnode1_eq == 0 and bnode2_eq == 1:
        return return_eq(-1)
    if bnode1_eq == 0 and bnode2_eq == -1:
        return return_eq(1)
    if bnode1_eq == -1 and bnode2_eq == 0:
        return return_eq(-1)
    return return_eq(bnode1_eq)


def compare_literal(graph1, node1, graph2, node2):
    try:
        cmp = node1.eq(node2)
    except TypeError:
        # Type error means we cannot compare these literals
        cmp = False
    if cmp:
        return 0  # 0 = equal
    else:
        return 1  # 1 = not-equal


def compare_node(graph1, node1, graph2, node2, recursion=0):
    if isinstance(node1, rdflib.Literal) and isinstance(node2, rdflib.Literal):
        eq = compare_literal(graph1, node1, graph2, node2)
    elif isinstance(node1, rdflib.Literal):
        eq = 1 # node1 being a literal is greater
    elif isinstance(node2, rdflib.Literal):
        eq = -1 # node2 being a literal is greater
    elif isinstance(node1, rdflib.BNode) and isinstance(node2, rdflib.BNode):
        eq = compare_blank_node(graph1, node1, graph2, node2,
                                recursion=recursion+1)
    elif isinstance(node1, rdflib.BNode):
        eq = 1 # node1 being a BNode is greater
    elif isinstance(node2, rdflib.BNode):
        eq = -1  # node2 being a BNode is greater
    elif isinstance(node1, rdflib.URIRef) and isinstance(node2, rdflib.URIRef):
        s1 = str(node1)
        s2 = str(node2)
        if s1 > s2:
            eq = 1
        elif s2 > s1:
            eq = -1
        else:
            eq = 0
    else:
        s1 = str(node1)
        s2 = str(node2)
        if s1 > s2:
            eq = 1
        elif s2 > s1:
            eq = -1
        else:
            eq = 0
    return eq