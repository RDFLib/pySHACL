# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-range
"""
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError

SH_MinExclusiveConstraintComponent = SH.term('MinExclusiveConstraintComponent')
SH_MinInclusiveConstraintComponent = SH.term('MinInclusiveConstraintComponent')
SH_minExclusive = SH.term('minExclusive')
SH_minInclusive = SH.term('minInclusive')
SH_MaxExclusiveConstraintComponent = SH.term('MaxExclusiveConstraintComponent')
SH_MaxInclusiveConstraintComponent = SH.term('MaxInclusiveConstraintComponent')
SH_maxExclusive = SH.term('maxExclusive')
SH_maxInclusive = SH.term('maxInclusive')


class MinExclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MinExclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $minExclusive < v does not return true, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(MinExclusiveConstraintComponent, self).__init__(shape)
        min_vals = list(self.shape.objects(SH_minExclusive))
        if len(min_vals) < 1:
            raise ConstraintLoadError(
                "MinExclusiveConstraintComponent must have at least one sh:minExclusive predicate.",
                "https://www.w3.org/TR/shacl/#MinExclusiveConstraintComponent")
        self.min_vals = min_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_minExclusive]

    @classmethod
    def constraint_name(cls):
        return "MinExclusiveConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MinExclusiveConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for m_val in self.min_vals:
            _nc, _r = self._evaluate_min_rule(m_val, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_min_rule(self, m_val, f_v_dict):
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
                            r = m_val < v
                            flag = r
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError(
                        "Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports

class MinInclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MinInclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $minInclusive <= v does not return true, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(MinInclusiveConstraintComponent, self).__init__(shape)
        min_vals = list(self.shape.objects(SH_minInclusive))
        if len(min_vals) < 1:
            raise ConstraintLoadError(
                "MinInclusiveConstraintComponent must have at least one sh:minInclusive predicate.",
                "https://www.w3.org/TR/shacl/#MinInclusiveConstraintComponent")
        self.min_vals = min_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_minInclusive]

    @classmethod
    def constraint_name(cls):
        return "MinInclusiveConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MinInclusiveConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for m_val in self.min_vals:
            _nc, _r = self._evaluate_min_rule(m_val, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_min_rule(self, m_val, f_v_dict):
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
                            r = m_val <= v
                            flag = r
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError(
                        "Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class MaxExclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MaxExclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $maxExclusive > v does not return true, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(MaxExclusiveConstraintComponent, self).__init__(shape)
        max_vals = list(self.shape.objects(SH_maxExclusive))
        if len(max_vals) < 1:
            raise ConstraintLoadError(
                "MaxExclusiveConstraintComponent must have at least one sh:minExclusive predicate.",
                "https://www.w3.org/TR/shacl/#MaxExclusiveConstraintComponent")
        self.max_vals = max_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxExclusive]

    @classmethod
    def constraint_name(cls):
        return "MaxExclusiveConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MaxExclusiveConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for m_val in self.max_vals:
            _nc, _r = self._evaluate_max_rule(m_val, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_max_rule(self, m_val, f_v_dict):
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
                            r = m_val > v
                            flag = r
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError(
                        "Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class MaxInclusiveConstraintComponent(ConstraintComponent):
    """
    Link:
    https://www.w3.org/TR/shacl/#MaxInclusiveConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $maxInclusive >= v does not return true, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(MaxInclusiveConstraintComponent, self).__init__(shape)
        max_vals = list(self.shape.objects(SH_maxInclusive))
        if len(max_vals) < 1:
            raise ConstraintLoadError(
                "MaxInclusiveConstraintComponent must have at least one sh:minInclusive predicate.",
                "https://www.w3.org/TR/shacl/#MaxInclusiveConstraintComponent")
        self.max_vals = max_vals

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxInclusive]

    @classmethod
    def constraint_name(cls):
        return "MaxInclusiveConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MaxInclusiveConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for m_val in self.max_vals:
            _nc, _r = self._evaluate_max_rule(m_val, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_max_rule(self, m_val, f_v_dict):
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
                            r = m_val >= v
                            flag = r
                        except (TypeError, NotImplementedError):
                            flag = False
                else:
                    raise ReportableRuntimeError(
                        "Not sure how to compare anything else.")
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports
