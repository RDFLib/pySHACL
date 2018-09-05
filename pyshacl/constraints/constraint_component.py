
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import abc
from rdflib import BNode, Graph
from pyshacl.consts import *
import logging

log = logging.getLogger(__name__)

class ConstraintComponent(object, metaclass=abc.ABCMeta):

    def __init__(self, shape):
        self.shape = shape

    @classmethod
    @abc.abstractmethod
    def constraint_parameters(cls):
        return NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def constraint_name(cls):
        return NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def shacl_constraint_class(cls):
        return NotImplementedError()

    @abc.abstractmethod
    def evaluate(self, target_graph, focus_value_nodes):
        return NotImplementedError()

    def make_failure_description(self, severity, focus_node, value_node=None):
        constraint = self.shacl_constraint_class()
        constraint_name = self.constraint_name()
        if severity == SH_Violation:
            severity_desc = "Constraint Violation"
        else:
            severity_desc = "Failure"
        desc = "{} in {} ({}):\n\tShape: {}\n\tFocus Node: {}\n"\
            .format(severity_desc, constraint_name, str(constraint), str(self.shape.node), str(focus_node))
        if value_node is not None:
            if isinstance(value_node, rdflib.Literal):
                val_node_string = "Literal({}, lang={}, datatype={})".format(
                    str(value_node.value), str(value_node.language), str(value_node.datatype))
            else:
                val_node_string = str(value_node)
            desc += "\tValue Node: {}\n".format(val_node_string)
        if self.shape.is_property_shape:
            result_path = self.shape.path()
            if result_path is not None:
                desc += "\tResult Path: {}\n".format(str(result_path))
        return desc

    def make_failure(self, focus_node, value_node=None):
        constraint = self.shacl_constraint_class()
        severity = self.shape.severity()
        f_triples = list()
        f_node = BNode()
        f_triples.append((f_node, RDF_type, SH_ValidationResult))
        f_triples.append((f_node, SH_sourceConstraintComponent, constraint))
        f_triples.append((f_node, SH_sourceShape, self.shape.node))
        f_triples.append((f_node, SH_resultSeverity, severity))
        f_triples.append((f_node, SH_focusNode, focus_node))
        if value_node:
            f_triples.append((f_node, SH_value, value_node))
        if self.shape.is_property_shape:
            result_path = self.shape.path()
            f_triples.append((f_node, SH_resultPath, result_path))
        desc = self.make_failure_description(severity, focus_node, value_node)
        log.info(desc)
        return desc, f_node, f_triples
