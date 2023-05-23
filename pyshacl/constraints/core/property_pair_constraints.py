# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-property-pairs
"""
from typing import Dict, List

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node

SH_equals = SH.equals
SH_disjoint = SH.disjoint
SH_lessThan = SH.lessThan
SH_lessThanOrEquals = SH.lessThanOrEquals

SH_EqualsConstraintComponent = SH.EqualsConstraintComponent
SH_DisjointConstraintComponent = SH.DisjointConstraintComponent
SH_LessThanConstraintComponent = SH.LessThanConstraintComponent
SH_LessThanOrEqualsConstraintComponent = SH.LessThanOrEqualsConstraintComponent


class EqualsConstraintComponent(ConstraintComponent):
    """
    sh:equals specifies the condition that the set of all value nodes is equal to the set of objects of the triples that have the focus node as subject and the value of sh:equals as predicate.
    Link:
    https://www.w3.org/TR/shacl/#EqualsConstraintComponent
    Textual Definition:
    For each value node that does not exist as a value of the property $equals at the focus node, there is a validation result with the value node as sh:value. For each value of the property $equals at the focus node that is not one of the value nodes, there is a validation result with the value as sh:value.
    """

    shacl_constraint_component = SH_EqualsConstraintComponent

    def __init__(self, shape):
        super(EqualsConstraintComponent, self).__init__(shape)
        property_compare_set = set(self.shape.objects(SH_equals))
        if len(property_compare_set) < 1:
            raise ConstraintLoadError(
                "EqualsConstraintComponent must have at least one sh:equals predicate.",
                "https://www.w3.org/TR/shacl/#EqualsConstraintComponent",
            )
        self.property_compare_set = property_compare_set

    @classmethod
    def constraint_parameters(cls):
        return [SH_equals]

    @classmethod
    def constraint_name(cls):
        return "EqualsConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.property_compare_set) < 2:
            m = "Value of {}->{} != {}".format(
                stringify_node(datagraph, focus_node),
                stringify_node(self.shape.sg.graph, next(iter(self.property_compare_set))),
                stringify_node(datagraph, value_node),
            )
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, p) for p in self.property_compare_set)
            m = "Value of {}->{} != {}".format(
                stringify_node(datagraph, focus_node), rules, stringify_node(datagraph, value_node)
            )
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for eq in iter(self.property_compare_set):
            _nc, _r = self._evaluate_property_equals(eq, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_property_equals(self, eq, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            value_node_set = set(value_nodes)
            compare_values = set(target_graph.objects(f, eq))
            value_nodes_missing = value_node_set.difference(compare_values)
            compare_values_missing = compare_values.difference(value_node_set)
            if len(value_nodes_missing) > 0 or len(compare_values_missing) > 0:
                non_conformant = True
            else:
                continue
            for value_node in value_nodes_missing:
                rept = self.make_v_result(target_graph, f, value_node=value_node)
                reports.append(rept)
            for compare_value in compare_values_missing:
                rept = self.make_v_result(target_graph, f, value_node=compare_value)
                reports.append(rept)
        return non_conformant, reports


class DisjointConstraintComponent(ConstraintComponent):
    """
    sh:disjoint specifies the condition that the set of value nodes is disjoint with the set of objects of the triples that have the focus node as subject and the value of sh:disjoint as predicate.
    Link:
    https://www.w3.org/TR/shacl/#DisjointConstraintComponent
    Textual Definition:
    For each value node that also exists as a value of the property $disjoint at the focus node, there is a validation result with the value node as sh:value.
    """

    shacl_constraint_component = SH_DisjointConstraintComponent

    def __init__(self, shape):
        super(DisjointConstraintComponent, self).__init__(shape)
        property_compare_set = set(self.shape.objects(SH_disjoint))
        if len(property_compare_set) < 1:
            raise ConstraintLoadError(
                "DisjointConstraintComponent must have at least one sh:disjoint predicate.",
                "https://www.w3.org/TR/shacl/#DisjointConstraintComponent",
            )
        self.property_compare_set = property_compare_set

    @classmethod
    def constraint_parameters(cls):
        return [SH_disjoint]

    @classmethod
    def constraint_name(cls):
        return "DisjointConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.property_compare_set) < 2:
            m = "Value of {}->{} == {}".format(
                stringify_node(datagraph, focus_node),
                stringify_node(self.shape.sg.graph, next(iter(self.property_compare_set))),
                stringify_node(datagraph, value_node),
            )
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, p) for p in self.property_compare_set)
            m = "Value of {}->{} == {}".format(
                stringify_node(datagraph, focus_node), rules, stringify_node(datagraph, value_node)
            )
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for dj in iter(self.property_compare_set):
            _nc, _r = self._evaluate_property_disjoint(dj, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_property_disjoint(self, dj, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            value_node_set = set(value_nodes)
            compare_values = set(target_graph.objects(f, dj))
            common_nodes = value_node_set.intersection(compare_values)
            if len(common_nodes) > 0:
                non_conformant = True
            else:
                continue
            for common_node in common_nodes:
                rept = self.make_v_result(target_graph, f, value_node=common_node)
                reports.append(rept)

        return non_conformant, reports


class LessThanConstraintComponent(ConstraintComponent):
    """
    sh:lessThan specifies the condition that each value node is smaller than all the objects of the triples that have the focus node as subject and the value of sh:lessThan as predicate.
    Link:
    https://www.w3.org/TR/shacl/#LessThanConstraintComponent
    Textual Definition:
    For each pair of value nodes and the values of the property $lessThan at the given focus node where the first value is not less than the second value (based on SPARQL's < operator) or where the two values cannot be compared, there is a validation result with the value node as sh:value.
    """

    shacl_constraint_component = SH_LessThanConstraintComponent

    def __init__(self, shape):
        super(LessThanConstraintComponent, self).__init__(shape)
        property_compare_set = set(self.shape.objects(SH_lessThan))
        if len(property_compare_set) < 1:
            raise ConstraintLoadError(
                "LessThanConstraintComponent must have at least one sh:lessThan predicate.",
                "https://www.w3.org/TR/shacl/#LessThanConstraintComponent",
            )
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "LessThanConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#LessThanConstraintComponent",
            )
        self.property_compare_set = property_compare_set

    @classmethod
    def constraint_parameters(cls):
        return [SH_lessThan]

    @classmethod
    def constraint_name(cls):
        return "LessThanConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.property_compare_set) < 2:
            m = "Value of {}->{} <= {}".format(
                stringify_node(datagraph, focus_node),
                stringify_node(self.shape.sg.graph, next(iter(self.property_compare_set))),
                stringify_node(datagraph, value_node),
            )
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, p) for p in self.property_compare_set)
            m = "Value of {}->{} <= {}".format(
                stringify_node(datagraph, focus_node), rules, stringify_node(datagraph, value_node)
            )
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for lt in iter(self.property_compare_set):
            if isinstance(lt, rdflib.Literal) or isinstance(lt, rdflib.BNode):
                raise ReportableRuntimeError("Value of sh:lessThan MUST be a URI Identifier.")
            _nc, _r = self._evaluate_less_than(lt, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_less_than(self, lt, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            value_node_set = set(value_nodes)
            compare_values = set(target_graph.objects(f, lt))

            for value_node in iter(value_node_set):
                if isinstance(value_node, rdflib.BNode):
                    raise ReportableRuntimeError("Cannot use sh:lessThan to compare a BlankNode.")
                value_is_string = False
                orig_value_node = value_node
                if isinstance(value_node, rdflib.URIRef):
                    value_node = str(value_node)
                    value_is_string = True
                elif isinstance(value_node, rdflib.Literal) and isinstance(value_node.value, str):
                    value_node = value_node.value
                    value_is_string = True

                for compare_value in compare_values:
                    if isinstance(compare_value, rdflib.BNode):
                        raise ReportableRuntimeError("Cannot use sh:lessThan to compare a BlankNode.")
                    compare_is_string = False
                    if isinstance(compare_value, rdflib.URIRef):
                        compare_value = str(compare_value)
                        compare_is_string = True
                    elif isinstance(compare_value, rdflib.Literal) and isinstance(compare_value.value, str):
                        compare_value = compare_value.value
                        compare_is_string = True
                    if (value_is_string and not compare_is_string) or (compare_is_string and not value_is_string):
                        non_conformant = True
                    elif not value_node < compare_value:
                        non_conformant = True
                    else:
                        continue
                    rept = self.make_v_result(target_graph, f, value_node=orig_value_node)
                    reports.append(rept)
        return non_conformant, reports


class LessThanOrEqualsConstraintComponent(ConstraintComponent):
    """
    sh:lessThanOrEquals specifies the condition that each value node is smaller than or equal to all the objects of the triples that have the focus node as subject and the value of sh:lessThanOrEquals as predicate.
    Link:
    https://www.w3.org/TR/shacl/#LessThanOrEqualsConstraintComponent
    Textual Definition:
    For each pair of value nodes and the values of the property $lessThanOrEquals at the given focus node where the first value is not less than or equal to the second value (based on SPARQL's <= operator) or where the two values cannot be compared, there is a validation result with the value node as sh:value.
    """

    shacl_constraint_component = SH_LessThanOrEqualsConstraintComponent

    def __init__(self, shape):
        super(LessThanOrEqualsConstraintComponent, self).__init__(shape)
        property_compare_set = set(self.shape.objects(SH_lessThanOrEquals))
        if len(property_compare_set) < 1:
            raise ConstraintLoadError(
                "LessThanOrEqualsConstraintComponent must have at least one sh:lessThanOrEquals predicate.",
                "https://www.w3.org/TR/shacl/#LessThanOrEqualsConstraintComponent",
            )
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "LessThanOrEqualsConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#LessThanOrEqualsConstraintComponent",
            )
        self.property_compare_set = property_compare_set

    @classmethod
    def constraint_parameters(cls):
        return [SH_lessThanOrEquals]

    @classmethod
    def constraint_name(cls):
        return "LessThanOrEqualsConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.property_compare_set) < 2:
            m = "Value of {}->{} < {}".format(
                stringify_node(datagraph, focus_node),
                stringify_node(self.shape.sg.graph, next(iter(self.property_compare_set))),
                stringify_node(datagraph, value_node),
            )
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, p) for p in self.property_compare_set)
            m = "Value of {}->{} < {}".format(
                stringify_node(datagraph, focus_node), rules, stringify_node(datagraph, value_node)
            )
        return [rdflib.Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for lt in iter(self.property_compare_set):
            if isinstance(lt, rdflib.Literal) or isinstance(lt, rdflib.BNode):
                raise ReportableRuntimeError("Value of sh:lessThanOrEquals MUST be a URI Identifier.")
            _nc, _r = self._evaluate_ltoe(lt, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_ltoe(self, lt, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            value_node_set = set(value_nodes)
            compare_values = set(target_graph.objects(f, lt))

            for value_node in iter(value_node_set):
                if isinstance(value_node, rdflib.BNode):
                    raise ReportableRuntimeError("Cannot use sh:lessThanOrEquals to compare a BlankNode.")
                value_is_string = False
                orig_value_node = value_node
                if isinstance(value_node, rdflib.URIRef):
                    value_node = str(value_node)
                    value_is_string = True
                elif isinstance(value_node, rdflib.Literal) and isinstance(value_node.value, str):
                    value_node = value_node.value
                    value_is_string = True

                for compare_value in compare_values:
                    if isinstance(compare_value, rdflib.BNode):
                        raise ReportableRuntimeError("Cannot use sh:lessThanOrEquals to compare a BlankNode.")
                    compare_is_string = False
                    if isinstance(compare_value, rdflib.URIRef):
                        compare_value = str(compare_value)
                        compare_is_string = True
                    elif isinstance(compare_value, rdflib.Literal) and isinstance(compare_value.value, str):
                        compare_value = compare_value.value
                        compare_is_string = True
                    if (value_is_string and not compare_is_string) or (compare_is_string and not value_is_string):
                        non_conformant = True
                    elif not value_node <= compare_value:
                        non_conformant = True
                    else:
                        continue
                    rept = self.make_v_result(target_graph, f, value_node=orig_value_node)
                    reports.append(rept)
        return non_conformant, reports
