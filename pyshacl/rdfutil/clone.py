# -*- coding: utf-8 -*-
#
import rdflib
from rdflib.collection import Collection
from . import RDF_first


def clone_graph(source_graph, target_graph=None, identifier=None):
    """
    Make a clone of the source_graph by directly copying triples from source_graph to target_graph
    :param source_graph:
    :type source_graph: rdflib.Graph
    :param target_graph:
    :type target_graph: rdflib.Graph
    :param identifier:
    :type identifier: str | None
    :return: The cloned graph
    :rtype: rdflib.Graph
    """
    if target_graph is None:
        g = rdflib.Graph(identifier=identifier)
        for p, n in source_graph.namespace_manager.namespaces():
            g.namespace_manager.bind(p, n, override=True, replace=True)
    else:
        g = target_graph
        for p, n in source_graph.namespace_manager.namespaces():
            g.namespace_manager.bind(p, n, override=False, replace=False)
    for t in iter(source_graph):
        g.add(t)
    return g


def mix_graphs(source_graph1, source_graph2):
    """
    Make a clone of source_graph1 and add in the triples from source_graph2
    :param source_graph1:
    :type source_graph1: rdflib.Graph
    :param source_graph2:
    :type source_graph2: rdflib.Graph
    :return: The cloned graph with mixed in triples from source_graph2
    :rtype: rdflib.Graph
    """
    g = clone_graph(source_graph1, identifier=source_graph1.identifier)
    g = clone_graph(source_graph2, target_graph=g)
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
