# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import rdflib
from datetime import date, time, datetime
from rdflib.term import Literal
from rdflib.namespace import RDF, XSD
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, RDFS_subClassOf, RDF_type,\
    SH_IRI, SH_BlankNode, SH_Literal, SH_IRIOrLiteral, SH_BlankNodeOrIRI,\
    SH_BlankNodeORLiteral
from pyshacl.errors import ConstraintLoadError

RDF_langString = RDF.term('langString')
XSD_string = XSD.term('string')
XSD_integer = XSD.term('integer')
XSD_float = XSD.term('float')
XSD_boolean = XSD.term('boolean')
XSD_date = XSD.term('date')
XSD_time = XSD.term('time')
XSD_dateTime = XSD.term('dateTime')

SH_class = SH.term('class')
SH_datatype = SH.term('datatype')
SH_nodeKind = SH.term('nodeKind')
SH_ClassConstraintComponent = SH.term('ClassConstraintComponent')
SH_DatatypeConstraintComponent = SH.term('DatatypeConstraintComponent')
SH_NodeKindConstraintComponent = SH.term('NodeKindConstraintComponent')

class ClassConstraintComponent(ConstraintComponent):
    """
    The condition specified by sh:class is that each value node is a SHACL instance of a given type.
    Link:
    https://www.w3.org/TR/shacl/#ClassConstraintComponent
    Textual Definition:
    For each value node that is either a literal, or a non-literal that is not a SHACL instance of $class in the data graph, there is a validation result with the value node as sh:value.
    """

    def __init__(self, shape):
        super(ClassConstraintComponent, self).__init__(shape)
        class_rules = list(self.shape.objects(SH_class))
        if len(class_rules) < 1:
            raise ConstraintLoadError(
                "ClassConstraintComponent must have at least one sh:class predicate.",
                "https://www.w3.org/TR/shacl/#ClassConstraintComponent")
        self.class_rules = class_rules

    @classmethod
    def constraint_parameters(cls):
        return [SH_class]

    @classmethod
    def constraint_name(cls):
        return "ClassConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_ClassConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False
        for c in self.class_rules:
            _n, _r = self._evaluate_class_rules(
                target_graph, focus_value_nodes, c)
            non_conformant = non_conformant or _n
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_class_rules(self, target_graph, f_v_dict, class_rule):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                found = False
                objs = target_graph.objects(v, RDF_type)
                for ctype in iter(objs):
                    if ctype == class_rule:
                        found = True
                        break
                    # Note, this only ones _one_ level of subclass traversing.
                    # For more levels, the whole target graph should be put through
                    # a RDFS reasoning engine.
                    subclasses = target_graph.objects(ctype, RDFS_subClassOf)
                    if class_rule in iter(subclasses):
                        found = True
                        break
                if not found:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
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

    def __init__(self, shape):
        super(DatatypeConstraintComponent, self).__init__(shape)
        datatype_rules = list(self.shape.objects(SH_datatype))
        if len(datatype_rules) < 1:
            raise ConstraintLoadError(
                "DatatypeConstraintComponent must have at least one sh:datatype predicate.",
                "https://www.w3.org/TR/shacl/#DatatypeConstraintComponent")
        elif len(datatype_rules) > 1:
            raise ConstraintLoadError(
                "DatatypeConstraintComponent must have at most one sh:datatype predicate.",
                "https://www.w3.org/TR/shacl/#DatatypeConstraintComponent")
        self.datatype_rule = datatype_rules[0]

    @classmethod
    def constraint_parameters(cls):
        return [SH_datatype]

    @classmethod
    def constraint_name(cls):
        return "DatatypeConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_DatatypeConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
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
                        matches = self._assert_actual_datatype(v, dtype_rule)
                    elif datatype is None and lang is None and \
                            dtype_rule == XSD_string:
                        matches = self._assert_actual_datatype(v, dtype_rule)
                    elif dtype_rule == RDF_langString and lang:
                        matches = self._assert_actual_datatype(v, dtype_rule)
                if not matches:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
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

    def __init__(self, shape):
        super(NodeKindConstraintComponent, self).__init__(shape)
        nodekind_rules = list(self.shape.objects(SH_nodeKind))
        if len(nodekind_rules) < 1:
            raise ConstraintLoadError(
                "NodeKindConstraintComponent must have at least one sh:nodeKind predicate.",
                "https://www.w3.org/TR/shacl/#NodeKindConstraintComponent")
        elif len(nodekind_rules) > 1:
            raise ConstraintLoadError(
                "NodeKindConstraintComponent must have at most one sh:nodeKind predicate.",
                "https://www.w3.org/TR/shacl/#NodeKindConstraintComponent")
        self.nodekind_rule = nodekind_rules[0]

    @classmethod
    def constraint_parameters(cls):
        return [SH_nodeKind]

    @classmethod
    def constraint_name(cls):
        return "NodeKindConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_NodeKindConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
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
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return (not non_conformant), reports

    def _evaluate_nodekind_rules(self, target_graph, f_v_pairs, nodekind_rule):
        reports = []
        non_conformant = False

        return non_conformant, reports
