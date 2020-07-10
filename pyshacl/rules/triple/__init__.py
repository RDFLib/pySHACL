# -*- coding: utf-8 -*-
import itertools

from typing import TYPE_CHECKING

import rdflib

from pyshacl.consts import SH_object, SH_path, SH_predicate, SH_subject, SH_this
from pyshacl.rules.shacl_rule import SHACLRule


if TYPE_CHECKING:
    from pyshacl.shape import Shape


class TripleRule(SHACLRule):
    __slots__ = ("s", "p", "o")

    def __init__(self, shape: 'Shape', rule_node: 'rdflib.term.Identifier'):
        """

        :param shape:
        :type shape: Shape
        :param rule_node:
        :type rule_node: rdflib.term.Identifier
        """
        super(TripleRule, self).__init__(shape, rule_node)
        my_subject_nodes = set(self.shape.sg.objects(self.node, SH_subject))
        if len(my_subject_nodes) < 1:
            raise RuntimeError("No sh:subject")
        elif len(my_subject_nodes) > 1:
            raise RuntimeError("Too many sh:subject")
        self.s = next(iter(my_subject_nodes))

        my_predicate_nodes = set(self.shape.sg.objects(self.node, SH_predicate))
        if len(my_predicate_nodes) < 1:
            raise RuntimeError("No sh:predicate")
        elif len(my_predicate_nodes) > 1:
            raise RuntimeError("Too many sh:predicate")
        self.p = next(iter(my_predicate_nodes))

        my_object_nodes = set(self.shape.sg.objects(self.node, SH_object))
        if len(my_object_nodes) < 1:
            raise RuntimeError("No sh:object")
        elif len(my_object_nodes) > 1:
            raise RuntimeError("Too many sh:object")
        self.o = next(iter(my_object_nodes))

    def get_nodes_from_node_expression(self, expr, focus_node, data_graph):
        if expr == SH_this:
            return [focus_node]
        elif isinstance(expr, (rdflib.URIRef, rdflib.Literal)):
            return [expr]
        elif isinstance(expr, rdflib.BNode):
            path_nodes = set(self.shape.sg.objects(expr, SH_path))
            if len(path_nodes) > 0:
                path_results = []
                for p in path_nodes:
                    vals = self.shape.value_nodes_from_path(self.shape.sg, focus_node, p, data_graph)
                    path_results.extend(vals)
                return path_results
            else:
                raise NotImplementedError("Unsupported expression s, p, or o, in SHACL TripleRule")
        else:
            raise NotImplementedError("Unsupported expression s, p, or o, in SHACL TripleRule")

    def apply(self, data_graph):
        focus_nodes = self.shape.focus_nodes(data_graph)  # uses target nodes to find focus nodes
        applicable_nodes = self.filter_conditions(focus_nodes, data_graph)
        for a in applicable_nodes:
            s_set = self.get_nodes_from_node_expression(self.s, a, data_graph)
            p_set = self.get_nodes_from_node_expression(self.p, a, data_graph)
            o_set = self.get_nodes_from_node_expression(self.o, a, data_graph)
            new_triples = itertools.product(s_set, p_set, o_set)
            for i in iter(new_triples):
                data_graph.add(i)
