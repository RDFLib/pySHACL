import typing

from typing import List, Sequence, Union

from pyshacl.consts import RDF_type, SH_ask, SH_select, SH_SHACLFunction, SH_SPARQLFunction
from pyshacl.pytypes import GraphLike

from .shacl_function import SHACLFunction, SPARQLFunction


if typing.TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph


def gather_functions(shacl_graph: 'ShapesGraph') -> Sequence[Union['SHACLFunction', 'SPARQLFunction']]:
    """

    :param shacl_graph:
    :type shacl_graph: ShapesGraph
    :return:
    :rtype: [SHACLRule]
    """
    spq_nodes = set(shacl_graph.subjects(RDF_type, SH_SPARQLFunction))
    scl_nodes = set(shacl_graph.subjects(RDF_type, SH_SHACLFunction)).difference(spq_nodes)
    to_swap = set()
    for n in scl_nodes:
        has_select = len(shacl_graph.objects(n, SH_select)) > 0
        has_ask = len(shacl_graph.objects(n, SH_ask)) > 0
        if has_ask or has_select:
            to_swap.add(n)
    for n in to_swap:
        scl_nodes.remove(n)
        spq_nodes.add(n)

    all_fns: List[Union['SHACLFunction', 'SPARQLFunction']] = []
    for n in spq_nodes:
        all_fns.append(SPARQLFunction(n, shacl_graph))
    for n in scl_nodes:
        all_fns.append(SHACLFunction(n, shacl_graph))
    return all_fns


def apply_functions(fns: Sequence, data_graph: GraphLike):
    for f in fns:
        f.apply(data_graph)


def unapply_functions(fns: Sequence, data_graph: GraphLike):
    for f in fns:
        f.unapply(data_graph)
