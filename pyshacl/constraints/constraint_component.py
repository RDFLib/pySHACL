
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import abc
from rdflib import BNode
from pyshacl.consts import *
from pyshacl.rdfutil import stringify_node


class ConstraintComponent(object, metaclass=abc.ABCMeta):
    """
    Abstract Constraint Component Class
    All Constraint Components must inherit from this class.
    """

    def __init__(self, shape):
        """

        :param shape:
        :type shape: pyshacl.shape.Shape
        """
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
    def evaluate(self, target_graph, focus_value_nodes, _evaluation_path):
        return NotImplementedError()  # pragma: no cover

    def __str__(self):
        c_name = str(self.__class__.__name__)
        shape_id = str(self.shape)
        return "<{} on {}>".format(c_name, shape_id)

    def recursion_triggers(self, _evaluation_path):
        shape = self.shape
        eval_length = len(_evaluation_path)
        maybe_recursive = []
        if eval_length >= 6:
            _shape, _self = _evaluation_path[eval_length - 2:]
            if _shape is not shape or _self is not self:
                raise RuntimeError("Bad evaluation path construction")
            seen_before = [i for i, x in enumerate(_evaluation_path[:eval_length-2]) if x is shape] #_evaluation_path.index(shape, 0, eval_length - 2)
            for s in seen_before:
                for i, p in enumerate(_evaluation_path[s + 1:-2]):
                    if isinstance(p, ConstraintComponent):
                        if p.shape is shape and p.__class__ == self.__class__:
                            try:
                                next_shape = _evaluation_path[s + 1 + i + 1]
                                maybe_recursive.append(next_shape)
                            except IndexError:
                                pass
                        break
        return maybe_recursive


    def make_v_result_description(self, datagraph, focus_node, severity, value_node=None, result_path=None,
                                  constraint_component=None, source_constraint=None, extra_messages=None):
        """
        :param datagraph:
        :type datagraph: rdflib.Graph | rdflib.Dataset
        :param focus_node:
        :type focus_node: rdflib.term.Identifier
        :param value_node:
        :type value_node: rdflib.term.Identifier | None
        :param result_path:
        :param constraint_component:
        :param source_constraint:
        :param extra_messages:
        :return:
        """
        sg = self.shape.sg.graph
        constraint_component = constraint_component or self.shacl_constraint_class()
        constraint_name = self.constraint_name()
        if severity == SH_Violation:
            severity_desc = "Constraint Violation"
        else:
            severity_desc = "Constraint Report"
        source_shape_text = stringify_node(sg, self.shape.node)
        severity_node_text = stringify_node(sg, severity)
        focus_node_text = stringify_node(datagraph or sg, focus_node)
        desc = "{} in {} ({}):\n\tSeverity: {}\n\tSource Shape: {}\n\tFocus Node: {}\n"\
            .format(severity_desc, constraint_name,
                    str(constraint_component),
                    severity_node_text, source_shape_text, focus_node_text)
        if value_node is not None:
            val_node_string = stringify_node(datagraph or sg, value_node)
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

    def make_v_result(self, datagraph, focus_node, value_node=None, result_path=None,
                      constraint_component=None, source_constraint=None,
                      extra_messages=None):
        """
        :param datagraph:
        :type datagraph: rdflib.Graph | rdflib.Dataset
        :param focus_node:
        :type focus_node: rdflib.term.Identifier
        :param value_node:
        :type value_node: rdflib.term.Identifier | None
        :param result_path:
        :param constraint_component:
        :param source_constraint:
        :param extra_messages:
        :return:
        """
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
            datagraph, focus_node, severity, value_node,
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
