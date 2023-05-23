#
#
import typing
from typing import Dict, List

from rdflib import Literal

from pyshacl.constraints import ConstraintComponent
from pyshacl.consts import SH, SH_js, SH_message
from pyshacl.errors import ConstraintLoadError
from pyshacl.pytypes import GraphLike

from .js_executable import JSExecutable

if typing.TYPE_CHECKING:
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph


SH_JSConstraint = SH.JSConstraint
SH_JSConstraintComponent = SH.JSConstraintComponent


class JSConstraintImpl(JSExecutable):
    __slots__ = ("messages",)

    def __init__(self, shapes_graph: 'ShapesGraph', node):
        super(JSConstraintImpl, self).__init__(shapes_graph, node)
        msgs_iter = shapes_graph.objects(node, SH_message)
        self.messages = []
        for m in msgs_iter:
            if not isinstance(m, Literal):
                raise ConstraintLoadError(
                    "JSConstraint sh:message must be a RDF Literal.",
                    "https://www.w3.org/TR/shacl-js/#js-constraints",
                )
            if not isinstance(m.value, str):
                raise ConstraintLoadError(
                    "JSConstraint sh:message must be a RDF Literal with type string.",
                    "https://www.w3.org/TR/shacl-js/#js-constraints",
                )
            self.messages.append(m)

    def make_messages(self, args_map=None):
        if args_map is None:
            return self.messages
        ret_msgs = []
        for m in self.messages:
            this_m = m.value[:]
            for a, v in args_map.items():
                replace_me = "{$" + str(a) + "}"
                if isinstance(v, Literal):
                    v = v.value
                this_m = this_m.replace(replace_me, str(v))
            ret_msgs.append(Literal(this_m))
        return ret_msgs


class JSConstraint(ConstraintComponent):
    shacl_constraint_component = SH_JSConstraint

    def __init__(self, shape: 'Shape'):
        super(JSConstraint, self).__init__(shape)
        js_decls = list(self.shape.objects(SH_js))
        if len(js_decls) < 1:
            raise ConstraintLoadError(
                "JSConstraint must have at least one sh:js predicate.",
                "https://www.w3.org/TR/shacl-js/#js-constraints",
            )
        self.js_impls = [JSConstraintImpl(shape.sg, j) for j in js_decls]

    @classmethod
    def constraint_parameters(cls):
        return [SH_js]

    @classmethod
    def constraint_name(cls):
        return "JSConstraint"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        return [Literal("Javascript Function generated constraint validation reports.")]

    def evaluate(self, data_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type data_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False
        for c in self.js_impls:
            _n, _r = self._evaluate_js_exe(data_graph, focus_value_nodes, c)
            non_conformant = non_conformant or _n
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_js_exe(self, data_graph, f_v_dict, js_impl: JSConstraintImpl):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                failed = False
                try:
                    args_map = {'this': f, 'value': v}
                    if self.shape.is_property_shape:
                        args_map['path'] = self.shape.path()
                    res_dict = js_impl.execute(data_graph, args_map)
                    result = res_dict['_result']
                    if result is True:
                        continue
                    msgs = js_impl.make_messages(args_map)
                    if isinstance(result, list):
                        pass
                    else:
                        result = [result]
                    for res in result:
                        if isinstance(res, Literal):
                            res = res.value
                        if isinstance(res, bool):
                            if res:
                                continue
                            else:
                                failed = True
                                reports.append(self.make_v_result(data_graph, f, value_node=v, extra_messages=msgs))
                        elif isinstance(res, str):
                            failed = True
                            msgs.append(Literal(res))
                            reports.append(self.make_v_result(data_graph, f, value_node=v, extra_messages=msgs))
                        elif isinstance(res, dict):
                            failed = True
                            args_map2 = args_map.copy()
                            val = res.get('value', None)
                            if val is None:
                                val = v
                            args_map2['value'] = val
                            path = res.get('path', None) if not self.shape.is_property_shape else None
                            if path is not None:
                                args_map2['value'] = path
                            msgs = js_impl.make_messages(args_map2)
                            message = res.get('message', None)
                            if message is not None:
                                msgs.append(Literal(message))
                            reports.append(
                                self.make_v_result(
                                    data_graph, f, value_node=val, result_path=path, extra_messages=msgs
                                )
                            )
                except Exception as e:
                    print(e)
                    raise
                if failed:
                    non_conformant = True
        return non_conformant, reports
