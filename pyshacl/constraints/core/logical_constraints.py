# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-logical
"""

from typing import Dict, List
from warnings import warn

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError, ShapeRecursionWarning, ValidationFailure
from pyshacl.pytypes import GraphLike, SHACLExecutor
from pyshacl.rdfutil import stringify_node
from pyshacl.shape import Shape

SH_not = SH["not"]
SH_and = SH["and"]
SH_or = SH["or"]
SH_xone = SH.xone

SH_NotConstraintComponent = SH.NotConstraintComponent
SH_AndConstraintComponent = SH.AndConstraintComponent
SH_OrConstraintComponent = SH.OrConstraintComponent
SH_XoneConstraintComponent = SH.XoneConstraintComponent


class NotConstraintComponent(ConstraintComponent):
    """
    sh:not specifies the condition that each value node cannot conform to a given shape. This is comparable to negation and the logical "not" operator.
    Link:
    https://www.w3.org/TR/shacl/#NotConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be reported if the conformance checking of v against the shape $not produces a failure. Otherwise, if v conforms to the shape $not, there is validation result with v as sh:value.
    """

    shacl_constraint_component = SH_NotConstraintComponent
    shape_expecting = True
    list_taking = False

    def __init__(self, shape: Shape) -> None:
        super(NotConstraintComponent, self).__init__(shape)
        not_list = list(self.shape.objects(SH_not))
        if len(not_list) < 1:
            raise ConstraintLoadError(
                "NotConstraintComponent must have at least one sh:not predicate.",
                "https://www.w3.org/TR/shacl/#NotConstraintComponent",
            )
        self.not_list = not_list

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_not]

    @classmethod
    def constraint_name(cls) -> str:
        return "NotConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        try:
            value_node_str = stringify_node(datagraph, value_node)
        except (LookupError, ValueError):
            # value node doesn't exist in the datagraph.
            value_node_str = str(value_node)
        if len(self.not_list) == 1:
            m = f"Node {value_node_str} must not conform to shape {stringify_node(self.shape.sg.graph, self.not_list[0])}"
        else:
            nots_list = " , ".join(stringify_node(self.shape.sg.graph, n) for n in self.not_list)
            m = f"Node {value_node_str} must not conform to any shapes in {nots_list}"
        return [rdflib.Literal(m)]

    def evaluate(self, executor: SHACLExecutor, datagraph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type executor: SHACLExecutor
        :type datagraph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False
        potentially_recursive = self.recursion_triggers(_evaluation_path)

        for not_c in self.not_list:
            _nc, _r = self._evaluate_not_constraint(
                executor, not_c, datagraph, focus_value_nodes, potentially_recursive, _evaluation_path
            )
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_not_constraint(
        self, executor, not_c, datagraph, focus_value_nodes, potentially_recursive, _evaluation_path
    ):
        """
        :type not_c: List[Node]
        :type datagraph: rdflib.Graph
        :type focus_value_nodes: dict
        :type potentially_recursive: Optional[List]
        :type _evaluation_path: List
        """
        _reports = []
        _non_conformant = False
        not_shape = self.shape.get_other_shape(not_c)
        if not not_shape:
            raise ReportableRuntimeError(
                "Shape pointed to by sh:not does not exist or is not a well-formed SHACL Shape."
            )
        if potentially_recursive and not_shape in potentially_recursive:
            warn(ShapeRecursionWarning(_evaluation_path))
            return _non_conformant, _reports
        upstream_reports = []
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                try:
                    _is_conform, _r = not_shape.validate(
                        executor, datagraph, focus=v, _evaluation_path=_evaluation_path[:]
                    )
                except ValidationFailure as e:
                    raise e
                if len(_r):
                    upstream_reports.extend(_r)
                if _is_conform:
                    # in this case, we _dont_ want to conform!
                    _non_conformant = True
                    rept = self.make_v_result(datagraph, f, value_node=v)
                    _reports.append(rept)
        if len(upstream_reports) and self.shape.sg.debug:
            self.shape.logger.debug(
                "sh:not constraint reports ignored, conformance inverted and passed to the parent Node:"
            )
            for v_str, v_node, v_parts in upstream_reports:
                self.shape.logger.debug(v_str)
        return _non_conformant, _reports


class AndConstraintComponent(ConstraintComponent):
    """
    sh:and specifies the condition that each value node conforms to all provided shapes. This is comparable to conjunction and the logical "and" operator.
    Link:
    https://www.w3.org/TR/shacl/#AndConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against any of the members of $and produces a failure. Otherwise, if v does not conform to each member of $and, there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_AndConstraintComponent
    shape_expecting = True
    list_taking = True

    def __init__(self, shape: Shape) -> None:
        super(AndConstraintComponent, self).__init__(shape)
        and_list = list(self.shape.objects(SH_and))
        if len(and_list) < 1:
            raise ConstraintLoadError(
                "AndConstraintComponent must have at least one sh:and predicate.",
                "https://www.w3.org/TR/shacl/#AndConstraintComponent",
            )
        self.and_list = and_list

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_and]

    @classmethod
    def constraint_name(cls) -> str:
        return "AndConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.and_list) < 2:
            and_node_string = " , ".join(
                stringify_node(self.shape.sg.graph, a_c) for a_c in self.shape.sg.graph.items(self.and_list[0])
            )
        else:
            and_node_strings = []
            for a in self.and_list:
                and_node_string1 = " , ".join(
                    stringify_node(self.shape.sg.graph, a_c) for a_c in self.shape.sg.graph.items(a)
                )
                and_node_strings.append(f"({and_node_string1})")
            and_node_string = " and ".join(and_node_strings)
        try:
            value_node_str = stringify_node(datagraph, value_node)
        except (LookupError, ValueError):
            # value node doesn't exist in the datagraph.
            value_node_str = str(value_node)
        m = f"Node {value_node_str} must conform to all shapes in {and_node_string}"
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

        for and_c in self.and_list:
            _nc, _r = self._evaluate_and_constraint(executor, and_c, target_graph, focus_value_nodes, _evaluation_path)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_and_constraint(self, executor, and_c, target_graph, focus_value_nodes, _evaluation_path):
        _reports = []
        _non_conformant = False
        sg = self.shape.sg.graph
        and_list = set(sg.items(and_c))
        if len(and_list) < 1:
            raise ReportableRuntimeError("The list associated with sh:and is not a valid RDF list.")
        and_shapes = set()
        for a in and_list:
            and_shape = self.shape.get_other_shape(a)
            if not and_shape:
                raise ReportableRuntimeError(
                    "Shape pointed to by sh:and does not exist or is not a well-formed SHACL Shape."
                )
            and_shapes.add(and_shape)
        upstream_reports = []
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                passed_all = True
                for and_shape in and_shapes:
                    try:
                        _is_conform, _r = and_shape.validate(
                            executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                        )
                    except ValidationFailure as e:
                        raise e
                    if len(_r):
                        upstream_reports.extend(_r)
                    passed_all = passed_all and _is_conform
                if not passed_all:
                    _non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    _reports.append(rept)
        if len(upstream_reports) and self.shape.sg.debug:
            self.shape.logger.debug("sh:and constraint reports will be inspected and not passed to the parent Node:")
            for v_str, v_node, v_parts in upstream_reports:
                self.shape.logger.debug(v_str)
        return _non_conformant, _reports


class OrConstraintComponent(ConstraintComponent):
    """
    sh:or specifies the condition that each value node conforms to at least one of the provided shapes. This is comparable to disjunction and the logical "or" operator.
    Link:
    https://www.w3.org/TR/shacl/#OrConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against any of the members produces a failure. Otherwise, if v conforms to none of the members of $or there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_OrConstraintComponent
    shape_expecting = True
    list_taking = True

    def __init__(self, shape: Shape) -> None:
        super(OrConstraintComponent, self).__init__(shape)
        or_list = list(self.shape.objects(SH_or))
        if len(or_list) < 1:
            raise ConstraintLoadError(
                "OrConstraintComponent must have at least one sh:or predicate.",
                "https://www.w3.org/TR/shacl/#OrConstraintComponent",
            )
        self.or_list = or_list

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_or]

    @classmethod
    def constraint_name(cls) -> str:
        return "OrConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.or_list) < 2:
            or_node_string = " , ".join(
                stringify_node(self.shape.sg.graph, o_c) for o_c in self.shape.sg.graph.items(self.or_list[0])
            )
        else:
            or_node_strings = []
            for a in self.or_list:
                or_node_string1 = " , ".join(
                    stringify_node(self.shape.sg.graph, a_c) for a_c in self.shape.sg.graph.items(a)
                )
                or_node_strings.append(f"({or_node_string1})")
            or_node_string = " and ".join(or_node_strings)
        try:
            value_node_str = stringify_node(datagraph, value_node)
        except (LookupError, ValueError):
            # value node doesn't exist in the datagraph.
            value_node_str = str(value_node)
        m = f"Node {value_node_str} must conform to one or more shapes in {or_node_string}"
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

        for or_c in self.or_list:
            _nc, _r = self._evaluate_or_constraint(executor, or_c, target_graph, focus_value_nodes, _evaluation_path)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_or_constraint(self, executor, or_c, target_graph, focus_value_nodes, _evaluation_path):
        _reports = []
        _non_conformant = False
        shape_graph = self.shape.sg.graph
        or_list = set(shape_graph.items(or_c))
        if len(or_list) < 1:
            raise ReportableRuntimeError("The list associated with sh:or is not a valid RDF list.")
        or_shapes = set()
        for o in or_list:
            or_shape = self.shape.get_other_shape(o)
            if not or_shape:
                raise ReportableRuntimeError(
                    "Shape pointed to by sh:or does not exist or is not a well-formed SHACL Shape."
                )
            or_shapes.add(or_shape)
        upstream_reports = []
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                passed_any = False
                for or_shape in or_shapes:
                    try:
                        _is_conform, _r = or_shape.validate(
                            executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                        )
                    except ValidationFailure as e:
                        raise e
                    if len(_r):
                        upstream_reports.extend(_r)
                    passed_any = passed_any or _is_conform
                if not passed_any:
                    _non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    _reports.append(rept)
        if len(upstream_reports) and self.shape.sg.debug:
            self.shape.logger.debug("sh:or constraint reports will be inspected and not passed to the parent Node:")
            for v_str, v_node, v_parts in upstream_reports:
                self.shape.logger.debug(v_str)
        return _non_conformant, _reports


class XoneConstraintComponent(ConstraintComponent):
    """
    sh:or specifies the condition that each value node conforms to at least one of the provided shapes. This is comparable to disjunction and the logical "or" operator.
    Link:
    https://www.w3.org/TR/shacl/#XoneConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against any of the members produces a failure. Otherwise, if v conforms to none of the members of $or there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_XoneConstraintComponent
    shape_expecting = True
    list_taking = True

    def __init__(self, shape: Shape) -> None:
        super(XoneConstraintComponent, self).__init__(shape)
        xone_nodes = list(self.shape.objects(SH_xone))
        if len(xone_nodes) < 1:
            raise ConstraintLoadError(
                "XoneConstraintComponent must have at least one sh:xone predicate.",
                "https://www.w3.org/TR/shacl/#XoneConstraintComponent",
            )
        self.xone_nodes = xone_nodes

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_xone]

    @classmethod
    def constraint_name(cls) -> str:
        return "XoneConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.xone_nodes) < 2:
            xone_node_string = " , ".join(
                stringify_node(self.shape.sg.graph, a_c) for a_c in self.shape.sg.graph.items(self.xone_nodes[0])
            )
        else:
            xone_node_strings = []
            for a in self.xone_nodes:
                xone_node_string1 = " , ".join(
                    stringify_node(self.shape.sg.graph, a_c) for a_c in self.shape.sg.graph.items(a)
                )
                xone_node_strings.append(f"({xone_node_string1})")
            xone_node_string = " and ".join(xone_node_strings)
        try:
            value_node_str = stringify_node(datagraph, value_node)
        except (LookupError, ValueError):
            # value node doesn't exist in the datagraph.
            value_node_str = str(value_node)
        m = f"Node {value_node_str} must conform to exactly one shape in {xone_node_string}"
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

        for xone_c in self.xone_nodes:
            _nc, _r = self._evaluate_xone_constraint(
                executor, xone_c, target_graph, focus_value_nodes, _evaluation_path
            )
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_xone_constraint(self, executor, xone_c, target_graph, focus_value_nodes, _evaluation_path):
        _reports = []
        _non_conformant = False
        shapes_graph = self.shape.sg.graph
        xone_list = list(shapes_graph.items(xone_c))
        if len(xone_list) < 1:
            raise ReportableRuntimeError("The list associated with sh:xone is not a valid RDF list.")
        xone_shapes = list()
        for x in xone_list:
            xone_shape = self.shape.get_other_shape(x)
            if not xone_shape:
                raise ReportableRuntimeError(
                    "Shape pointed to by sh:xone does not exist or is not a well-formed SHACL Shape."
                )
            xone_shapes.append(xone_shape)
        upstream_reports = []
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                passed_count = 0
                for xone_shape in xone_shapes:
                    try:
                        _is_conform, _r = xone_shape.validate(
                            executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                        )
                    except ValidationFailure as e:
                        raise e
                    if len(_r):
                        upstream_reports.extend(_r)
                    if _is_conform:
                        passed_count += 1
                if not (passed_count == 1):
                    _non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    _reports.append(rept)
        if len(upstream_reports) and self.shape.sg.debug:
            self.shape.logger.debug(
                "sh:xone constraint reports ignored, conformance noted and passed to the parent Node:"
            )
            for v_str, v_node, v_parts in upstream_reports:
                self.shape.logger.debug(v_str)
        return _non_conformant, _reports
