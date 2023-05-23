# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict, List

import rdflib
from rdflib.namespace import XSD
from rdflib.term import Literal

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import (
    RDF,
    RDFS,
    SH,
    SH_IRI,
    RDF_type,
    RDFS_subClassOf,
    SH_BlankNode,
    SH_BlankNodeOrIRI,
    SH_BlankNodeORLiteral,
    SH_datatype,
    SH_IRIOrLiteral,
    SH_Literal,
    SH_nodeKind,
)
from pyshacl.errors import ConstraintLoadError
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node

RDF_langString = RDF.langString
RDFS_Datatype = RDFS.Datatype
RDFS_Literal = RDFS.Literal
XSD_string = XSD.string
XSD_integer = XSD.integer
XSD_float = XSD.float
XSD_boolean = XSD.boolean
XSD_date = XSD.date
XSD_time = XSD.time
XSD_dateTime = XSD.dateTime
XSD_decimal = XSD.decimal

SH_class = SH["class"]
SH_ClassConstraintComponent = SH.ClassConstraintComponent
SH_DatatypeConstraintComponent = SH.DatatypeConstraintComponent
SH_NodeKindConstraintComponent = SH.NodeKindConstraintComponent


class ClassConstraintComponent(ConstraintComponent):
    """
    The condition specified by sh:class is that each value node is a SHACL instance of a given type.
    Link:
    https://www.w3.org/TR/shacl/#ClassConstraintComponent
    Textual Definition:
    For each value node that is either a literal, or a non-literal that is not a SHACL instance of $class in the data graph, there is a validation result with the value node as sh:value.
    """

    shacl_constraint_component = SH_ClassConstraintComponent

    def __init__(self, shape):
        super(ClassConstraintComponent, self).__init__(shape)
        class_rules = list(self.shape.objects(SH_class))
        if len(class_rules) < 1:
            raise ConstraintLoadError(
                "ClassConstraintComponent must have at least one sh:class predicate.",
                "https://www.w3.org/TR/shacl/#ClassConstraintComponent",
            )
        self.class_rules = class_rules

    @classmethod
    def constraint_parameters(cls):
        return [SH_class]

    @classmethod
    def constraint_name(cls):
        return "ClassConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        if len(self.class_rules) < 2:
            m = "Value does not have class {}".format(stringify_node(self.shape.sg.graph, self.class_rules[0]))
        else:
            rules = ", ".join(stringify_node(self.shape.sg.graph, c) for c in self.class_rules)
            m = "Value class is not in classes ({})".format(rules)
        return [Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False
        for c in self.class_rules:
            _n, _r = self._evaluate_class_rules(target_graph, focus_value_nodes, c)
            non_conformant = non_conformant or _n
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_class_rules(self, target_graph, f_v_dict, class_rule):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                found = False
                if isinstance(v, Literal):
                    self.shape.logger.debug(
                        "Class Constraint won't work with Literals. "
                        "Attempting to match Literal node {} to class of {} will fail.".format(v, class_rule)
                    )
                else:
                    objs = target_graph.objects(v, RDF_type)
                    for ctype in iter(objs):
                        if ctype == class_rule:
                            found = True
                            break
                        subclasses = target_graph.transitive_objects(ctype, RDFS_subClassOf)
                        if class_rule in iter(subclasses):
                            found = True
                            break
                if not found:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class DatatypeConstraintComponent(ConstraintComponent):
    """
    sh:datatype specifies a condition to be satisfied with regards to the datatype of each value node.
    Link:
    https://www.w3.org/TR/shacl/#DatatypeConstraintComponent
    Textual Definition:
    For each value node that is not a literal, or is a literal with a datatype that does not match $datatype, there is a validation result with the value node as sh:value. The datatype of a literal is determined following the datatype function of SPARQL 1.1. A literal matches a datatype if the literal's datatype has the same IRI and, for the datatypes supported by SPARQL 1.1, is not an ill-typed literal.
    """

    shacl_constraint_component = SH_DatatypeConstraintComponent

    def __init__(self, shape):
        super(DatatypeConstraintComponent, self).__init__(shape)
        datatype_rules = list(self.shape.objects(SH_datatype))
        if len(datatype_rules) < 1:
            raise ConstraintLoadError(
                "DatatypeConstraintComponent must have at least one sh:datatype predicate.",
                "https://www.w3.org/TR/shacl/#DatatypeConstraintComponent",
            )
        elif len(datatype_rules) > 1:
            raise ConstraintLoadError(
                "DatatypeConstraintComponent must have at most one sh:datatype predicate.",
                "https://www.w3.org/TR/shacl/#DatatypeConstraintComponent",
            )
        self.datatype_rule = datatype_rules[0]

    @classmethod
    def constraint_parameters(cls):
        return [SH_datatype]

    @classmethod
    def constraint_name(cls):
        return "DatatypeConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        m = "Value is not Literal with datatype {}".format(stringify_node(self.shape.sg.graph, self.datatype_rule))
        return [Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False
        dtype_rule = self.datatype_rule
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                matches = False
                if isinstance(v, Literal):
                    datatype = v.datatype
                    lang = v.language
                    if datatype == dtype_rule:
                        ill_formed = getattr(v, "ill_typed", None)
                        if ill_formed is True:
                            matches = False
                        else:
                            matches = self._assert_actual_datatype(v, dtype_rule)
                    elif dtype_rule == RDFS_Literal:
                        # Special case. All literals are instance of RDFS.Literal
                        # and all literals have datatype of RDFS.Literal
                        matches = True
                    elif dtype_rule == RDFS_Datatype and datatype:
                        # Special case. All literals with a datatype are instances of RDFS.Datatype
                        # and all literals with datatype have datatype of RDFS.Datatype
                        matches = True
                    elif datatype is None and lang is None and dtype_rule == XSD_string:
                        matches = self._assert_actual_datatype(v, dtype_rule)
                    elif dtype_rule == RDF_langString and lang:
                        matches = self._assert_actual_datatype(v, dtype_rule)
                else:
                    self.shape.logger.debug(
                        "Datatype Constraint only works on Literal datatypes. "
                        "Attempting to match non-Literal node {} to datatype of {} will fail.".format(v, dtype_rule)
                    )
                if not matches:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return (not non_conformant), reports

    def _assert_actual_datatype(self, value_node, datatype_rule):
        value = value_node.value
        if datatype_rule == XSD_string or datatype_rule == RDF_langString:
            return isinstance(value, (str, bytes))
        elif datatype_rule == XSD_integer:
            return isinstance(value, int)
        elif datatype_rule == XSD_float:
            return isinstance(value, float)
        elif datatype_rule == XSD_decimal:
            return isinstance(value, Decimal)
        elif datatype_rule == XSD_boolean:
            return isinstance(value, bool)
        elif datatype_rule == XSD_date:
            return isinstance(value, date)
        elif datatype_rule == XSD_time:
            return isinstance(value, time)
        elif datatype_rule == XSD_dateTime:
            return isinstance(value, datetime)
        else:
            # We don't know how to check other datatypes. Assume pass.
            return True


class NodeKindConstraintComponent(ConstraintComponent):
    """
    sh:nodeKind specifies a condition to be satisfied by the RDF node kind of each value node.
    Link:
    https://www.w3.org/TR/shacl/#NodeKindConstraintComponent
    Textual Definition:
    For each value node that does not match $nodeKind, there is a validation result with the value node as sh:value. Any IRI matches only sh:IRI, sh:BlankNodeOrIRI and sh:IRIOrLiteral. Any blank node matches only sh:BlankNode, sh:BlankNodeOrIRI and sh:BlankNodeOrLiteral. Any literal matches only sh:Literal, sh:BlankNodeOrLiteral and sh:IRIOrLiteral.
    """

    shacl_constraint_component = SH_NodeKindConstraintComponent

    def __init__(self, shape):
        super(NodeKindConstraintComponent, self).__init__(shape)
        nodekind_rules = list(self.shape.objects(SH_nodeKind))
        if len(nodekind_rules) < 1:
            raise ConstraintLoadError(
                "NodeKindConstraintComponent must have at least one sh:nodeKind predicate.",
                "https://www.w3.org/TR/shacl/#NodeKindConstraintComponent",
            )
        elif len(nodekind_rules) > 1:
            raise ConstraintLoadError(
                "NodeKindConstraintComponent must have at most one sh:nodeKind predicate.",
                "https://www.w3.org/TR/shacl/#NodeKindConstraintComponent",
            )
        self.nodekind_rule = nodekind_rules[0]

    @classmethod
    def constraint_parameters(cls):
        return [SH_nodeKind]

    @classmethod
    def constraint_name(cls):
        return "NodeKindConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        m = "Value is not of Node Kind {}".format(stringify_node(self.shape.sg.graph, self.nodekind_rule))
        return [Literal(m)]

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        n_rule = self.nodekind_rule
        reports = []
        non_conformant = False
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                match = False
                if isinstance(v, rdflib.BNode):
                    if n_rule in (SH_BlankNode, SH_BlankNodeORLiteral, SH_BlankNodeOrIRI):
                        match = True
                elif isinstance(v, rdflib.Literal):
                    if n_rule in (SH_Literal, SH_BlankNodeORLiteral, SH_IRIOrLiteral):
                        match = True
                elif isinstance(v, rdflib.term.Identifier):
                    if n_rule in (SH_IRI, SH_IRIOrLiteral, SH_BlankNodeOrIRI):
                        match = True
                if not match:
                    non_conformant = True
                    rept = self.make_v_result(target_graph, f, value_node=v)
                    reports.append(rept)
        return (not non_conformant), reports

    def _evaluate_nodekind_rules(self, target_graph, f_v_pairs, nodekind_rule):
        reports = []
        non_conformant = False

        return non_conformant, reports
