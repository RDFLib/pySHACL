# -*- coding: utf-8 -*-
#
import sys
from typing import TYPE_CHECKING, Dict, Sequence, Union

from pyshacl.consts import (
    RDF_type,
    SH_ask,
    SH_JSFunction,
    SH_jsFunctionName,
    SH_jsLibrary,
    SH_select,
    SH_SHACLFunction,
    SH_SPARQLFunction,
)
from pyshacl.pytypes import GraphLike, RDFNode

if TYPE_CHECKING:
    from pyshacl.extras.js.function import JSFunction  # noqa F401
    from pyshacl.shapes_graph import ShapesGraph

    from .shacl_function import SHACLFunction, SPARQLFunction


module = sys.modules[__name__]


def gather_functions(shacl_graph: 'ShapesGraph') -> Sequence[Union['SHACLFunction', 'SPARQLFunction']]:
    """

    :param shacl_graph:
    :type shacl_graph: ShapesGraph
    :return:
    :rtype: [SHACLRule]
    """

    spq_nodes = set(shacl_graph.subjects(RDF_type, SH_SPARQLFunction))
    if shacl_graph.js_enabled:
        js_nodes = set(shacl_graph.subjects(RDF_type, SH_JSFunction))
        use_JSFunction = True
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

    all_fns: Dict[RDFNode, Union['SHACLFunction', 'SPARQLFunction', 'JSFunction']] = {}
    if spq_nodes:
        SPQ = getattr(module, 'SPARQLFunction', None)
        if not SPQ:
            # Lazy-import SPARQLFunction to prevent rdflib import error
            from .shacl_function import SPARQLFunction

            setattr(module, 'SPARQLFunction', SPARQLFunction)
            SPQ = SPARQLFunction
        for n in spq_nodes:
            all_fns[n] = SPQ(n, shacl_graph)
    if scl_nodes:
        SCL = getattr(module, 'SHACLFunction', None)
        if not SCL:
            # Lazy-import SHACLFunction to prevent rdflib import error
            from .shacl_function import SHACLFunction

            setattr(module, 'SHACLFunction', SHACLFunction)
            SCL = SHACLFunction
        for n in scl_nodes:
            all_fns[n] = SCL(n, shacl_graph)
    if use_JSFunction and js_nodes:
        JSF = getattr(module, 'JSFunction', None)
        if not JSF:
            # Lazy-import JSFunction to prevent rdflib import error
            from pyshacl.extras.js.function import JSFunction  # noqa F401

            setattr(module, 'JSFunction', JSFunction)
            JSF = JSFunction
        for n in js_nodes:
            all_fns[n] = JSF(n, shacl_graph)
    return list(all_fns.values())


def apply_functions(fns: Sequence, data_graph: GraphLike):
    for f in fns:
        f.apply(data_graph)


def unapply_functions(fns: Sequence, data_graph: GraphLike):
    for f in fns:
        f.unapply(data_graph)
