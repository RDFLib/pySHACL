#
#
import typing
from typing import Dict, List
from warnings import warn

from rdflib import URIRef

from pyshacl.consts import SH_JSTargetType
from pyshacl.errors import ShapeLoadError
from pyshacl.target import BoundSHACLTargetType, SHACLTargetType

from .js_executable import JSExecutable

if typing.TYPE_CHECKING:
    from pyshacl.pytypes import GraphLike
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph


class JSTarget(JSExecutable):
    def __init__(self, shapes_graph: 'ShapesGraph', exe_node):
        super(JSTarget, self).__init__(shapes_graph, exe_node)

    def find_targets(self, data_graph):
        results = self.execute(data_graph, {}, mode='target')
        return [u for u in results['_result'] if isinstance(u, URIRef)]


class BoundJSTargetType(BoundSHACLTargetType):
    __slots__ = ('params_kv',)

    def __init__(self, target_type: 'JSTargetType', target_declaration, shape: 'Shape', params_kv):
        super(BoundJSTargetType, self).__init__(target_type, target_declaration, shape)
        self.params_kv = params_kv  # type: dict

    @classmethod
    def constraint_parameters(cls):
        return []

    @classmethod
    def constraint_name(cls):
        return "JSTargetType"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_JSTargetType

    def evaluate(self, target_graph: 'GraphLike', focus_value_nodes: Dict, _evaluation_path: List):
        raise NotImplementedError()

    def find_targets(self, data_graph):
        results = self.target_type.js_exe.execute(data_graph, self.params_kv, mode='target')
        return [u for u in results['_result'] if isinstance(u, URIRef)]


class JSTargetType(SHACLTargetType):
    __slots__ = ('js_exe',)

    def __init__(self, tt_node, sg: 'ShapesGraph'):
        super(JSTargetType, self).__init__(tt_node, sg)
        self.js_exe = JSExecutable(sg, tt_node)

    def check_params(self, target_declaration):
        param_kv = {}
        for p in self.parameters:
            path = p.path()
            name = p.localname
            vals = set(self.sg.objects(target_declaration, path))
            if len(vals) < 1:
                if p.optional:
                    continue
                raise ShapeLoadError(
                    "sh:target does not have a value for {}".format(name),
                    "https://www.w3.org/TR/shacl-js/#JSTargetType",
                )
            if len(vals) > 1:
                warn(Warning("Found more than one value for {} on sh:target. Using just first one.".format(name)))
            param_kv[name] = next(iter(vals))
        return param_kv

    def bind(self, shape, target_declaration):
        param_vals = self.check_params(target_declaration)
        return BoundJSTargetType(self, target_declaration, shape, param_vals)
