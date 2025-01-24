# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-property-pairs
"""

from typing import Dict, List

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError
from pyshacl.helper.path_helper import shacl_path_to_sparql_path
from pyshacl.pytypes import GraphLike, SHACLExecutor
from pyshacl.rdfutil import stringify_node
from pyshacl.shape import Shape

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

    def __init__(self, shape: Shape) -> None:
        super(EqualsConstraintComponent, self).__init__(shape)
        property_compare_set = set(self.shape.objects(SH_equals))
        if len(property_compare_set) < 1:
            raise ConstraintLoadError(
                "EqualsConstraintComponent must have at least one sh:equals predicate.",
                "https://www.w3.org/TR/shacl/#EqualsConstraintComponent",
            )
        self.property_compare_set = property_compare_set

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_equals]

    @classmethod
    def constraint_name(cls) -> str:
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

    def evaluate(
        self, executor: SHACLExecutor, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List
    ):
        """
        :type executor: SHACLExecutor
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for eq in iter(self.property_compare_set):
            if executor.sparql_mode:
                _nc, _r = self._evaluate_property_equals_sparql(eq, target_graph, focus_value_nodes)
            else:
                _nc, _r = self._evaluate_property_equals_rdflib(eq, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_property_equals_sparql(self, eq, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        prefixes = dict(target_graph.namespaces())
        eq_path = shacl_path_to_sparql_path(self.shape.sg, eq, prefixes=prefixes)
        eq_lookup_query = f"SELECT DISTINCT {' '.join(f'?v{i}' for i, _ in enumerate(f_v_dict))} WHERE {{\n"
        init_bindings = {}
        f_eq_results = {}
        for i, f in enumerate(f_v_dict.keys()):
            eq_lookup_query += f"OPTIONAL {{ $f{i} {eq_path} ?v{i} . }}\n"
            init_bindings[f"f{i}"] = f
            f_eq_results[f] = set()
        eq_lookup_query += "}"
        try:
            results = target_graph.query(eq_lookup_query, initBindings=init_bindings)
        except Exception as e:
            print(e)
            raise
        if len(results) > 0:
            for r in results:
                for i, f in enumerate(f_v_dict.keys()):
                    val_i = r[i]
                    if val_i is None or val_i == "UNDEF":
                        continue
                    f_eq_results[f].add(val_i)
        for i, f in enumerate(f_v_dict.keys()):
            value_node_set = set(f_v_dict[f])
            compare_values = f_eq_results[f]
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

    def _evaluate_property_equals_rdflib(self, eq, target_graph, f_v_dict):
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

    def __init__(self, shape: Shape) -> None:
        super(DisjointConstraintComponent, self).__init__(shape)
        property_compare_set = set(self.shape.objects(SH_disjoint))
        if len(property_compare_set) < 1:
            raise ConstraintLoadError(
                "DisjointConstraintComponent must have at least one sh:disjoint predicate.",
                "https://www.w3.org/TR/shacl/#DisjointConstraintComponent",
            )
        self.property_compare_set = property_compare_set

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_disjoint]

    @classmethod
    def constraint_name(cls) -> str:
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

    def evaluate(
        self, executor: SHACLExecutor, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List
    ):
        """
        :type executor: SHACLExecutor
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for dj in iter(self.property_compare_set):
            if executor.sparql_mode:
                _nc, _r = self._evaluate_property_disjoint_sparql(dj, target_graph, focus_value_nodes)
            else:
                _nc, _r = self._evaluate_property_disjoint_rdflib(dj, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_property_disjoint_sparql(self, dj, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        prefixes = dict(target_graph.namespaces())
        dj_path = shacl_path_to_sparql_path(self.shape.sg, dj, prefixes=prefixes)
        dj_lookup_query = f"SELECT DISTINCT {' '.join(f'?v{i}' for i, _ in enumerate(f_v_dict))} WHERE {{\n"
        init_bindings = {}
        f_dj_results = {}
        for i, f in enumerate(f_v_dict.keys()):
            dj_lookup_query += f"OPTIONAL {{ $f{i} {dj_path} ?v{i} . }}\n"
            init_bindings[f"f{i}"] = f
            f_dj_results[f] = set()
        dj_lookup_query += "}"
        try:
            results = target_graph.query(dj_lookup_query, initBindings=init_bindings)
        except Exception as e:
            print(e)
            raise
        if len(results) > 0:
            for r in results:
                for i, f in enumerate(f_v_dict.keys()):
                    val_i = r[i]
                    if val_i is None or val_i == "UNDEF":
                        continue
                    f_dj_results[f].add(val_i)
        for i, f in enumerate(f_v_dict.keys()):
            value_node_set = set(f_v_dict[f])
            compare_values = f_dj_results[f]
            common_nodes = value_node_set.intersection(compare_values)
            if len(common_nodes) > 0:
                non_conformant = True
            else:
                continue
            for common_node in common_nodes:
                rept = self.make_v_result(target_graph, f, value_node=common_node)
                reports.append(rept)
        return non_conformant, reports

    def _evaluate_property_disjoint_rdflib(self, dj, target_graph, f_v_dict):
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

    def __init__(self, shape: Shape) -> None:
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
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_lessThan]

    @classmethod
    def constraint_name(cls) -> str:
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

    def evaluate(
        self, executor: SHACLExecutor, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List
    ):
        """
        :type executor: SHACLExecutor
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for lt in iter(self.property_compare_set):
            if isinstance(lt, rdflib.Literal) or isinstance(lt, rdflib.BNode):
                raise ReportableRuntimeError("Value of sh:lessThan MUST be a URI Identifier.")
            if executor.sparql_mode:
                _nc, _r = self._evaluate_less_than_sparql(lt, target_graph, focus_value_nodes)
            else:
                _nc, _r = self._evaluate_less_than_rdflib(lt, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _compare_lt(self, value_node_set, compare_values, datagraph, f):
        non_conformant = False
        reports = []
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
                rept = self.make_v_result(datagraph, f, value_node=orig_value_node)
                reports.append(rept)
        return non_conformant, reports

    def _evaluate_less_than_sparql(self, lt, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        prefixes = dict(target_graph.namespaces())
        lt_path = shacl_path_to_sparql_path(self.shape.sg, lt, prefixes=prefixes)
        lt_lookup_query = f"SELECT DISTINCT {' '.join(f'?v{i}' for i, _ in enumerate(f_v_dict))} WHERE {{\n"
        init_bindings = {}
        f_lt_results = {}
        for i, f in enumerate(f_v_dict.keys()):
            lt_lookup_query += f"OPTIONAL {{ $f{i} {lt_path} ?v{i} . }}\n"
            init_bindings[f"f{i}"] = f
            f_lt_results[f] = set()
        lt_lookup_query += "}"
        try:
            results = target_graph.query(lt_lookup_query, initBindings=init_bindings)
        except Exception as e:
            print(e)
            raise
        if len(results) > 0:
            for r in results:
                for i, f in enumerate(f_v_dict.keys()):
                    val_i = r[i]
                    if val_i is None or val_i == "UNDEF":
                        continue
                    f_lt_results[f].add(val_i)
        for i, f in enumerate(f_v_dict.keys()):
            value_node_set = set(f_v_dict[f])
            compare_values = f_lt_results[f]
            _nc, _r = self._compare_lt(value_node_set, compare_values, target_graph, f)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return non_conformant, reports

    def _evaluate_less_than_rdflib(self, lt, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            value_node_set = set(value_nodes)
            compare_values = set(target_graph.objects(f, lt))
            _nc, _r = self._compare_lt(value_node_set, compare_values, target_graph, f)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
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

    def __init__(self, shape: Shape) -> None:
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
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_lessThanOrEquals]

    @classmethod
    def constraint_name(cls) -> str:
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

    def evaluate(
        self, executor: SHACLExecutor, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List
    ):
        """
        :type executor: SHACLExecutor
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False

        for lt in iter(self.property_compare_set):
            if isinstance(lt, rdflib.Literal) or isinstance(lt, rdflib.BNode):
                raise ReportableRuntimeError("Value of sh:lessThanOrEquals MUST be a URI Identifier.")
            if executor.sparql_mode:
                _nc, _r = self._evaluate_ltoe_sparql(lt, target_graph, focus_value_nodes)
            else:
                _nc, _r = self._evaluate_ltoe_rdflib(lt, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _compare_ltoe(self, value_node_set, compare_values, datagraph, f):
        non_conformant = False
        reports = []
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
                rept = self.make_v_result(datagraph, f, value_node=orig_value_node)
                reports.append(rept)
        return non_conformant, reports

    def _evaluate_ltoe_sparql(self, ltoe, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        prefixes = dict(target_graph.namespaces())
        ltoe_path = shacl_path_to_sparql_path(self.shape.sg, ltoe, prefixes=prefixes)
        ltoe_lookup_query = f"SELECT DISTINCT {' '.join(f'?v{i}' for i, _ in enumerate(f_v_dict))} WHERE {{\n"
        init_bindings = {}
        f_ltoe_results = {}
        for i, f in enumerate(f_v_dict.keys()):
            ltoe_lookup_query += f"OPTIONAL {{ $f{i} {ltoe_path} ?v{i} . }}\n"
            init_bindings[f"f{i}"] = f
            f_ltoe_results[f] = set()
        ltoe_lookup_query += "}"
        try:
            results = target_graph.query(ltoe_lookup_query, initBindings=init_bindings)
        except Exception as e:
            print(e)
            raise
        if len(results) > 0:
            for r in results:
                for i, f in enumerate(f_v_dict.keys()):
                    val_i = r[i]
                    if val_i is None or val_i == "UNDEF":
                        continue
                    f_ltoe_results[f].add(val_i)
        for i, f in enumerate(f_v_dict.keys()):
            value_node_set = set(f_v_dict[f])
            compare_values = f_ltoe_results[f]
            _nc, _r = self._compare_ltoe(value_node_set, compare_values, target_graph, f)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return non_conformant, reports

    def _evaluate_ltoe_rdflib(self, ltoe, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            value_node_set = set(value_nodes)
            compare_values = set(target_graph.objects(f, ltoe))
            _nc, _r = self._compare_ltoe(value_node_set, compare_values, target_graph, f)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return non_conformant, reports
