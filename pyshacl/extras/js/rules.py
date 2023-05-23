#
#
import typing

from pyshacl.consts import SH
from pyshacl.errors import ReportableRuntimeError
from pyshacl.rules.shacl_rule import SHACLRule

from .js_executable import JSExecutable

if typing.TYPE_CHECKING:
    from pyshacl.pytypes import GraphLike
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph

SH_JSRule = SH.JSRule


class JSRule(SHACLRule):
    __slots__ = ('js_exe',)

    def __init__(self, shape: 'Shape', rule_node, **kwargs):
        super(JSRule, self).__init__(shape, rule_node, **kwargs)
        shapes_graph: 'ShapesGraph' = shape.sg
        self.js_exe = JSExecutable(shapes_graph, rule_node)

    def apply(self, data_graph: 'GraphLike') -> int:
        focus_nodes = self.shape.focus_nodes(data_graph)  # uses target nodes to find focus nodes
        all_added = 0
        iterate_limit = 100
        while True:
            if iterate_limit < 1:
                raise ReportableRuntimeError("Local rule iteration exceeded iteration limit of 100.")
            iterate_limit -= 1
            added = 0
            applicable_nodes = self.filter_conditions(focus_nodes, data_graph)
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
                all_added += added
                for s in sets_to_add:
                    for t in s:
                        data_graph.add(t)
                if self.iterate:
                    continue  # Jump up to iterate
                else:
                    break  # Don't iterate
            break
        return all_added
