# -*- coding: utf-8 -*-
#
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import abc

from typing import TYPE_CHECKING, Dict, Iterable, List, Optional

import rdflib

from rdflib import BNode, Literal, URIRef

from pyshacl.consts import (
    RDF_type,
    SH_focusNode,
    SH_resultMessage,
    SH_resultPath,
    SH_resultSeverity,
    SH_sourceConstraint,
    SH_sourceConstraintComponent,
    SH_sourceShape,
    SH_ValidationResult,
    SH_value,
    SH_Violation,
)
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node


if TYPE_CHECKING:
    from pyshacl.shape import Shape


class ConstraintComponent(object, metaclass=abc.ABCMeta):
    __slots__ = ('shape',)

    """
    Abstract Constraint Component Class
    All Constraint Components must inherit from this class.
    """

    def __init__(self, shape: 'Shape'):
        """

        :param shape:
        :type shape: Shape
        """
        self.shape = shape  # type: Shape

    @classmethod
    @abc.abstractmethod
    def constraint_parameters(cls):
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def constraint_name(cls):
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def shacl_constraint_class(cls):
        raise NotImplementedError()  # pragma: no cover

    @abc.abstractmethod
    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        raise NotImplementedError()  # pragma: no cover

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        return []

    def __str__(self):
        c_name = str(self.__class__.__name__)
        shape_id = str(self.shape)
        return "<{} on {}>".format(c_name, shape_id)

    def recursion_triggers(self, _evaluation_path):
        shape = self.shape
        eval_length = len(_evaluation_path)
        maybe_recursive = []
        if eval_length >= 6:
            _shape, _self = _evaluation_path[eval_length - 2 :]
            if _shape is not shape or _self is not self:
                raise RuntimeError("Bad evaluation path construction")
            seen_before = [i for i, x in enumerate(_evaluation_path[: eval_length - 2]) if x is shape]
            for s in seen_before:
                for i, p in enumerate(_evaluation_path[s + 1 : -2]):
                    if isinstance(p, ConstraintComponent):
                        if p.shape is shape and p.__class__ == self.__class__:
                            try:
                                next_shape = _evaluation_path[s + 1 + i + 1]
                                maybe_recursive.append(next_shape)
                            except IndexError:
                                pass
                        break
        return maybe_recursive

    def make_v_result_description(
        self,
        datagraph: GraphLike,
        focus_node: 'rdflib.term.Identifier',
        severity: URIRef,
        value_node: Optional['rdflib.term.Identifier'],
        messages: List[str],
        result_path=None,
        constraint_component=None,
        source_constraint=None,
        extra_messages: Optional[Iterable] = None,
    ):

        """
        :param datagraph:
        :type datagraph: rdflib.Graph | rdflib.ConjunctiveGraph | rdflib.Dataset
        :param focus_node:
        :type focus_node: rdflib.term.Identifier
        :param severity:
        :type value_node: rdflib.URIRef
        :param value_node:
        :type value_node: rdflib.term.Identifier | None
        :param messages:
        :type messages: List[str]
        :param result_path:
        :param constraint_component:
        :param source_constraint:
        :param extra_messages:
        :type extra_messages: collections.abc.Iterable | None
        :return:
        """
        sg = self.shape.sg.graph
        constraint_component = constraint_component or self.shacl_constraint_class()
        constraint_name = self.constraint_name()
        if severity == SH_Violation:
            severity_desc = "Constraint Violation"
        else:
            severity_desc = "Validation Result"
        source_shape_text = stringify_node(sg, self.shape.node)
        severity_node_text = stringify_node(sg, severity)
        focus_node_text = stringify_node(datagraph or sg, focus_node)
        desc = "{} in {} ({}):\n\tSeverity: {}\n\tSource Shape: {}\n\tFocus Node: {}\n".format(
            severity_desc,
            constraint_name,
            str(constraint_component),
            severity_node_text,
            source_shape_text,
            focus_node_text,
        )
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
                if m in messages:
                    continue
                if isinstance(m, Literal):
                    desc += "\tMessage: {}\n".format(str(m.value))
                else:  # pragma: no cover
                    desc += "\tMessage: {}\n".format(str(m))
        for m in messages:
            if isinstance(m, Literal):
                desc += "\tMessage: {}\n".format(str(m.value))
            else:  # pragma: no cover
                desc += "\tMessage: {}\n".format(str(m))
        return desc

    def make_v_result(
        self,
        datagraph: GraphLike,
        focus_node: 'rdflib.term.Identifier',
        value_node: Optional['rdflib.term.Identifier'] = None,
        result_path=None,
        constraint_component=None,
        source_constraint=None,
        extra_messages: Optional[Iterable] = None,
    ):
        """
        :param datagraph:
        :type datagraph: rdflib.Graph | rdflib.ConjunctiveGraph | rdflib.Dataset
        :param focus_node:
        :type focus_node: rdflib.term.Identifier
        :param value_node:
        :type value_node: rdflib.term.Identifier | None
        :param result_path:
        :param constraint_component:
        :param source_constraint:
        :param extra_messages:
        :type extra_messages: collections.abc.Iterable | None
        :return:
        """
        constraint_component = constraint_component or self.shacl_constraint_class()
        severity = self.shape.severity
        sg = self.shape.sg.graph
        r_triples = list()
        r_node = BNode()
        r_triples.append((r_node, RDF_type, SH_ValidationResult))
        r_triples.append((r_node, SH_sourceConstraintComponent, (sg, constraint_component)))
        r_triples.append((r_node, SH_sourceShape, (sg, self.shape.node)))
        r_triples.append((r_node, SH_resultSeverity, severity))
        r_triples.append((r_node, SH_focusNode, (datagraph or sg, focus_node)))
        if value_node:
            r_triples.append((r_node, SH_value, (datagraph, value_node)))
        if result_path is None and self.shape.is_property_shape:
            result_path = self.shape.path()
        if result_path:
            r_triples.append((r_node, SH_resultPath, (sg, result_path)))
        if source_constraint:
            r_triples.append((r_node, SH_sourceConstraint, (sg, source_constraint)))
        messages = list(self.shape.message)
        if extra_messages:
            for m in iter(extra_messages):
                if m in messages:
                    continue
                r_triples.append((r_node, SH_resultMessage, m))
        elif not messages:
            messages = self.make_generic_messages(datagraph, focus_node, value_node) or messages
        for m in messages:
            r_triples.append((r_node, SH_resultMessage, m))
        desc = self.make_v_result_description(
            datagraph,
            focus_node,
            severity,
            value_node,
            messages,
            result_path=result_path,
            constraint_component=constraint_component,
            source_constraint=source_constraint,
            extra_messages=extra_messages,
        )
        self.shape.logger.debug(desc)
        return desc, r_node, r_triples
