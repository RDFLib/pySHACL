# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-count
"""
from typing import Dict, List

from rdflib.namespace import XSD
from rdflib.term import Literal

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node

XSD_integer = XSD.integer
SH_minCount = SH.minCount
SH_maxCount = SH.maxCount

SH_MinCountConstraintComponent = SH.MinCountConstraintComponent
SH_MaxCountConstraintComponent = SH.MaxCountConstraintComponent


class MinCountConstraintComponent(ConstraintComponent):
    """
    sh:minCount specifies the minimum number of value nodes that satisfy the condition. If the minimum cardinality value is 0 then this constraint is always satisfied and so may be omitted.
    Link:
    https://www.w3.org/TR/shacl/#MinCountConstraintComponent
    Textual Definition:
    If the number of value nodes is less than $minCount, there is a validation result.
    """

    shacl_constraint_component = SH_MinCountConstraintComponent

    def __init__(self, shape):
        super(MinCountConstraintComponent, self).__init__(shape)
        min_count = list(self.shape.objects(SH_minCount))
        if len(min_count) < 1:
            raise ConstraintLoadError(
                "MinCountConstraintComponent must have at least one sh:minCount predicate.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent",
            )
        if len(min_count) > 1:
            raise ConstraintLoadError(
                "MinCountConstraintComponent must have at most one sh:minCount predicate.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent",
            )
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "MinCountConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent",
            )
        self.min_count = min_count[0]
        if not (isinstance(self.min_count, Literal) and self.min_count.datatype == XSD_integer):
            raise ConstraintLoadError(
                "MinCountConstraintComponent sh:minCount must be a literal with datatype xsd:integer.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent",
            )
        if int(self.min_count.value) < 0:
            raise ConstraintLoadError(
                "MinCountConstraintComponent sh:minCount must be an integer >= 0.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent",
            )

    @classmethod
    def constraint_parameters(cls):
        return [SH_minCount]

    @classmethod
    def constraint_name(cls):
        return "MinCountConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        p = self.shape.path()
        if p:
            p = stringify_node(self.shape.sg.graph, p)
            m = "Less than {} values on {}->{}".format(
                str(self.min_count.value), stringify_node(datagraph, focus_node), p
            )
        else:
            m = "Less than {} values on {}".format(str(self.min_count.value), stringify_node(datagraph, focus_node))
        return [Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        min_count = int(self.min_count.value)
        if min_count == 0:
            # MinCount of zero always passes
            return True, []
        reports = []
        non_conformant = False

        for f, value_nodes in focus_value_nodes.items():
            if not len(value_nodes) >= min_count:
                non_conformant = True
                rept = self.make_v_result(target_graph, f)
                reports.append(rept)
        return (not non_conformant), reports


class MaxCountConstraintComponent(ConstraintComponent):
    """
    sh:maxCount specifies the maximum number of value nodes that satisfy the condition.
    Link: https://www.w3.org/TR/shacl/#MaxCountConstraintComponent
    Textual Definition:
    If the number of value nodes is greater than $maxCount, there is a validation result.
    """

    shacl_constraint_component = SH_MaxCountConstraintComponent

    def __init__(self, shape):
        super(MaxCountConstraintComponent, self).__init__(shape)
        max_count = list(self.shape.objects(SH_maxCount))
        if len(max_count) < 1:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent must have at least one sh:maxCount predicate.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent",
            )
        if len(max_count) > 1:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent must have at most one sh:maxCount predicate.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent",
            )
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent",
            )
        self.max_count = max_count[0]
        if not (isinstance(self.max_count, Literal) and self.max_count.datatype == XSD_integer):
            raise ConstraintLoadError(
                "MaxCountConstraintComponent sh:maxCount must be a literal with datatype xsd:integer.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent",
            )
        if int(self.max_count.value) < 0:
            raise ConstraintLoadError(
                "MaxCountConstraintComponent sh:maxCount must be an integer >= 0.",
                "https://www.w3.org/TR/shacl/#MaxCountConstraintComponent",
            )

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxCount]

    @classmethod
    def constraint_name(cls):
        return "MaxCountConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        p = self.shape.path()
        if p:
            p = stringify_node(self.shape.sg.graph, p)
            m = "More than {} values on {}->{}".format(
                str(self.max_count.value), stringify_node(datagraph, focus_node), p
            )
        else:
            m = "More than {} values on {}".format(str(self.max_count.value), stringify_node(datagraph, focus_node))
        return [Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        max_count = int(self.max_count.value)
        reports = []
        non_conformant = False

        for f, value_nodes in focus_value_nodes.items():
            if not len(value_nodes) <= max_count:
                non_conformant = True
                rept = self.make_v_result(target_graph, f)
                reports.append(rept)
        return (not non_conformant), reports
