# -*- coding: utf-8 -*-
#
"""
SHACL-AF Advanced Constraints
https://www.w3.org/TR/shacl-af/#ExpressionConstraintComponent
"""
import typing
from typing import Dict, List

from rdflib import Literal

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_message
from pyshacl.errors import ConstraintLoadError
from pyshacl.helper.expression_helper import nodes_from_node_expression
from pyshacl.pytypes import GraphLike

SH_expression = SH.expression
SH_ExpressionConstraintComponent = SH.ExpressionConstraintComponent

if typing.TYPE_CHECKING:
    from pyshacl.shape import Shape


class ExpressionConstraint(ConstraintComponent):
    shacl_constraint_component = SH_ExpressionConstraintComponent

    def __init__(self, shape: 'Shape'):
        super(ExpressionConstraint, self).__init__(shape)
        self.expr_nodes = list(self.shape.objects(SH_expression))
        if len(self.expr_nodes) < 1:
            raise ConstraintLoadError(
                "ExpressionConstraintComponent must have at least one sh:expression predicate.",
                "https://www.w3.org/TR/shacl-af/#ExpressionConstraintComponent",
            )

    @classmethod
    def constraint_parameters(cls):
        return [SH_expression]

    @classmethod
    def constraint_name(cls):
        return "ExpressionConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        return [Literal("Expression evaluation generated constraint did not return true.")]

    def evaluate(self, data_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type data_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False
        for n in self.expr_nodes:
            _n, _r = self._evaluate_expression(data_graph, focus_value_nodes, n)
            non_conformant = non_conformant or _n
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_expression(self, data_graph, f_v_dict, expr):
        reports = []
        non_conformant = False
        messages = list(self.shape.sg.objects(expr, SH_message))
        if len(messages):
            messages = [next(iter(messages))]
        else:
            messages = None
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                try:
                    n_set = nodes_from_node_expression(expr, v, data_graph, self.shape.sg)
                    if (
                        isinstance(n_set, (list, set))
                        and len(n_set) == 1
                        and next(iter(n_set)) in (Literal(True), True)
                    ):
                        ...
                    else:
                        non_conformant = non_conformant or True
                        reports.append(
                            self.make_v_result(
                                data_graph, f, value_node=v, source_constraint=expr, extra_messages=messages
                            )
                        )
                except Exception as e:
                    print(e)
                    raise
        return non_conformant, reports
