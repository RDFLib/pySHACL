#
#
from typing import TYPE_CHECKING, List, Optional, Sequence, Union

import rdflib

from pyshacl.consts import SH
from pyshacl.errors import ReportableRuntimeError
from pyshacl.rules.shacl_rule import SHACLRule

from .js_executable import JSExecutable

if TYPE_CHECKING:
    from rdflib.term import URIRef

    from pyshacl.pytypes import GraphLike, RDFNode, SHACLExecutor
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph

SH_JSRule = SH.JSRule

JS_RULE_ITERATE_LIMIT = 100


class JSRule(SHACLRule):
    __slots__ = ('js_exe',)

    def __init__(self, executor: 'SHACLExecutor', shape: 'Shape', rule_node, **kwargs):
        super(JSRule, self).__init__(executor, shape, rule_node, **kwargs)
        shapes_graph: 'ShapesGraph' = shape.sg
        self.js_exe = JSExecutable(shapes_graph, rule_node)

    def apply(
        self,
        data_graph: 'GraphLike',
        focus_nodes: Union[Sequence['RDFNode'], None] = None,
        target_graph_identifier: Optional['URIRef'] = None,
    ) -> int:
        focus_list: Sequence['RDFNode']
        if focus_nodes is not None:
            focus_list = list(focus_nodes)
        else:
            focus_list = list(self.shape.focus_nodes(data_graph))
        if self.executor.focus_nodes is not None and len(self.executor.focus_nodes) > 0:
            filtered_focus_nodes: List[Union[rdflib.URIRef]] = []
            for _fo in focus_list:  # type: RDFNode
                if isinstance(_fo, rdflib.URIRef) and _fo in self.executor.focus_nodes:
                    filtered_focus_nodes.append(_fo)
            len_filtered_focus = len(filtered_focus_nodes)
            if len_filtered_focus < 1:
                return 0
            focus_list = filtered_focus_nodes
        all_added = 0
        iterate_limit = int(JS_RULE_ITERATE_LIMIT)
        while True:
            if iterate_limit < 1:
                raise ReportableRuntimeError(f"JS rule iteration exceeded iteration limit of {JS_RULE_ITERATE_LIMIT}.")
            iterate_limit -= 1
            added = 0
            applicable_nodes = self.filter_conditions(focus_list, data_graph)
            sets_to_add = []
            for a in applicable_nodes:
                args_map = {"this": a}
                results = self.js_exe.execute(data_graph, args_map, mode="construct")
                triples = results['_result']
                this_added = False
                if triples is not None and isinstance(triples, (list, tuple)):
                    set_to_add = set()
                    for t in triples:
                        s, p, o = tr = t[:3]
                        if not this_added and tr not in data_graph:
                            this_added = True
                        set_to_add.add(tr)
                    sets_to_add.append(set_to_add)
                if this_added:
                    added += 1
            if added > 0:
                if isinstance(data_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
                    if target_graph_identifier is not None:
                        target_graph = data_graph.get_context(target_graph_identifier)
                    else:
                        target_graph = data_graph.default_context
                else:
                    target_graph = data_graph
                for s in sets_to_add:
                    for t in s:
                        target_graph.add(t)
                all_added += added
                if self.iterate:
                    continue  # Jump up to iterate
                else:
                    break  # Don't iterate
            break
        return all_added
