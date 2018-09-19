# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-logical
"""
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError, ValidationFailure, ReportableRuntimeError

SH_not = SH.term('not')
SH_and = SH.term('and')
SH_or = SH.term('or')
SH_xone = SH.term('xone')

SH_NotConstraintComponent = SH.term('NotConstraintComponent')
SH_AndConstraintComponent = SH.term('AndConstraintComponent')
SH_OrConstraintComponent = SH.term('OrConstraintComponent')
SH_XoneConstraintComponent = SH.term('XoneConstraintComponent')


class NotConstraintComponent(ConstraintComponent):
    """
    sh:not specifies the condition that each value node cannot conform to a given shape. This is comparable to negation and the logical "not" operator.
    Link:
    https://www.w3.org/TR/shacl/#NotConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be reported if the conformance checking of v against the shape $not produces a failure. Otherwise, if v conforms to the shape $not, there is validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(NotConstraintComponent, self).__init__(shape)
        not_list = list(self.shape.objects(SH_not))
        if len(not_list) < 1:
            raise ConstraintLoadError(
                "NotConstraintComponent must have at least one sh:not predicate.",
                "https://www.w3.org/TR/shacl/#NotConstraintComponent")
        if len(not_list) > 1:
            raise ConstraintLoadError(
                "NotConstraintComponent must have at most one sh:not predicate.",
                "https://www.w3.org/TR/shacl/#NotConstraintComponent")
        self.not_list = not_list

    @classmethod
    def constraint_parameters(cls):
        return [SH_not]

    @classmethod
    def constraint_name(cls):
        return "NotConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_NotConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for not_c in self.not_list:
            _nc, _r = self._evaluate_not_constraint(not_c, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_not_constraint(self, not_c, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        not_shape = self.shape.get_other_shape(not_c)
        if not not_shape:
            raise ReportableRuntimeError(
                "Shape pointed to by sh:not does not exist or is not "
                "a well-formed SHACL Shape.")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                try:
                    _is_conform, _r = not_shape.validate(target_graph, focus=v)
                except ValidationFailure as e:
                    raise e
                if _is_conform:
                    # in this case, we _dont_ want to conform!
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class AndConstraintComponent(ConstraintComponent):
    """
    sh:and specifies the condition that each value node conforms to all provided shapes. This is comparable to conjunction and the logical "and" operator.
    Link:
    https://www.w3.org/TR/shacl/#AndConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against any of the members of $and produces a failure. Otherwise, if v does not conform to each member of $and, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(AndConstraintComponent, self).__init__(shape)
        and_list = list(self.shape.objects(SH_and))
        if len(and_list) < 1:
            raise ConstraintLoadError(
                "AndConstraintComponent must have at least one sh:and predicate.",
                "https://www.w3.org/TR/shacl/#AndConstraintComponent")
        self.and_list = and_list

    @classmethod
    def constraint_parameters(cls):
        return [SH_and]

    @classmethod
    def constraint_name(cls):
        return "AndConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_AndConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for and_c in self.and_list:
            _nc, _r = self._evaluate_and_constraint(and_c, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_and_constraint(self, and_c, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        sg = self.shape.sg.graph
        and_list = set(sg.items(and_c))
        if len(and_list) < 1:
            raise ReportableRuntimeError(
                "The list associated with sh:and is not a "
                "valid RDF list.")
        and_shapes = set()
        for a in and_list:
            and_shape = self.shape.get_other_shape(a)
            if not and_shape:
                raise ReportableRuntimeError(
                    "Shape pointed to by sh:and does not exist or "
                    "is not a well-formed SHACL Shape.")
            and_shapes.add(and_shape)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                passed_all = True
                for and_shape in and_shapes:
                    try:
                        _is_conform, _r = and_shape.validate(target_graph, focus=v)
                    except ValidationFailure as e:
                        raise e
                    passed_all = passed_all and _is_conform
                if not passed_all:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class OrConstraintComponent(ConstraintComponent):
    """
    sh:or specifies the condition that each value node conforms to at least one of the provided shapes. This is comparable to disjunction and the logical "or" operator.
    Link:
    https://www.w3.org/TR/shacl/#OrConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against any of the members produces a failure. Otherwise, if v conforms to none of the members of $or there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(OrConstraintComponent, self).__init__(shape)
        or_list = list(self.shape.objects(SH_or))
        if len(or_list) < 1:
            raise ConstraintLoadError(
                "OrConstraintComponent must have at least one sh:or predicate.",
                "https://www.w3.org/TR/shacl/#OrConstraintComponent")
        self.or_list = or_list

    @classmethod
    def constraint_parameters(cls):
        return [SH_or]

    @classmethod
    def constraint_name(cls):
        return "OrConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_OrConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for or_c in self.or_list:
            _nc, _r = self._evaluate_or_constraint(or_c, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_or_constraint(self, or_c, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        sg = self.shape.sg.graph
        or_list = set(sg.items(or_c))
        if len(or_list) < 1:
            raise ReportableRuntimeError(
                "The list associated with sh:or "
                "is not a valid RDF list.")
        or_shapes = set()
        for o in or_list:
            or_shape = self.shape.get_other_shape(o)
            if not or_shape:
                raise ReportableRuntimeError(
                    "Shape pointed to by sh:or does not exist or "
                    "is not a well-formed SHACL Shape.")
            or_shapes.add(or_shape)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                passed_any = False
                for or_shape in or_shapes:
                    try:
                        _is_conform, _r = or_shape.validate(target_graph, focus=v)
                    except ValidationFailure as e:
                        raise e
                    passed_any = passed_any or _is_conform
                if not passed_any:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class XoneConstraintComponent(ConstraintComponent):
    """
    sh:or specifies the condition that each value node conforms to at least one of the provided shapes. This is comparable to disjunction and the logical "or" operator.
    Link:
    https://www.w3.org/TR/shacl/#XoneConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against any of the members produces a failure. Otherwise, if v conforms to none of the members of $or there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(XoneConstraintComponent, self).__init__(shape)
        xone_nodes = list(self.shape.objects(SH_xone))
        if len(xone_nodes) < 1:
            raise ConstraintLoadError(
                "XoneConstraintComponent must have at least one sh:xone predicate.",
                "https://www.w3.org/TR/shacl/#XoneConstraintComponent")
        self.xone_nodes = xone_nodes

    @classmethod
    def constraint_parameters(cls):
        return [SH_xone]

    @classmethod
    def constraint_name(cls):
        return "XoneConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_XoneConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for xone_c in self.xone_nodes:
            _nc, _r = self._evaluate_xone_constraint(xone_c, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_xone_constraint(self, xone_c, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        sg = self.shape.sg.graph
        xone_list = list(sg.items(xone_c))
        if len(xone_list) < 1:
            raise ReportableRuntimeError(
                "The list associated with sh:xone is not "
                "a valid RDF list.")
        xone_shapes = list()
        for x in xone_list:
            xone_shape = self.shape.get_other_shape(x)
            if not xone_shape:
                raise ReportableRuntimeError(
                    "Shape pointed to by sh:xone does not exist "
                    "or is not a well-formed SHACL Shape.")
            xone_shapes.append(xone_shape)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                passed_count = 0
                for xone_shape in xone_shapes:
                    try:
                        _is_conform, _r = xone_shape.validate(target_graph, focus=v)
                    except ValidationFailure as e:
                        raise e
                    if _is_conform:
                        passed_count += 1
                if not (passed_count == 1):
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports

