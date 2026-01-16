# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-shape
"""

from textwrap import indent
from typing import Dict, List, Optional
from warnings import warn

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import (
    SH,
    SH_detail,
    SH_node,
    SH_NodeConstraintComponent,
    SH_property,
    SH_PropertyConstraintComponent,
)
from pyshacl.errors import (
    ConstraintLoadError,
    ConstraintLoadWarning,
    ReportableRuntimeError,
    ShapeRecursionWarning,
    ValidationFailure,
)
from pyshacl.pytypes import GraphLike, SHACLExecutor
from pyshacl.rdfutil import stringify_node
from pyshacl.shape import Shape

SH_QualifiedValueCountConstraintComponent = SH.QualifiedValueConstraintComponent
SH_QualifiedMaxCountConstraintComponent = SH.QualifiedMaxCountConstraintComponent
SH_QualifiedMinCountConstraintComponent = SH.QualifiedMinCountConstraintComponent

SH_qualifiedValueShape = SH.qualifiedValueShape
SH_qualifiedValueShapesDisjoint = SH.qualifiedValueShapesDisjoint
SH_qualifiedMinCount = SH.qualifiedMinCount
SH_qualifiedMaxCount = SH.qualifiedMaxCount


class PropertyConstraintComponent(ConstraintComponent):
    """
    sh:property can be used to specify that each value node has a given property shape.
    Link:
    https://www.w3.org/TR/shacl/#PropertyConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the validation of v as focus node against the property shape $property produces a failure. Otherwise, the validation results are the results of validating v as focus node against the property shape $property.
    """

    shacl_constraint_component = SH_PropertyConstraintComponent
    shape_expecting = True
    list_taking = False

    def __init__(self, shape: Shape) -> None:
        super(PropertyConstraintComponent, self).__init__(shape)
        property_shapes = list(self.shape.objects(SH_property))
        if len(property_shapes) < 1:
            raise ConstraintLoadError(
                "PropertyConstraintComponent must have at least one sh:property predicate.",
                "https://www.w3.org/TR/shacl/#PropertyConstraintComponent",
            )
        self.property_shapes = property_shapes

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_property]

    @classmethod
    def constraint_name(cls) -> str:
        return "PropertyConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        raise NotImplementedError("A Property Constraint Component should not be able to generate its own message.")

    def evaluate(
        self, executor: SHACLExecutor, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List
    ):
        """
        Entrypoint for constraint evaluation.
        :type executor: SHACLExecutor
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports: List[Dict] = []
        non_conformant = False

        # Shortcut, when there are no value nodes, don't check for recursion, don't validate and exit early
        value_node_count = 0
        for f, value_nodes in focus_value_nodes.items():
            value_node_count = value_node_count + len(value_nodes)
        if value_node_count < 1:
            return (not non_conformant), reports

        potentially_recursive = self.recursion_triggers(_evaluation_path)

        for p_shape in self.property_shapes:
            if self.shape.sg.is_filtered_out_shape(p_shape):
                continue
            _nc, _r = self._evaluate_property_shape(
                executor, p_shape, target_graph, focus_value_nodes, potentially_recursive, _evaluation_path
            )
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_property_shape(
        self, executor, prop_shape, target_graph, focus_value_nodes, potentially_recursive, _evaluation_path
    ):
        _reports = []
        _non_conformant = False
        found_prop_shape = self.shape.get_other_shape(prop_shape)
        if potentially_recursive and found_prop_shape in potentially_recursive:
            warn(ShapeRecursionWarning(_evaluation_path))
            return _non_conformant, _reports
        if not found_prop_shape:
            raise ReportableRuntimeError(
                f"SHACL PropertyShape not found: The shape referenced by sh:property does not exist. "
                f"Please check if the shape '{prop_shape}' is defined."
            )
        elif not found_prop_shape.is_property_shape:
            raise ReportableRuntimeError(
                f"'{prop_shape}' exists but is not a well-formed SHACL PropertyShape. "
                f"Ensure it has the correct type (sh:PropertyShape) and all required properties."
            )

        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                _is_conform, _r = found_prop_shape.validate(
                    executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                )
                _non_conformant = _non_conformant or (not _is_conform)
                _reports.extend(_r)
        return _non_conformant, _reports


class NodeConstraintComponent(ConstraintComponent):
    """
    sh:node specifies the condition that each value node conforms to the given node shape.
    Link:
    https://www.w3.org/TR/shacl/#NodeShapeComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against $node produces a failure. Otherwise, if v does not conform to $node, there is a validation result with v as sh:value.
    """

    shacl_constraint_component = SH_NodeConstraintComponent
    shape_expecting = True
    list_taking = False

    def __init__(self, shape: Shape) -> None:
        super(NodeConstraintComponent, self).__init__(shape)
        node_shapes = list(self.shape.objects(SH_node))
        if len(node_shapes) < 1:
            raise ConstraintLoadError(
                "NodeConstraintComponent must have at least one sh:node predicate.",
                "https://www.w3.org/TR/shacl/#NodeConstraintComponent",
            )
        self.node_shapes = node_shapes

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_node]

    @classmethod
    def constraint_name(cls) -> str:
        return "NodeConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.node_shapes) < 2:
            m = "Value does not conform to Shape {}.".format(stringify_node(self.shape.sg.graph, self.node_shapes[0]))
        else:
            rules = "', '".join(stringify_node(self.shape.sg.graph, c) for c in self.node_shapes)
            m = "Value must conform to every Shape in ('{}').".format(rules)
        m += " See details for more information."
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
        reports: List[Dict] = []
        non_conformant = False

        # Shortcut, when there are no value nodes, don't check for recursion, don't validate and exit early
        value_node_count = 0
        for f, value_nodes in focus_value_nodes.items():
            value_node_count = value_node_count + len(value_nodes)
        if value_node_count < 1:
            return (not non_conformant), reports

        potentially_recursive = self.recursion_triggers(_evaluation_path)

        for n_shape in self.node_shapes:
            if self.shape.sg.is_filtered_out_shape(n_shape):
                continue
            _nc, _r = self._evaluate_node_shape(
                executor, n_shape, target_graph, focus_value_nodes, potentially_recursive, _evaluation_path
            )
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_node_shape(
        self, executor, node_shape, target_graph, focus_value_nodes, potentially_recursive, _evaluation_path
    ):
        _reports = []
        _non_conformant = False
        found_node_shape = self.shape.get_other_shape(node_shape)
        if potentially_recursive and found_node_shape in potentially_recursive:
            warn(ShapeRecursionWarning(_evaluation_path))
            return _non_conformant, _reports
        if not found_node_shape:
            raise ReportableRuntimeError(
                f"SHACL Shape not found: The shape referenced by sh:node does not exist. "
                f"Please check if the shape '{node_shape}' is defined."
            )
        elif found_node_shape.is_property_shape:
            raise ReportableRuntimeError("Shape pointed to by sh:node is not a well-formed SHACL NodeShape.")
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                _is_conform, _r = found_node_shape.validate(
                    executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                )
                # Create a failure for this constraint component if any failures exist
                if (not _is_conform) or len(_r) > 0:
                    _non_conformant = True
                    rept_text, rept_node, rept_triples = self.make_v_result(target_graph, f, value_node=v)
                    # Nest the others underneath via sh:detail
                    rept_text = f"{rept_text}\tDetails:\n"
                    for text_sub, node_sub, triples_sub in _r:
                        # Add text of validation result in nested details section
                        rept_text += indent(text_sub, "\t\t")
                        # Add a triple connecting the new validation result to the
                        # validation result for the nested node
                        rept_triples.append((rept_node, SH_detail, node_sub))
                        # Extend the triples in the report with the ones from the nested result
                        rept_triples.extend(triples_sub)
                    _reports.append((rept_text, rept_node, rept_triples))
        return _non_conformant, _reports


class QualifiedValueShapeConstraintComponent(ConstraintComponent):
    """
    sh:qualifiedValueShape specifies the condition that a specified number of value nodes conforms to the given shape. Each sh:qualifiedValueShape can have: one value for sh:qualifiedMinCount, one value for sh:qualifiedMaxCount or, one value for each, at the same subject.
    Link:
    https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent
    Textual Definition for qualifiedMinCount:
    Let C be the number of value nodes v where v conforms to $qualifiedValueShape and where v does not conform to any of the sibling shapes for the current shape, i.e. the shape that v is validated against and which has $qualifiedValueShape as its value for sh:qualifiedValueShape. A failure MUST be produced if any of the said conformance checks produces a failure. Otherwise, there is a validation result if C is less than $qualifiedMinCount. The constraint component for sh:qualifiedMinCount is sh:QualifiedMinCountConstraintComponent.
    Textual Definition for qualifiedMaxCount:
    Let C be as defined for sh:qualifiedMinCount above. A failure MUST be produced if any of the said conformance checks produces a failure. Otherwise, there is a validation result if C is greater than $qualifiedMaxCount. The constraint component for sh:qualifiedMaxCount is sh:QualifiedMaxCountConstraintComponent.
    """

    shacl_constraint_component = NotImplemented
    shape_expecting = True
    list_taking = False

    def __init__(self, shape: Shape) -> None:
        super(QualifiedValueShapeConstraintComponent, self).__init__(shape)
        if not shape.is_property_shape:
            # Note, this no longer throws an error, this constraint is simply ignored on NodeShapes.
            raise ConstraintLoadWarning(
                "QualifiedValueShapeConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
            )
        value_shapes = set(self.shape.objects(SH_qualifiedValueShape))
        if len(value_shapes) < 1:
            raise ConstraintLoadError(
                "QualifiedValueShapeConstraintComponent must have at least one sh:qualifiedValueShape predicate.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
            )
        self.value_shapes = value_shapes
        min_count: Optional[int]
        min_counts = set(self.shape.objects(SH_qualifiedMinCount))
        if len(min_counts) < 1:
            min_count = None
        elif len(min_counts) > 1:
            raise ConstraintLoadError(
                "QualifiedMinCountConstraintComponent must have at most one sh:qualifiedMinCount predicate.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
            )
        else:
            min_count_literal = next(iter(min_counts))
            if not isinstance(min_count_literal, rdflib.Literal) or not isinstance(min_count_literal.value, int):
                raise ConstraintLoadError(
                    "QualifiedMinCountConstraintComponent sh:qualifiedMinCount must be a Literal with Int.",
                    "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
                )
            min_count = min_count_literal.value

        max_count: Optional[int]
        max_counts = set(self.shape.objects(SH_qualifiedMaxCount))
        if len(max_counts) < 1:
            max_count = None
        elif len(max_counts) > 1:
            raise ConstraintLoadError(
                "QualifiedMaxCountConstraintComponent must have at most one sh:qualifiedMaxCount predicate.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
            )
        else:
            max_count_literal = next(iter(max_counts))
            if not isinstance(max_count_literal, rdflib.Literal) or not isinstance(max_count_literal.value, int):
                raise ConstraintLoadError(
                    "QualifiedMaxCountConstraintComponent sh:qualifiedMaxCount must be a Literal with Int.",
                    "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
                )
            max_count = max_count_literal.value

        if min_count is None and max_count is None:
            raise ConstraintLoadError(
                "QualifiedValueShapeConstraintComponent must have at lease one sh:qualifiedMinCount or "
                "sh:qualifiedMaxCount",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent",
            )
        is_disjoint = False
        disjoint_nodes = set(self.shape.objects(SH_qualifiedValueShapesDisjoint))
        for d in disjoint_nodes:
            if isinstance(d, rdflib.Literal):
                if isinstance(d.value, bool):
                    is_disjoint = is_disjoint or d.value
        self.min_count = min_count
        self.max_count = max_count
        self.is_disjoint = is_disjoint

    @classmethod
    def constraint_parameters(cls) -> List[rdflib.URIRef]:
        return [SH_qualifiedValueShape, SH_qualifiedMinCount, SH_qualifiedValueShapesDisjoint, SH_qualifiedMaxCount]

    @classmethod
    def constraint_name(cls) -> str:
        return "QualifiedValueShapeConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        # TODO:
        #  Implement default message for QualifiedValueConstraint (seems messy)
        shapes_string = ",".join(stringify_node(self.shape.sg.graph, s) for s in self.value_shapes)
        count_message = ""
        if self.min_count is not None:
            count_message += f" MinCount {self.min_count}"
        if self.max_count is not None:
            count_message += f" MaxCount {self.max_count}"
        if len(self.value_shapes) > 1:
            return [rdflib.Literal(f"Focus node does not conform to shapes{count_message}: ({shapes_string})")]
        return [rdflib.Literal(f"Focus node does not conform to shape{count_message}: {shapes_string}")]

    def evaluate(
        self, executor: SHACLExecutor, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List
    ):
        """
        :type executor: SHACLExecutor
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports: List[Dict] = []
        non_conformant = False

        # Shortcut, when there are no value nodes, don't check for recursion, don't validate and exit early
        value_node_count = 0
        for f, value_nodes in focus_value_nodes.items():
            value_node_count = value_node_count + len(value_nodes)
        if not self.is_disjoint and value_node_count < 1 and (self.min_count is None or self.min_count < 1):
            return (not non_conformant), reports

        potentially_recursive = self.recursion_triggers(_evaluation_path)

        for v_shape in self.value_shapes:
            if self.shape.sg.is_filtered_out_shape(v_shape):
                continue
            _nc, _r = self._evaluate_value_shape(
                executor, v_shape, target_graph, focus_value_nodes, potentially_recursive, _evaluation_path
            )
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_value_shape(
        self, executor, _v_shape, target_graph, focus_value_nodes, potentially_recursive, _evaluation_path
    ):
        _reports = []
        _non_conformant = False
        other_shape = self.shape.get_other_shape(_v_shape)
        if potentially_recursive and other_shape in potentially_recursive:
            warn(ShapeRecursionWarning(_evaluation_path))
            return _non_conformant, _reports
        if not other_shape:
            raise ReportableRuntimeError(
                "Shape pointed to by sh:qualifiedValueShape does not exist or is not a well-formed SHACL Shape."
            )
        if self.is_disjoint:
            # Textual Definition of Sibling Shapes:
            # Let Q be a shape in shapes graph G that declares a qualified cardinality constraint (by having values for sh:qualifiedValueShape and at least one of sh:qualifiedMinCount or sh:qualifiedMaxCount). Let ps be the set of shapes in G that have Q as a value of sh:property. If Q has true as a value for sh:qualifiedValueShapesDisjoint then the set of sibling shapes for Q is defined as the set of all values of the SPARQL property path sh:property/sh:qualifiedValueShape for any shape in ps minus the value of sh:qualifiedValueShape of Q itself. The set of sibling shapes is empty otherwise.
            sibling_shapes = set()
            parent_shapes = set(self.shape.sg.subjects(SH_property, self.shape.node))
            for p in iter(parent_shapes):
                parent_property_shapes = set(self.shape.sg.objects(p, SH_property))
                for s in iter(parent_property_shapes):
                    parent_property_qualifiedvalueshapes = set(self.shape.sg.objects(s, SH_qualifiedValueShape))
                    for sibling in parent_property_qualifiedvalueshapes:
                        if sibling == _v_shape:
                            continue
                        sibling_shapes.add(sibling)

            sibling_shapes = set(self.shape.get_other_shape(s) for s in sibling_shapes)
            sibling_shapes = {s for s in sibling_shapes if s is not None}
        else:
            sibling_shapes = set()
        upstream_reports = []
        for f, value_nodes in focus_value_nodes.items():
            number_conforms = 0
            for v in value_nodes:
                try:
                    _is_conform, _r = other_shape.validate(
                        executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                    )
                    if len(_r):
                        upstream_reports.extend(_r)
                    if _is_conform:
                        _conforms_to_sibling = False
                        for sibling_shape in sibling_shapes:
                            _c2, _r = sibling_shape.validate(
                                executor, target_graph, focus=v, _evaluation_path=_evaluation_path[:]
                            )
                            _conforms_to_sibling = _conforms_to_sibling or _c2
                        if not _conforms_to_sibling:
                            number_conforms += 1
                except ValidationFailure as v:
                    raise v
            if self.max_count is not None and number_conforms > self.max_count:
                _non_conformant = True
                _r = self.make_v_result(target_graph, f, constraint_component=SH_QualifiedMaxCountConstraintComponent)
                _reports.append(_r)
            if self.min_count is not None and number_conforms < self.min_count:
                _non_conformant = True
                _r = self.make_v_result(target_graph, f, constraint_component=SH_QualifiedMinCountConstraintComponent)
                _reports.append(_r)
        if len(upstream_reports) and self.shape.sg.debug:
            self.shape.logger.debug(
                "sh:qualifiedValueShape constraint reports will be ignored and not passed to the parent Node:"
            )
            for v_str, v_node, v_parts in upstream_reports:
                self.shape.logger.debug(v_str)
        return _non_conformant, _reports
