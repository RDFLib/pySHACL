# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

import rdflib

from rdflib import Literal
from rdflib.namespace import XSD

from pyshacl.consts import SH_construct
from pyshacl.errors import ReportableRuntimeError, RuleLoadError
from pyshacl.rdfutil import clone_graph
from pyshacl.rules.shacl_rule import SHACLRule
from pyshacl.sparql_query_helper import SPARQLQueryHelper


if TYPE_CHECKING:
    from pyshacl.shape import Shape

XSD_string = XSD.term('string')


class SPARQLRule(SHACLRule):
    __slots__ = ("_constructs", "_qh")

    def __init__(self, shape: 'Shape', rule_node: 'rdflib.term.Identifier'):
        """

        :param shape:
        :type shape: Shape
        :param rule_node:
        :type rule_node: rdflib.term.Identifier
        """
        super(SPARQLRule, self).__init__(shape, rule_node)
        construct_nodes = set(self.shape.sg.objects(self.node, SH_construct))
        if len(construct_nodes) < 1:
            raise RuleLoadError("No sh:construct on SPARQLRule", "https://www.w3.org/TR/shacl-af/#SPARQLRule")
        self._constructs = []
        for c in construct_nodes:
            if not isinstance(c, Literal) or not (
                c.datatype == XSD_string or c.language is not None or isinstance(c.value, str)
            ):
                raise RuleLoadError(
                    "SPARQLRule sh:construct must be an xsd:string", "https://www.w3.org/TR/shacl-af/#SPARQLRule"
                )
            self._constructs.append(str(c.value))
        query_helper = SPARQLQueryHelper(self.shape, self.node, None, deactivated=self._deactivated)
        query_helper.collect_prefixes()
        self._qh = query_helper

    def apply(self, data_graph):
        focus_nodes = self.shape.focus_nodes(data_graph)  # uses target nodes to find focus nodes
        applicable_nodes = self.filter_conditions(focus_nodes, data_graph)
        construct_graphs = set()
        for a in applicable_nodes:
            for c in self._constructs:
                init_bindings = {}
                found_this = SPARQLQueryHelper.bind_this_regex.search(c)
                if found_this:
                    init_bindings['this'] = a
                c = self._qh.apply_prefixes(c)
                results = data_graph.query(c, initBindings=init_bindings)
                if results.type != "CONSTRUCT":
                    raise ReportableRuntimeError("Query executed by a SHACL SPARQLRule must be CONSTRUCT query.")
                construct_graphs.add(results.graph)
        for g in construct_graphs:
            data_graph = clone_graph(g, target_graph=data_graph)
