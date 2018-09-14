# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-count
"""
import rdflib
from rdflib.term import Literal
from rdflib.namespace import XSD
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError

XSD_integer = XSD.term('integer')
SH_minCount = SH.term('minCount')
SH_maxCount = SH.term('maxCount')

SH_MinCountConstraintComponent = SH.term('MinCountConstraintComponent')
SH_MaxCountConstraintComponent = SH.term('MaxCountConstraintComponent')


class MinCountConstraintComponent(ConstraintComponent):
    """
    sh:minCount specifies the minimum number of value nodes that satisfy the condition. If the minimum cardinality value is 0 then this constraint is always satisfied and so may be omitted.
    Link:
    https://www.w3.org/TR/shacl/#MinCountConstraintComponent
    Textual Definition:
    If the number of value nodes is less than $minCount, there is a validation result.
    """

    def __init__(self, shape):
        super(MinCountConstraintComponent, self).__init__(shape)
        min_count = list(self.shape.objects(SH_minCount))
        if len(min_count) < 1:
            raise ConstraintLoadError(
                "MinCountConstraintComponent must have at least one sh:minCount predicate.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent")
        if len(min_count) > 1:
            raise ConstraintLoadError(
                "MinCountConstraintComponent must have at most one sh:minCount predicate.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent")
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "MinCountConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent")
        self.min_count = min_count[0]
        if not (isinstance(self.min_count, Literal) and
                self.min_count.datatype == XSD_integer):
            raise ConstraintLoadError(
                "MinCountConstraintComponent sh:minCount must be a literal with datatype xsd:integer.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent")
        if int(self.min_count.value) < 0:
            raise ConstraintLoadError(
                "MinCountConstraintComponent sh:minCount must be an integer >= 0.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent")

    @classmethod
    def constraint_parameters(cls):
        return [SH_minCount]

    @classmethod
    def constraint_name(cls):
        return "MinCountConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MinCountConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        min_count = int(self.min_count.value)
        if min_count == 0:
            # MinCount of zero always passes
            return True, []
        reports = []
        non_conformant = False

        for f, value_nodes in focus_value_nodes.items():
            flag = len(value_nodes) >= min_count
            if not flag:
                non_conformant = True
                rept = self.make_v_result(f)
                reports.append(rept)
        return (not non_conformant), reports


class MaxCountConstraintComponent(ConstraintComponent):
    """
    sh:maxCount specifies the maximum number of value nodes that satisfy the condition.
    Link: https://www.w3.org/TR/shacl/#MaxCountConstraintComponent
    Textual Definition:
    If the number of value nodes is greater than $maxCount, there is a validation result.
    """

    def __init__(self, shape):
        super(MaxCountConstraintComponent, self).__init__(shape)
        max_count = list(self.shape.objects(SH_maxCount))
        if len(max_count) < 1:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent must have at least one sh:maxCount predicate.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent")
        if len(max_count) > 1:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent must have at most one sh:maxCount predicate.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent")
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent")
        self.max_count = max_count[0]
        if not (isinstance(self.max_count, Literal) and
                self.max_count.datatype == XSD_integer):
            raise ConstraintLoadError(
                "MaxCountConstraintComponent sh:maxCount must be a literal with datatype xsd:integer.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent")
        if int(self.max_count.value) < 0:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent sh:maxCount must be an integer >= 0.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent")

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxCount]

    @classmethod
    def constraint_name(cls):
        return "MaxCountConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MaxCountConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        max_count = int(self.max_count.value)
        reports = []
        non_conformant = False

        for f, value_nodes in focus_value_nodes.items():
            flag = len(value_nodes) <= max_count
            if not flag:
                non_conformant = True
                rept = self.make_v_result(f)
                reports.append(rept)
        return (not non_conformant), reports

