#
#
import typing

from pyshacl.consts import SH
from pyshacl.rules.shacl_rule import SHACLRule

from .js_executable import JSExecutable


if typing.TYPE_CHECKING:
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph

SH_JSRule = SH.term('JSRule')


class JSRule(SHACLRule):
    __slots__ = ('js_exe',)

    def __init__(self, shape: 'Shape', rule_node):
        super(JSRule, self).__init__(shape, rule_node)
        shapes_graph = shape.sg  # type: ShapesGraph
        self.js_exe = JSExecutable(shapes_graph, rule_node)

    def apply(self, data_graph):
        focus_nodes = self.shape.focus_nodes(data_graph)  # uses target nodes to find focus nodes
        applicable_nodes = self.filter_conditions(focus_nodes, data_graph)
        sets_to_add = []
        for a in applicable_nodes:
            args_map = {"this": a}
            results = self.js_exe.execute(data_graph, args_map, mode="construct")
            triples = results['_result']
            if triples is not None and isinstance(triples, (list, tuple)):
                set_to_add = set()
                for t in triples:
                    s, p, o = t[:3]
                    set_to_add.add((s, p, o))
                sets_to_add.append(set_to_add)
        for s in sets_to_add:
            for t in s:
                data_graph.add(t)
        return
