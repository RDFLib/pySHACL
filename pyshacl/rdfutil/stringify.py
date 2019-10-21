# -*- coding: utf-8 -*-
#
import rdflib
from . import SH, RDF_first


def stringify_blank_node(graph, bnode, ns_manager=None, recursion=0):
    if isinstance(graph, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        raise RuntimeError("Can only stringify a blank node when graph is an rdflib.Graph")
    assert isinstance(graph, rdflib.Graph)
    assert isinstance(bnode, rdflib.BNode)
    if recursion >= 9:
        return "<http://recursion.too.deep>"
    stringed_cache_key = id(graph), str(bnode)
    if stringify_blank_node.stringed_cache is None:
        stringify_blank_node.stringed_cache = {}
    else:
        try:
            cached = stringify_blank_node.stringed_cache[stringed_cache_key]
            return cached
        except KeyError:
            pass
    if ns_manager is None:  # pragma: no cover
        ns_manager = graph.namespace_manager
        ns_manager.bind("sh", SH)

    def stringify_list(node):
        nonlocal graph, ns_manager, recursion
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
    if ns_manager is None:  # pragma: no cover
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


def find_node_named_graph(dataset, node):
    if isinstance(node, rdflib.Literal):
        raise RuntimeError("Cannot search for a Literal node in a dataset.")
    for g in iter(dataset.contexts()):
        try:
             first = next(iter(g.predicate_objects(node)))
             return g
        except StopIteration:
            continue
    raise RuntimeError("Cannot find that node in any named graph.")

def stringify_node(graph, node, ns_manager=None, recursion=0):
    if ns_manager is None:
        ns_manager = graph.namespace_manager
    if isinstance(ns_manager, rdflib.Graph):
        #json-ld loader can set namespace_manager to the conjunctive graph itself.
        ns_manager = ns_manager.namespace_manager
    ns_manager.bind("sh", SH, override=False, replace=False)
    if isinstance(node, rdflib.Literal):
        return stringify_literal(graph, node, ns_manager=ns_manager)
    if isinstance(node, rdflib.BNode):
        if isinstance(graph, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
            graph = find_node_named_graph(graph, node)
        return stringify_blank_node(graph, node, ns_manager=ns_manager,
                                    recursion=recursion+1)
    if isinstance(node, rdflib.URIRef):
        return node.n3(namespace_manager=ns_manager)
    else:
        node_string = str(node)
    return node_string


def stringify_graph(graph):
    string_builder = ""
    for t in iter(graph):
        node_string = stringify_node(graph, t, ns_manager=graph.namespace_manager)
        string_builder += node_string
        string_builder += "\n"
    return string_builder


def match_blank_nodes(graph1, bnode1, graph2, bnode2):
    string_1 = stringify_blank_node(graph1, bnode1)
    string_2 = stringify_blank_node(graph2, bnode2)
    return string_1 == string_2
