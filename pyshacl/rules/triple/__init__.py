# -*- coding: utf-8 -*-
import itertools
import operator

from typing import TYPE_CHECKING, List, Set, Union
from warnings import warn

import rdflib

from pyshacl.consts import (
    SH_filterShape,
    SH_intersection,
    SH_nodes,
    SH_object,
    SH_path,
    SH_predicate,
    SH_subject,
    SH_this,
    SH_union,
)
from pyshacl.errors import ReportableRuntimeError
from pyshacl.rules.shacl_rule import SHACLRule


if TYPE_CHECKING:
    from pyshacl.pytypes import GraphLike, RDFNode
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph


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

    def get_nodes_from_node_expression(
        self, expr, focus_node, data_graph: 'GraphLike', recurse_depth=0
    ) -> Union[Set['RDFNode'], List['RDFNode']]:
        if expr == SH_this:
            return [focus_node]
        sg = self.shape.sg  # type: ShapesGraph
        if isinstance(expr, (rdflib.URIRef, rdflib.Literal)):
            return [expr]
        elif isinstance(expr, rdflib.BNode):
            unions = set(sg.objects(expr, SH_union))
            intersections = set(sg.objects(expr, SH_intersection))
            if len(unions) and len(intersections):
                raise ReportableRuntimeError("Cannot have sh:intersection and sh:union on the same bnode.")
            if recurse_depth > 8 and (len(unions) or len(intersections)):
                warn(Warning("sh:union and sh:intersection depth too deep. Won't capture all of it!"))
                return []
            if len(unions):
                union_list = next(iter(unions))
                parts = list(sg.graph.items(union_list))
                all_nodes: Set['RDFNode'] = set()
                for p in parts:
                    new_parts = self.get_nodes_from_node_expression(
                        p, focus_node, data_graph, recurse_depth=recurse_depth + 1
                    )
                    all_nodes = all_nodes.union(new_parts)
                return all_nodes
            if len(intersections):
                inter_list = next(iter(intersections))
                parts = list(data_graph.items(inter_list))
                inter_nodes: Set[RDFNode] = set()
                new = True
                for p in parts:
                    new_parts = self.get_nodes_from_node_expression(
                        p, focus_node, data_graph, recurse_depth=recurse_depth + 1
                    )
                    if new is True:
                        inter_nodes = set(iter(new_parts))
                        new = False
                    else:
                        inter_nodes = inter_nodes.intersection(new_parts)
                return inter_nodes
            path_nodes = set(sg.objects(expr, SH_path))
            if len(path_nodes) > 0:
                path_results = []
                for p in path_nodes:
                    vals = self.shape.value_nodes_from_path(sg, focus_node, p, data_graph)
                    path_results.extend(vals)
                return path_results
            filter_shapes = set(sg.objects(expr, SH_filterShape))
            nodes_nodes = set(sg.objects(expr, SH_nodes))
            if len(filter_shapes) > 0:  # pragma: no cover
                # Note: Theres no tests for this whole filterShapes feature!
                if len(nodes_nodes) > 1:
                    warn(Warning("More than one sh:nodes found. Using the first one."))
                elif len(nodes_nodes) < 1:
                    raise ReportableRuntimeError("The Node FilterShape {} does not have sh:nodes.".format(expr))
                filter_shape = next(iter(filter_shapes))
                filter_shape = sg.lookup_shape_from_node(filter_shape)
                nodes_expr = next(iter(nodes_nodes))
                to_filter = self.get_nodes_from_node_expression(
                    nodes_expr, focus_node, data_graph, recurse_depth=recurse_depth + 1
                )
                passes = set()
                for n in to_filter:
                    conforms, reports = filter_shape.validate(data_graph, n)
                    if conforms:
                        passes.add(n)
                return passes
            # Got to here, the only other possibility is this is a FunctionExpression.
            remain_pairs = set(sg.predicate_objects(expr))
            if len(remain_pairs) > 1:
                warn(Warning("More than one NodeExpression found on the TripleRule. Using the first one."))
            fnexpr, fnargslist = next(iter(remain_pairs))
            # find the function!
            try:
                function, optionals = sg.get_shacl_function(fnexpr)
            except KeyError:
                raise ReportableRuntimeError(
                    "The SHACLFunction {} was not defined in this SHACL Shapes file.".format(fnexpr)
                )
            argslist_parts = list(sg.graph.items(fnargslist))
            args_sets = [
                self.get_nodes_from_node_expression(p, focus_node, data_graph, recurse_depth=recurse_depth + 1)
                for p in argslist_parts
            ]
            num_args_sets = len(args_sets)
            num_expected_args = len(optionals)
            if num_args_sets > num_expected_args:
                raise ReportableRuntimeError("Too many arguments given for {}".format(fnexpr))
            if num_args_sets < num_expected_args:
                # not enough, but some might be optional
                num_diff = num_expected_args - num_args_sets
                args_sets_slice = args_sets[0 - num_diff :]
                all_empty = itertools.accumulate(
                    {True if len(a) < 1 else False for a in args_sets_slice}, func=operator.or_
                )
                if all_empty:
                    args_sets = args_sets[:num_expected_args]
                else:
                    raise ReportableRuntimeError(
                        "Too few arguments given for {}, with non-optional arguments.".format(fnexpr)
                    )
            add_nones = set()
            for i, a in enumerate(args_sets):
                if len(a) < 1:
                    if optionals[i] is False:
                        warn(Warning("Got an empty set of nodes for a non-optional argument in {}.".format(fnexpr)))
                        return []
                    else:
                        add_nones.add(i)
            for i in add_nones:
                args_sets[i] = [None]
            args_permutations = list(itertools.product(*args_sets))
            responses = set()
            for p in args_permutations:
                result = function(data_graph, *p)
                responses.add(result)
            return responses

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
