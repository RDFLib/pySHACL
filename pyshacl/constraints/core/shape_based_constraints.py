# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-shape
"""
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_property, SH_node
from pyshacl.errors import ConstraintLoadError, ValidationFailure, ReportableRuntimeError, ConstraintLoadWarning

SH_PropertyConstraintComponent = SH.term('PropertyConstraintComponent')
SH_NodeConstraintComponent = SH.term('NodeConstraintComponent')

SH_QualifiedValueCountConstraintComponent = SH.term('QualifiedValueConstraintComponent')
SH_QualifiedMaxCountConstraintComponent = SH.term('QualifiedMaxCountConstraintComponent')
SH_QualifiedMinCountConstraintComponent = SH.term('QualifiedMinCountConstraintComponent')

SH_qualifiedValueShape = SH.term('qualifiedValueShape')
SH_qualifiedValueShapesDisjoint = SH.term('qualifiedValueShapesDisjoint')
SH_qualifiedMinCount = SH.term('qualifiedMinCount')
SH_qualifiedMaxCount = SH.term('qualifiedMaxCount')


class PropertyConstraintComponent(ConstraintComponent):
    """
    sh:property can be used to specify that each value node has a given property shape.
    Link:
    https://www.w3.org/TR/shacl/#PropertyConstraintComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the validation of v as focus node against the property shape $property produces a failure. Otherwise, the validation results are the results of validating v as focus node against the property shape $property.
    """

    def __init__(self, shape):
        super(PropertyConstraintComponent, self).__init__(shape)
        property_shapes = list(self.shape.objects(SH_property))
        if len(property_shapes) < 1:
            raise ConstraintLoadError(
                "PropertyConstraintComponent must have at least one sh:property predicate.",
                "https://www.w3.org/TR/shacl/#PropertyConstraintComponent")
        self.property_shapes = property_shapes

    @classmethod
    def constraint_parameters(cls):
        return [SH_property]

    @classmethod
    def constraint_name(cls):
        return "PropertyConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_PropertyConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for p_shape in self.property_shapes:
            _nc, _r = self._evaluate_property_shape(p_shape, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_property_shape(self, prop_shape, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        prop_shape = self.shape.get_other_shape(prop_shape)
        if not prop_shape or not prop_shape.is_property_shape:
            raise ReportableRuntimeError(
                "Shape pointed to by sh:property does not exist "
                "or is not a well-formed SHACL PropertyShape.")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                _is_conform, _r = prop_shape.validate(target_graph, focus=v)
                non_conformant = non_conformant or (not _is_conform)
                reports.extend(_r)
        return non_conformant, reports


class NodeConstraintComponent(ConstraintComponent):
    """
    sh:node specifies the condition that each value node conforms to the given node shape.
    Link:
    https://www.w3.org/TR/shacl/#NodeShapeComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against $node produces a failure. Otherwise, if v does not conform to $node, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(NodeConstraintComponent, self).__init__(shape)
        node_shapes = list(self.shape.objects(SH_node))
        if len(node_shapes) < 1:
            raise ConstraintLoadError(
                "NodeConstraintComponent must have at least one sh:node predicate.",
                "https://www.w3.org/TR/shacl/#NodeConstraintComponent")
        self.node_shapes = node_shapes

    @classmethod
    def constraint_parameters(cls):
        return [SH_node]

    @classmethod
    def constraint_name(cls):
        return "NodeConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_NodeConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for n_shape in self.node_shapes:
            _nc, _r = self._evaluate_node_shape(n_shape, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_node_shape(self, node_shape, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        node_shape = self.shape.get_other_shape(node_shape)
        if not node_shape or node_shape.is_property_shape:
            raise ReportableRuntimeError(
                "Shape pointed to by sh:node does not exist or "
                "is not a well-formed SHACL NodeShape.")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                _is_conform, _r = node_shape.validate(target_graph, focus=v)
                # ignore the fails from the node, create our own fail
                if (not _is_conform) or len(_r) > 0:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


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

    def __init__(self, shape):
        super(QualifiedValueShapeConstraintComponent, self).__init__(shape)
        if not shape.is_property_shape:
            # Note, this no longer throws an error, this constraint is simply ignored on NodeShapes.
            raise ConstraintLoadWarning(
                "QualifiedValueShapeConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent")
        value_shapes = set(self.shape.objects(SH_qualifiedValueShape))
        if len(value_shapes) < 1:
            raise ConstraintLoadError(
                "QualifiedValueShapeConstraintComponent must have at least one sh:qualifiedValueShape predicate.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent")
        self.value_shapes = value_shapes
        min_count = set(self.shape.objects(SH_qualifiedMinCount))
        if len(min_count) < 1:
            min_count = None
        elif len(min_count) > 1:
            raise ConstraintLoadError(
                "QualifiedMinCountConstraintComponent must have at most one sh:qualifiedMinCount predicate.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent")
        else:
            min_count = next(iter(min_count))
            assert isinstance(min_count, rdflib.Literal) and isinstance(min_count.value, int)
            min_count = min_count.value

        max_count = set(self.shape.objects(SH_qualifiedMaxCount))
        if len(max_count) < 1:
            max_count = None
        elif len(max_count) > 1:
            raise ConstraintLoadError(
                "QualifiedMaxCountConstraintComponent must have at most one sh:qualifiedMaxCount predicate.",
                "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent")
        else:
            max_count = next(iter(max_count))
            assert isinstance(max_count, rdflib.Literal) and isinstance(max_count.value, int)
            max_count = max_count.value
        if min_count is None and max_count is None:
            raise ConstraintLoadError(
                "QualifiedValueShapeConstraintComponent must have at lease one sh:qualifiedMinCount or "
                "sh:qualifiedMaxCount", "https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent")
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
    def constraint_parameters(cls):
        return [SH_qualifiedValueShape, SH_qualifiedMinCount,
                SH_qualifiedValueShapesDisjoint, SH_qualifiedMaxCount]

    @classmethod
    def constraint_name(cls):
        return "QualifiedValueShapeConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        raise NotImplementedError("QualifiedValueShapeConstraintComponent must be either "
                                  "QualifiedMinCountConstraintComponent or "
                                  "QualifiedMaxCountConstraintComponent")

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for v_shape in self.value_shapes:
            _nc, _r = self._evaluate_value_shape(v_shape, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_value_shape(self, v_shape, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        other_shape = self.shape.get_other_shape(v_shape)
        if not other_shape:
            raise ReportableRuntimeError(
                "Shape pointed to by sh:property does not "
                "exist or is not a well-formed SHACL Shape.")
        if self.is_disjoint:
            # Textual Definition of Sibling Shapes:
            # Let Q be a shape in shapes graph G that declares a qualified cardinality constraint (by having values for sh:qualifiedValueShape and at least one of sh:qualifiedMinCount or sh:qualifiedMaxCount). Let ps be the set of shapes in G that have Q as a value of sh:property. If Q has true as a value for sh:qualifiedValueShapesDisjoint then the set of sibling shapes for Q is defined as the set of all values of the SPARQL property path sh:property/sh:qualifiedValueShape for any shape in ps minus the value of sh:qualifiedValueShape of Q itself. The set of sibling shapes is empty otherwise.
            sibling_shapes = set()
            parent_shapes = set(self.shape.sg.subjects(SH_property, self.shape.node))
            for p in iter(parent_shapes):
                found_siblings = set(self.shape.sg.objects(p, SH_property))
                for s in iter(found_siblings):
                    if s == self.shape.node:
                        continue
                    sibling_shapes.update(self.shape.sg.objects(s, SH_qualifiedValueShape))

            sibling_shapes = set(self.shape.get_other_shape(s) for s in sibling_shapes)
        else:
            sibling_shapes = set()
        for f, value_nodes in f_v_dict.items():
            number_conforms = 0
            for v in value_nodes:
                try:
                    _is_conform, _r = other_shape.validate(target_graph, focus=v)
                    if _is_conform:
                        _conforms_to_sibling = False
                        for sibling_shape in sibling_shapes:
                            _c2, _r = sibling_shape.validate(target_graph, focus=v)
                            _conforms_to_sibling = _conforms_to_sibling or _c2
                        if not _conforms_to_sibling:
                            number_conforms += 1
                except ValidationFailure as v:
                    raise v
            if self.max_count is not None and number_conforms > self.max_count:
                non_conformant = True
                _r = self.make_v_result(f, constraint_component=SH_QualifiedMaxCountConstraintComponent)
                reports.append(_r)
            if self.min_count is not None and number_conforms < self.min_count:
                non_conformant = True
                _r = self.make_v_result(f, constraint_component=SH_QualifiedMinCountConstraintComponent)
                reports.append(_r)
        return non_conformant, reports
