
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import abc
from rdflib import BNode
from pyshacl.consts import *
from pyshacl.util import stringify_blank_node, stringify_node


class ConstraintComponent(object, metaclass=abc.ABCMeta):
    """
    Abstract Constraint Component Class
    All Constraint Components must inherit from this class.
    """

    def __init__(self, shape):
        self.shape = shape

    @classmethod
    @abc.abstractmethod
    def constraint_parameters(cls):
        return NotImplementedError()  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def constraint_name(cls):
        return NotImplementedError()  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def shacl_constraint_class(cls):
        return NotImplementedError()  # pragma: no cover

    @abc.abstractmethod
    def evaluate(self, target_graph, focus_value_nodes):
        return NotImplementedError()  # pragma: no cover

    def make_v_result_description(self, severity, focus_node, value_node=None, result_path=None,
                                  constraint_component=None, source_constraint=None, extra_messages=None):
        sg = self.shape.sg.graph
        constraint_component = constraint_component or self.shacl_constraint_class()
        constraint_name = self.constraint_name()
        if severity == SH_Violation:
            severity_desc = "Constraint Violation"
        else:
            severity_desc = "Constraint Report"
        source_shape_text = stringify_node(sg, self.shape.node)
        focus_node_text = stringify_node(sg, focus_node)
        severity_node_text = stringify_node(sg, severity)
        desc = "{} in {} ({}):\n\tSeverity: {}\n\tSource Shape: {}\n\tFocus Node: {}\n"\
            .format(severity_desc, constraint_name,
                    str(constraint_component),
                    severity_node_text, source_shape_text, focus_node_text)
        if value_node is not None:
            val_node_string = stringify_node(sg, value_node)
            desc += "\tValue Node: {}\n".format(val_node_string)
        if result_path is None and self.shape.is_property_shape:
            result_path = self.shape.path()
        if result_path:
            result_path_text = stringify_node(sg, result_path)
            desc += "\tResult Path: {}\n".format(result_path_text)
        if source_constraint:
            sc_text = stringify_node(sg, source_constraint)
            desc += "\tSource Constraint: {}\n".format(sc_text)
        if extra_messages:
            for m in iter(extra_messages):
                if m in self.shape.message:
                    continue
                if isinstance(m, rdflib.Literal):
                    desc += "\tMessage: {}\n".format(str(m.value))
                else:  # pragma: no cover
                    desc += "\tMessage: {}\n".format(str(m))
        for m in self.shape.message:
            if isinstance(m, rdflib.Literal):
                desc += "\tMessage: {}\n".format(str(m.value))
            else:  # pragma: no cover
                desc += "\tMessage: {}\n".format(str(m))
        return desc

    def make_v_result(self, focus_node, value_node=None, result_path=None,
                      constraint_component=None, source_constraint=None,
                      extra_messages=None):
        constraint_component = constraint_component or self.shacl_constraint_class()
        severity = self.shape.severity
        r_triples = list()
        r_node = BNode()
        r_triples.append((r_node, RDF_type, SH_ValidationResult))
        r_triples.append((r_node, SH_sourceConstraintComponent, ('S', constraint_component)))
        r_triples.append((r_node, SH_sourceShape, ('S', self.shape.node)))
        r_triples.append((r_node, SH_resultSeverity, severity))
        r_triples.append((r_node, SH_focusNode, ('D', focus_node)))
        desc = self.make_v_result_description(
            severity, focus_node, value_node,
            result_path=result_path, constraint_component=constraint_component,
            source_constraint=source_constraint, extra_messages=extra_messages)
        if value_node:
            r_triples.append((r_node, SH_value, ('D', value_node)))
        if result_path is None and self.shape.is_property_shape:
            result_path = self.shape.path()
        if result_path:
            r_triples.append((r_node, SH_resultPath, ('S', result_path)))
        if source_constraint:
            r_triples.append((r_node, SH_sourceConstraint, ('S', source_constraint)))
        for m in self.shape.message:
            r_triples.append((r_node, SH_resultMessage, m))
        if extra_messages:
            for m in iter(extra_messages):
                if m in self.shape.message:
                    continue
                r_triples.append((r_node, SH_resultMessage, m))
        self.shape.logger.debug(desc)
        return desc, r_node, r_triples
