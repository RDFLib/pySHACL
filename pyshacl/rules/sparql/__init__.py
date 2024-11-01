# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, List, Optional, Sequence, Union

import rdflib
from rdflib import Literal
from rdflib.namespace import XSD

from pyshacl.consts import SH_construct
from pyshacl.errors import ReportableRuntimeError, RuleLoadError
from pyshacl.helper import get_query_helper_cls
from pyshacl.rdfutil import clone_graph

from ..shacl_rule import SHACLRule

if TYPE_CHECKING:
    from rdflib.term import URIRef

    from pyshacl.pytypes import GraphLike, RDFNode, SHACLExecutor
    from pyshacl.shape import Shape

XSD_string = XSD.string

SPARQL_RULE_ITERATE_LIMIT = 100


class SPARQLRule(SHACLRule):
    __slots__ = ("_constructs", "_qh")

    def __init__(self, executor: 'SHACLExecutor', shape: 'Shape', rule_node: 'rdflib.term.Identifier', **kwargs):
        """
        :param executor:
        :type executor: SHACLExecutor
        :param shape:
        :type shape: Shape
        :param rule_node:
        :type rule_node: rdflib.term.Identifier
        """
        super(SPARQLRule, self).__init__(executor, shape, rule_node, **kwargs)
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
        SPARQLQueryHelper = get_query_helper_cls()
        query_helper = SPARQLQueryHelper(self.shape, self.node, None, deactivated=self._deactivated)
        query_helper.collect_prefixes()
        self._qh = query_helper

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
        all_added = 0
        SPARQLQueryHelper = get_query_helper_cls()
        iterate_limit = int(SPARQL_RULE_ITERATE_LIMIT)
        while True:
            if iterate_limit < 1:
                raise ReportableRuntimeError(
                    f"Local SPARQLRule iteration exceeded iteration limit of {SPARQL_RULE_ITERATE_LIMIT}."
                )
            iterate_limit -= 1
            added = 0
            applicable_nodes = self.filter_conditions(focus_list, data_graph)
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
                    this_added = False
                    result_graph = results.graph
                    if result_graph is None:
                        raise ReportableRuntimeError("Query executed by a SHACL SPARQLRule did not return a Graph.")
                    for i in result_graph:
                        if not this_added and i not in data_graph:
                            this_added = True
                            # We only need to know at least one triple was added, then break!
                            break
                    if this_added:
                        added += 1
                        construct_graphs.add(result_graph)
            if added > 0:
                if isinstance(data_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
                    if target_graph_identifier is not None:
                        target_graph = data_graph.get_context(target_graph_identifier)
                    else:
                        target_graph = data_graph.default_context
                else:
                    target_graph = data_graph
                for g in construct_graphs:
                    data_graph = clone_graph(g, target_graph=target_graph)
                all_added += added
                if self.iterate:
                    continue  # Jump up to iterate
                else:
                    break  # Don't iterate
            break  # We've reached a local steady state
        return all_added
