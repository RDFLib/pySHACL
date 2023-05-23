# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-range
"""

from typing import Dict, List

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node
from pyshacl.rdfutil.compare import compare_literal

SH_MinExclusiveConstraintComponent = SH.MinExclusiveConstraintComponent
SH_MinInclusiveConstraintComponent = SH.MinInclusiveConstraintComponent
SH_minExclusive = SH.minExclusive
SH_minInclusive = SH.minInclusive
SH_MaxExclusiveConstraintComponent = SH.MaxExclusiveConstraintComponent
SH_MaxInclusiveConstraintComponent = SH.MaxInclusiveConstraintComponent
SH_maxExclusive = SH.maxExclusive
SH_maxInclusive = SH.maxInclusive


class MinExclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MinExclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $minExclusive < v does not return true, there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_MinExclusiveConstraintComponent

    def __init__(self, shape):
        super(MinExclusiveConstraintComponent, self).__init__(shape)
        min_vals = list(self.shape.objects(SH_minExclusive))
        if len(min_vals) < 1:
            raise ConstraintLoadError(
                "MinExclusiveConstraintComponent must have at least one sh:minExclusive predicate.",
                "https://www.w3.org/TR/shacl/#MinExclusiveConstraintComponent",
            )
        self.min_vals = min_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_minExclusive]

    @classmethod
    def constraint_name(cls):
        return "MinExclusiveConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.min_vals) < 2:
            m = "Value is not > {}".format(stringify_node(self.shape.sg.graph, self.min_vals[0]))
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, c) for c in self.min_vals)
            m = "Value is not > in ({})".format(rules)
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for m_val in self.min_vals:
            _nc, _r = self._evaluate_min_rule(m_val, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_min_rule(self, m_val, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(m_val, rdflib.Literal)
        min_is_string = isinstance(m_val.value, str)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass val comparison
                    pass
                elif isinstance(v, rdflib.URIRef):
                    # TODO: Don't know if URIRefs can be compared here
                    pass
                elif isinstance(v, rdflib.Literal):
                    v_is_string = isinstance(v.value, str)
                    if min_is_string and not v_is_string:
                        pass
                    elif v_is_string and not min_is_string:
                        pass
                    else:
                        try:
                            # pass if v > m_val
                            cmp = compare_literal(v, m_val)
                            flag = cmp > 0
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError("Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class MinInclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MinInclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $minInclusive <= v does not return true, there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_MinInclusiveConstraintComponent

    def __init__(self, shape):
        super(MinInclusiveConstraintComponent, self).__init__(shape)
        min_vals = list(self.shape.objects(SH_minInclusive))
        if len(min_vals) < 1:
            raise ConstraintLoadError(
                "MinInclusiveConstraintComponent must have at least one sh:minInclusive predicate.",
                "https://www.w3.org/TR/shacl/#MinInclusiveConstraintComponent",
            )
        self.min_vals = min_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_minInclusive]

    @classmethod
    def constraint_name(cls):
        return "MinInclusiveConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.min_vals) < 2:
            m = "Value is not >= {}".format(stringify_node(self.shape.sg.graph, self.min_vals[0]))
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, c) for c in self.min_vals)
            m = "Value is not >= in ({})".format(rules)
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for m_val in self.min_vals:
            _nc, _r = self._evaluate_min_rule(m_val, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_min_rule(self, m_val, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(m_val, rdflib.Literal)
        min_is_string = isinstance(m_val.value, str)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass val comparison
                    pass
                elif isinstance(v, rdflib.URIRef):
                    # TODO: Don't know if URIRefs can be compared here
                    pass
                elif isinstance(v, rdflib.Literal):
                    v_is_string = isinstance(v.value, str)
                    if min_is_string and not v_is_string:
                        pass
                    elif v_is_string and not min_is_string:
                        pass
                    else:
                        try:
                            # pass if v >= m_val
                            cmp = compare_literal(v, m_val)
                            flag = cmp >= 0
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError("Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class MaxExclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MaxExclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $maxExclusive > v does not return true, there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_MaxExclusiveConstraintComponent

    def __init__(self, shape):
        super(MaxExclusiveConstraintComponent, self).__init__(shape)
        max_vals = list(self.shape.objects(SH_maxExclusive))
        if len(max_vals) < 1:
            raise ConstraintLoadError(
                "MaxExclusiveConstraintComponent must have at least one sh:minExclusive predicate.",
                "https://www.w3.org/TR/shacl/#MaxExclusiveConstraintComponent",
            )
        self.max_vals = max_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxExclusive]

    @classmethod
    def constraint_name(cls):
        return "MaxExclusiveConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.max_vals) < 2:
            m = "Value is not < {}".format(stringify_node(self.shape.sg.graph, self.max_vals[0]))
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, c) for c in self.max_vals)
            m = "Value is not < in ({})".format(rules)
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for m_val in self.max_vals:
            _nc, _r = self._evaluate_max_rule(m_val, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_max_rule(self, m_val, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(m_val, rdflib.Literal)
        max_is_string = isinstance(m_val.value, str)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass val comparison
                    pass
                elif isinstance(v, rdflib.URIRef):
                    # TODO: Don't know if URIRefs can be compared here
                    pass
                elif isinstance(v, rdflib.Literal):
                    v_is_string = isinstance(v.value, str)
                    if max_is_string and not v_is_string:
                        pass
                    elif v_is_string and not max_is_string:
                        pass
                    else:
                        try:
                            # pass if v < m_val
                            cmp = compare_literal(v, m_val)
                            flag = cmp < 0
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError("Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class MaxInclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MaxInclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $maxInclusive >= v does not return true, there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_MaxInclusiveConstraintComponent

    def __init__(self, shape):
        super(MaxInclusiveConstraintComponent, self).__init__(shape)
        max_vals = list(self.shape.objects(SH_maxInclusive))
        if len(max_vals) < 1:
            raise ConstraintLoadError(
                "MaxInclusiveConstraintComponent must have at least one sh:minInclusive predicate.",
                "https://www.w3.org/TR/shacl/#MaxInclusiveConstraintComponent",
            )
        self.max_vals = max_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxInclusive]

    @classmethod
    def constraint_name(cls):
        return "MaxInclusiveConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.max_vals) < 2:
            m = "Value is not <= {}".format(stringify_node(self.shape.sg.graph, self.max_vals[0]))
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, c) for c in self.max_vals)
            m = "Value is not <= in ({})".format(rules)
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for m_val in self.max_vals:
            _nc, _r = self._evaluate_max_rule(m_val, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_max_rule(self, m_val, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(m_val, rdflib.Literal)
        max_is_string = isinstance(m_val.value, str)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass val comparison
                    pass
                elif isinstance(v, rdflib.URIRef):
                    # TODO: Don't know if URIRefs can be compared here
                    pass
                elif isinstance(v, rdflib.Literal):
                    v_is_string = isinstance(v.value, str)
                    if max_is_string and not v_is_string:
                        pass
                    elif v_is_string and not max_is_string:
                        pass
                    else:
                        try:
                            # pass if v <= m_val
                            cmp = compare_literal(v, m_val)
                            flag = cmp <= 0
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError("Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports
