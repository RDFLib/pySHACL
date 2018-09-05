# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-shape
"""
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_property, SH_node
from pyshacl.errors import ConstraintLoadError

SH_PropertyShapeComponent = SH.term('PropertyShapeComponent')
SH_NodeShapeComponent = SH.term('NodeShapeComponent')


class PropertyShapeComponent(ConstraintComponent):
    """
    sh:property can be used to specify that each value node has a given property shape.
    Link:
    https://www.w3.org/TR/shacl/#PropertyShapeComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the validation of v as focus node against the property shape $property produces a failure. Otherwise, the validation results are the results of validating v as focus node against the property shape $property.
    """

    def __init__(self, shape):
        super(PropertyShapeComponent, self).__init__(shape)
        property_shapes = list(self.shape.objects(SH_property))
        if len(property_shapes) < 1:
            raise ConstraintLoadError(
                "PropertyShapeComponent must have at least one sh:property predicate.",
                "https://www.w3.org/TR/shacl/#MinCountConstraintComponent")
        self.property_shapes = property_shapes

    @classmethod
    def constraint_parameters(cls):
        return [SH_property]

    @classmethod
    def constraint_name(cls):
        return "PropertyShapeComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_PropertyShapeComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        fails = []
        non_conformant = False

        for p_shape in self.property_shapes:
            _nc, _f = self._evaluate_property_shape(p_shape, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            fails.extend(_f)
        return (not non_conformant), fails

    def _evaluate_property_shape(self, prop_shape, target_graph, f_v_dict):
        fails = []
        non_conformant = False
        prop_shape = self.shape.get_other_shape(prop_shape)
        if not prop_shape or not prop_shape.is_property_shape:
            raise RuntimeError("Shape pointed to by sh:property does not exist or is not a well-formed SHACL PropertyShape.")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                _is_conform, _f = prop_shape.validate(target_graph, focus=v)
                non_conformant = non_conformant or (not _is_conform)
                fails.extend(_f)
        return non_conformant, fails


class NodeShapeComponent(ConstraintComponent):
    """
    sh:node specifies the condition that each value node conforms to the given node shape.
    Link:
    https://www.w3.org/TR/shacl/#NodeShapeComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the conformance checking of v against $node produces a failure. Otherwise, if v does not conform to $node, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(NodeShapeComponent, self).__init__(shape)
        node_shapes = list(self.shape.objects(SH_node))
        if len(node_shapes) < 1:
            raise ConstraintLoadError(
                "NodeShapeComponent must have at least one sh:node predicate.",
                "https://www.w3.org/TR/shacl/#NodeShapeComponent")
        self.node_shapes = node_shapes

    @classmethod
    def constraint_parameters(cls):
        return [SH_node]

    @classmethod
    def constraint_name(cls):
        return "NodeShapeComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_NodeShapeComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        fails = []
        non_conformant = False

        for n_shape in self.node_shapes:
            _nc, _f = self._evaluate_node_shape(n_shape, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            fails.extend(_f)
        return (not non_conformant), fails

    def _evaluate_node_shape(self, node_shape, target_graph, f_v_dict):
        fails = []
        non_conformant = False
        node_shape = self.shape.get_other_shape(node_shape)
        if not node_shape or node_shape.is_property_shape:
            raise RuntimeError("Shape pointed to by sh:node does not exist or is not a well-formed SHACL NodeShape.")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                _is_conform, _f = node_shape.validate(target_graph, focus=v)
                # ignore the fails from the node, create our own fail
                if (not _is_conform) or len(_f) > 0:
                    non_conformant = True
                    fail = self.make_failure(f, value_node=v)
                    fails.append(fail)
        return non_conformant, fails