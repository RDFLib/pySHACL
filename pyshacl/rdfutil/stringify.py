# -*- coding: utf-8 -*-
#
from functools import wraps
from typing import Iterator, List, Optional, Tuple, Union, cast

import rdflib
from rdflib.namespace import NamespaceManager

from .consts import OWL, SH, RDF_first, RDFNode

OWLsameAs = OWL.sameAs


def with_dict_cache(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        dict_cache = getattr(wrapped, "dict_cache", None)
        assert dict_cache is not None
        return f(*args, **kwargs)

    dict_cache = getattr(wrapped, "dict_cache", None)
    if dict_cache is None:
        dict_cache = {}
        setattr(wrapped, "dict_cache", dict_cache)
    return wrapped


@with_dict_cache
def stringify_blank_node(
    graph: rdflib.Graph, bnode: rdflib.BNode, ns_manager: Optional[NamespaceManager] = None, recursion: int = 0
):
    if isinstance(graph, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        raise RuntimeError("Can only stringify a blank node when graph is a rdflib.Graph")
    assert isinstance(graph, rdflib.Graph)
    assert isinstance(bnode, rdflib.BNode)
    if recursion >= 12:
        return "<http://recursion.too.deep>"
    stringed_cache_key = id(graph), str(bnode)

    try:
        cached = stringify_blank_node.dict_cache[stringed_cache_key]
        return cached
    except LookupError:
        pass
    if ns_manager is None:  # pragma: no cover
        ns_manager = graph.namespace_manager
        ns_manager.bind("sh", SH)

    def stringify_list(node):
        nonlocal graph, ns_manager, recursion
        item_texts: List[str] = []
        for item in iter(graph.items(node)):
            item_text = stringify_node(graph, item, ns_manager=ns_manager, recursion=recursion + 1)
            item_texts.append(item_text)
        # item_texts.sort()  ## Don't sort, to preserve list order
        return "( {} )".format(" ".join(item_texts))

    predicates: List[RDFNode] = list(cast(Iterator[RDFNode], graph.predicates(bnode)))
    if len(predicates) < 1:
        return "[ ]"
    if RDF_first in predicates:
        return stringify_list(bnode)
    p_string_map = {}
    for p in predicates:
        if isinstance(p, (rdflib.Literal, rdflib.BNode, rdflib.URIRef)):
            p_string = p.n3(namespace_manager=ns_manager)
        else:
            p_string = str(p)
        objs: List[RDFNode] = list(cast(Iterator[RDFNode], graph.objects(bnode, p)))
        if len(objs) < 1:
            continue
        o_texts = []
        for o in objs:
            if p is OWLsameAs and o is bnode:
                # Avoid a crazy owl:sameAs recursion with self.
                o_texts.append("<self>")
            else:
                o_text = stringify_node(graph, o, ns_manager=ns_manager, recursion=recursion + 1)
                o_texts.append(o_text)
        if len(o_texts) > 1:
            o_texts.sort()
            o_text = ", ".join(o_texts)
        else:
            o_text = o_texts[0]
        p_string_map[p_string] = o_text
    if len(p_string_map) > 1:
        g = ["{} {}".format(p, o) for p, o in sorted(p_string_map.items())]
        blank_string = " ; ".join(g)
    else:
        _p, _o = next(iter(p_string_map.items()))
        blank_string = "{} {}".format(_p, _o)
    blank_string = "[ {} ]".format(blank_string)
    stringify_blank_node.dict_cache[stringed_cache_key] = blank_string
    return blank_string


def stringify_literal(graph: rdflib.Graph, node: rdflib.Literal, ns_manager: Optional[NamespaceManager] = None):
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
        if isinstance(node.datatype, (rdflib.URIRef, rdflib.Literal)):
            datatype_uri = stringify_node(graph, node.datatype, ns_manager=ns_manager)
        else:
            datatype_uri = str(node.datatype)
        datatype_string = ", datatype={}".format(datatype_uri)
    else:
        datatype_string = ""
    node_string = "Literal({}{}{})".format(val_string, lang_string, datatype_string)
    return node_string


def find_node_named_graph(dataset, node):
    """
    Search through each graph in a dataset for one node, when it finds it, returns the graph it is in
    :param dataset:
    :param node:
    :return:
    """
    if isinstance(node, rdflib.Literal):
        raise RuntimeError("Cannot search for a Literal node in a dataset.")
    for g in iter(dataset.contexts()):
        try:
            # This will issue StopIteration if node is not found in g, and continue to the next graph
            _ = next(iter(g.predicate_objects(node)))
            return g
        except StopIteration:
            continue
    raise RuntimeError("Cannot find that node in any named graph.")


def stringify_node(
    graph: rdflib.Graph,
    node: RDFNode,
    ns_manager: Optional[Union[NamespaceManager, rdflib.Graph]] = None,
    recursion: int = 0,
):
    if ns_manager is None:
        ns_manager = graph.namespace_manager
    if isinstance(ns_manager, rdflib.Graph):
        # json-ld loader can set namespace_manager to the conjunctive graph itself.
        ns_manager = ns_manager.namespace_manager
    if ns_manager is None or isinstance(ns_manager, rdflib.Graph):
        raise RuntimeError("Cannot stringify node, no namespaces known.")
    ns_manager.bind("sh", SH, override=False, replace=False)
    if isinstance(node, rdflib.Literal):
        return stringify_literal(graph, node, ns_manager=ns_manager)
    if isinstance(node, rdflib.BNode):
        if isinstance(graph, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
            graph = find_node_named_graph(graph, node)
        return stringify_blank_node(graph, node, ns_manager=ns_manager, recursion=recursion + 1)
    if isinstance(node, rdflib.URIRef):
        try:
            node_string = node.n3(namespace_manager=ns_manager)
        except Exception:
            node_string = str(node)
    else:
        node_string = str(node)
    return node_string


def stringify_graph(graph: rdflib.Graph):
    string_builder = ""
    t: Tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]
    for t in iter(graph):
        n1, n2, n3 = t
        node_string = stringify_node(graph, n1, ns_manager=graph.namespace_manager)
        string_builder += node_string + ", "
        node_string = stringify_node(graph, n2, ns_manager=graph.namespace_manager)
        string_builder += node_string + ", "
        node_string = stringify_node(graph, n3, ns_manager=graph.namespace_manager)
        string_builder += node_string + "\n"
    return string_builder


def match_blank_nodes(graph1: rdflib.Graph, bnode1: rdflib.BNode, graph2: rdflib.Graph, bnode2: rdflib.BNode):
    string_1 = stringify_blank_node(graph1, bnode1)
    string_2 = stringify_blank_node(graph2, bnode2)
    return string_1 == string_2
