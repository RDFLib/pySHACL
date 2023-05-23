# -*- coding: utf-8 -*-
from decimal import Decimal

from rdflib import RDF, Literal

from pyshacl.consts import SH_condition, SH_deactivated, SH_order
from pyshacl.errors import RuleLoadError

RDF_first = RDF.first


class SHACLRuleCondition(object):
    __slots__ = ("rule", "cond_shape")

    def __init__(self, rule, cond_shape):
        self.rule = rule
        self.cond_shape = cond_shape

    def get_focus_nodes(self, data_graph):
        return self.cond_shape.focus_nodes(data_graph)

    def validate_condition(self, data_graph, focus_node):
        return self.cond_shape.validate(data_graph, focus=focus_node)


class SHACLRule(object):
    __slots__ = ("shape", "node", "iterate", "_deactivated")

    def __init__(self, shape, rule_node, iterate=False):
        """

        :param shape:
        :type shape: Shape
        :param rule_node:
        :type rule_node: rdflib.Identifier
        """
        super(SHACLRule, self).__init__()
        self.shape = shape
        self.node = rule_node
        self.iterate = False

        deactivated_nodes = list(self.shape.sg.objects(self.node, SH_deactivated))
        self._deactivated = len(deactivated_nodes) > 0 and bool(deactivated_nodes[0])

    @property
    def deactivated(self):
        return self._deactivated

    @property
    def order(self):
        order_nodes = list(self.shape.sg.objects(self.node, SH_order))
        if len(order_nodes) < 1:
            return Decimal("0.0")
        if len(order_nodes) > 1:
            raise RuleLoadError(
                "A SHACL Rule can have only one sh:order property.", "https://www.w3.org/TR/shacl-af/#rules-order"
            )
        order_node = next(iter(order_nodes))
        if not isinstance(order_node, Literal):
            raise RuleLoadError(
                "A SHACL Rule must be a numeric literal.", "https://www.w3.org/TR/shacl-af/#rules-order"
            )
        return Decimal(order_node.value)

    def get_conditions(self):
        cond_nodes = list(self.shape.sg.graph.objects(self.node, SH_condition))
        conditions = []
        for c in cond_nodes:
            # test_me = list(self.shape.sg.graph.predicate_objects(c))
            # check if this is a rdf:list
            first_nodes = list(self.shape.sg.graph.objects(c, RDF_first))
            if len(first_nodes) > 0:
                for c_item in self.shape.sg.graph.items(c):
                    try:
                        cond_shape = self.shape.sg.lookup_shape_from_node(c_item)
                    except (AttributeError, KeyError):
                        raise RuleLoadError(
                            "A SHACL Rule Condition must be an existing well-formed SHACL Shape.",
                            "https://www.w3.org/TR/shacl-af/#condition",
                        )
                    condition = SHACLRuleCondition(self, cond_shape)
                    conditions.append(condition)
            else:
                try:
                    cond_shape = self.shape.sg.lookup_shape_from_node(c)
                except (AttributeError, KeyError):
                    raise RuleLoadError(
                        "A SHACL Rule Condition must be an existing well-formed SHACL Shape.",
                        "https://www.w3.org/TR/shacl-af/#condition",
                    )
                condition = SHACLRuleCondition(self, cond_shape)
                conditions.append(condition)
        return conditions

    def filter_conditions(self, focus_nodes, data_graph):
        conditions = self.get_conditions()
        applicable_focus_nodes = []
        for f in focus_nodes:
            not_applicable = False
            for c in conditions:
                _conforms, _reports = c.validate_condition(data_graph, f)
                not_applicable = not_applicable or not (_conforms)
            if not not_applicable:
                applicable_focus_nodes.append(f)
        return applicable_focus_nodes

    def apply(self, data_graph):
        raise NotImplementedError()
