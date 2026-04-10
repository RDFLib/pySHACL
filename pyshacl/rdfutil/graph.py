# -*- coding: utf-8 -*-
#
import rdflib

from .pytypes import ConjunctiveLike, GraphLike


def get_default_graph(graph: GraphLike) -> rdflib.Graph:
    if isinstance(graph, rdflib.Dataset):
        return graph.default_graph
    if isinstance(graph, rdflib.ConjunctiveGraph):
        return graph.default_context
    return graph


def set_default_graph(graph: ConjunctiveLike, default_graph: rdflib.Graph) -> None:
    if isinstance(graph, rdflib.Dataset):
        graph.default_graph = default_graph
    else:
        graph.default_context = default_graph
