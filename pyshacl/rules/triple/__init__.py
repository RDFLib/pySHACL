# -*- coding: utf-8 -*-
import itertools
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple, Union, cast

import rdflib

from pyshacl.consts import SH_object, SH_predicate, SH_subject
from pyshacl.errors import ReportableRuntimeError
from pyshacl.helper.expression_helper import nodes_from_node_expression
from pyshacl.rules.shacl_rule import SHACLRule

if TYPE_CHECKING:
    from rdflib.term import URIRef

    from pyshacl.pytypes import GraphLike, RDFNode, SHACLExecutor
    from pyshacl.shape import Shape

TRIPLE_RULE_ITERATE_LIMIT = 100


class TripleRule(SHACLRule):
    __slots__ = ("s", "p", "o")

    def __init__(self, executor: 'SHACLExecutor', shape: 'Shape', rule_node: 'rdflib.term.Identifier', **kwargs):
        """
        :param executor:
        :type executor: SHACLExecutor
        :param shape:
        :type shape: Shape
        :param rule_node:
        :type rule_node: rdflib.term.Identifier
        """
        super(TripleRule, self).__init__(executor, shape, rule_node, **kwargs)
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

    def apply(
        self,
        data_graph: 'GraphLike',
        focus_nodes: Optional[Sequence['RDFNode']] = None,
        target_graph_identifier: Optional['URIRef'] = None,
    ) -> int:
        focus_list: Sequence['RDFNode']
        if focus_nodes is not None:
            focus_list = list(focus_nodes)
        else:
            focus_list = list(self.shape.focus_nodes(data_graph))
        if self.executor.focus_nodes is not None and len(self.executor.focus_nodes) > 0:
            filtered_focus_nodes: List[Union[rdflib.URIRef]] = []
            for _fo in focus_list:  # type: RDFNode
                if isinstance(_fo, rdflib.URIRef) and _fo in self.executor.focus_nodes:
                    filtered_focus_nodes.append(_fo)
            len_filtered_focus = len(filtered_focus_nodes)
            if len_filtered_focus < 1:
                return 0
            focus_list = filtered_focus_nodes
        # uses target nodes to find focus nodes
        applicable_nodes = self.filter_conditions(focus_list, data_graph)
        all_added = 0
        iterate_limit = int(TRIPLE_RULE_ITERATE_LIMIT)
        while True:
            if iterate_limit < 1:
                raise ReportableRuntimeError(
                    f"sh:rule iteration exceeded iteration limit of {TRIPLE_RULE_ITERATE_LIMIT}."
                )
            iterate_limit -= 1
            added = 0
            to_add = []
            for a in applicable_nodes:
                s_set = nodes_from_node_expression(self.s, a, data_graph, self.shape.sg)
                p_set = nodes_from_node_expression(self.p, a, data_graph, self.shape.sg)
                o_set = nodes_from_node_expression(self.o, a, data_graph, self.shape.sg)
                new_triples = itertools.product(s_set, p_set, o_set)
                this_added = False
                for i in iter(new_triples):
                    if not this_added and i not in data_graph:
                        this_added = True
                    to_add.append(i)
                if this_added:
                    added += 1
            if added > 0:
                if isinstance(data_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
                    if target_graph_identifier is not None:
                        target_graph = data_graph.get_context(target_graph_identifier)
                    else:
                        target_graph = data_graph.default_context
                else:
                    target_graph = data_graph
                for i in to_add:
                    target_graph.add(cast(Tuple['RDFNode', 'RDFNode', 'RDFNode'], i))
                all_added += added
                if self.iterate:
                    continue  # Jump up to iterate
                else:
                    break  # Don't iterate
            break
        return all_added
