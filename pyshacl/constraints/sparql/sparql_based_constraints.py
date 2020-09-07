# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#sparql-constraints
"""
from typing import Dict, List

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_deactivated, SH_message, SH_select
from pyshacl.errors import ConstraintLoadError, ValidationFailure
from pyshacl.pytypes import GraphLike
from pyshacl.sparql_query_helper import SPARQLQueryHelper


SH_sparql = SH.term('sparql')
SH_SPARQLConstraintComponent = SH.term('SPARQLConstraintComponent')


class SPARQLBasedConstraint(ConstraintComponent):
    """
    SHACL-SPARQL supports a constraint component that can be used to express restrictions based on a SPARQL SELECT query.
    Link:
    https://www.w3.org/TR/shacl/#sparql-constraints
    """

    def __init__(self, shape):
        super(SPARQLBasedConstraint, self).__init__(shape)
        sg = self.shape.sg.graph
        sparql_node_list = set(self.shape.objects(SH_sparql))
        if len(sparql_node_list) < 1:
            raise ConstraintLoadError(
                "SPARQLConstraintComponent must have at least one sh:sparql predicate.",
                "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent",
            )
        sparql_constraints = set()
        for s in iter(sparql_node_list):
            select_node_list = set(sg.objects(s, SH_select))
            if len(select_node_list) < 1:
                raise ConstraintLoadError(
                    "SPARQLConstraintComponent value for sh:select must have at least one sh:select predicate.",
                    "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent",
                )
            elif len(select_node_list) > 1:
                raise ConstraintLoadError(
                    "SPARQLConstraintComponent value for sh:select must have at most one sh:select predicate.",
                    "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent",
                )
            select_node = next(iter(select_node_list))
            if not (isinstance(select_node, rdflib.Literal) and isinstance(select_node.value, str)):
                raise ConstraintLoadError(
                    "SPARQLConstraintComponent value for sh:select must be a Literal with type xsd:string.",
                    "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent",
                )
            message_node_list = set(sg.objects(s, SH_message))
            msgs = None
            if len(message_node_list) > 0:
                message = next(iter(message_node_list))
                if not (isinstance(message, rdflib.Literal) and isinstance(message.value, str)):
                    raise ConstraintLoadError(
                        "SPARQLConstraintComponent value for sh:message must be a Literal with type xsd:string.",
                        "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent",
                    )
                msgs = message_node_list
            deactivated_node_list = set(sg.objects(s, SH_deactivated))
            deact = False
            if len(deactivated_node_list) > 0:
                deactivated = next(iter(deactivated_node_list))
                if not (isinstance(deactivated, rdflib.Literal) and isinstance(deactivated.value, bool)):
                    raise ConstraintLoadError(
                        "SPARQLConstraintComponent value for sh:deactivated must be "
                        "a Literal with type xsd:boolean.",
                        "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent",
                    )
                deact = bool(deactivated.value)
            query_helper = SPARQLQueryHelper(self.shape, s, select_node.value, messages=msgs, deactivated=deact)
            query_helper.collect_prefixes()
            sparql_constraints.add(query_helper)
        self.sparql_constraints = sparql_constraints

    @classmethod
    def constraint_parameters(cls):
        return [SH_sparql]

    @classmethod
    def constraint_name(cls):
        return "SPARQLConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_SPARQLConstraintComponent

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for query_helper in self.sparql_constraints:
            if query_helper.deactivated:
                continue
            _nc, _r = self._evaluate_sparql_constraint(query_helper, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_sparql_constraint(self, sparql_constraint, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        extra_messages = sparql_constraint.messages or None
        rept_kwargs = {'source_constraint': sparql_constraint.node, 'extra_messages': extra_messages}
        for f, value_nodes in f_v_dict.items():
            # we don't use value_nodes in the sparql constraint
            # All queries are done on the corresponding focus node.
            init_binds, sparql_text = sparql_constraint.pre_bind_variables(f)
            sparql_text = sparql_constraint.apply_prefixes(sparql_text)

            try:
                violating_vals = self._validate_sparql_query(sparql_text, init_binds, target_graph)

            except ValidationFailure as e:
                raise e
            if not self.shape.is_property_shape:
                result_val = f
            else:
                result_val = None
            for v in violating_vals:
                non_conformant = True
                if isinstance(v, bool) and v is True:
                    rept = self.make_v_result(target_graph, f, value_node=result_val, **rept_kwargs)
                elif isinstance(v, tuple):
                    t, p, v = v
                    if v is None:
                        v = result_val
                    rept = self.make_v_result(target_graph, t or f, value_node=v, result_path=p, **rept_kwargs)
                else:
                    rept = self.make_v_result(target_graph, f, value_node=v, **rept_kwargs)
                reports.append(rept)
        return non_conformant, reports

    def _validate_sparql_query(self, query, init_binds, target_graph):
        results = target_graph.query(query, initBindings=init_binds)
        if not results or len(results.bindings) < 1:
            return []
        violations = set()
        for r in results:
            try:
                p = r['path']
            except KeyError:
                p = None
            try:
                v = r['value']
            except KeyError:
                v = None
            try:
                t = r['this']
            except KeyError:
                t = None
            if p or v or t:
                violations.add((t, p, v))
            else:
                try:
                    _ = r['failure']
                    violations.add(True)
                except KeyError:
                    pass
        return violations
