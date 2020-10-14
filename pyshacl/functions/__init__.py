# -*- coding: utf-8 -*-
#
from typing import TYPE_CHECKING, List, Sequence, Type, Union

from pyshacl.consts import (
    RDF_type,
    SH_ask,
    SH_jsFunctionName,
    SH_jsLibrary,
    SH_select,
    SH_SHACLFunction,
    SH_SPARQLFunction,
)
from pyshacl.pytypes import GraphLike

from .shacl_function import SHACLFunction, SPARQLFunction


if TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph


def gather_functions(shacl_graph: 'ShapesGraph') -> Sequence[Union['SHACLFunction', 'SPARQLFunction']]:
    """

    :param shacl_graph:
    :type shacl_graph: ShapesGraph
    :return:
    :rtype: [SHACLRule]
    """

    spq_nodes = set(shacl_graph.subjects(RDF_type, SH_SPARQLFunction))
    if shacl_graph.js_enabled:
        from pyshacl.extras.js.function import JSFunction, SH_JSFunction

        js_nodes = set(shacl_graph.subjects(RDF_type, SH_JSFunction))
        use_JSFunction: Union[bool, Type] = JSFunction
    else:
        use_JSFunction = False
        js_nodes = set()
    scl_nodes = set(shacl_graph.subjects(RDF_type, SH_SHACLFunction)).difference(spq_nodes).difference(js_nodes)
    to_swap_spq = set()
    to_swap_js = set()
    for n in scl_nodes:
        has_select = len(shacl_graph.objects(n, SH_select)) > 0
        has_ask = len(shacl_graph.objects(n, SH_ask)) > 0
        if has_ask or has_select:
            to_swap_spq.add(n)
            continue
        if use_JSFunction:
            has_jslibrary = len(shacl_graph.objects(n, SH_jsLibrary)) > 0
            has_jsfuncitonnname = len(shacl_graph.objects(n, SH_jsFunctionName)) > 0
            if has_jslibrary or has_jsfuncitonnname:
                to_swap_js.add(n)
    for n in to_swap_spq:
        scl_nodes.remove(n)
        spq_nodes.add(n)
    for n in to_swap_js:
        scl_nodes.remove(n)
        js_nodes.add(n)

    all_fns: List[Union['SHACLFunction', 'SPARQLFunction', 'JSFunction']] = []
    for n in spq_nodes:
        all_fns.append(SPARQLFunction(n, shacl_graph))
    for n in scl_nodes:
        all_fns.append(SHACLFunction(n, shacl_graph))
    if use_JSFunction and callable(use_JSFunction):
        for n in js_nodes:
            all_fns.append(use_JSFunction(n, shacl_graph))
    return all_fns


def apply_functions(fns: Sequence, data_graph: GraphLike):
    for f in fns:
        f.apply(data_graph)


def unapply_functions(fns: Sequence, data_graph: GraphLike):
    for f in fns:
        f.unapply(data_graph)
