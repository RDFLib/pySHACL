# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Type, Union

from pyshacl.consts import RDF_type, SH_rule, SH_SPARQLRule, SH_TripleRule
from pyshacl.errors import ReportableRuntimeError, RuleLoadError
from pyshacl.pytypes import GraphLike
from pyshacl.rules.sparql import SPARQLRule
from pyshacl.rules.triple import TripleRule

if TYPE_CHECKING:
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph

    from .shacl_rule import SHACLRule


def gather_rules(shacl_graph: 'ShapesGraph', iterate_rules=False) -> Dict['Shape', List['SHACLRule']]:
    """

    :param shacl_graph:
    :type shacl_graph: ShapesGraph
    :return:
    :rtype: Dict[Shape, List[SHACLRule]]
    """
    triple_rule_nodes = set(shacl_graph.subjects(RDF_type, SH_TripleRule))
    sparql_rule_nodes = set(shacl_graph.subjects(RDF_type, SH_SPARQLRule))
    if shacl_graph.js_enabled:
        from pyshacl.extras.js.rules import JSRule, SH_JSRule

        js_rule_nodes = set(shacl_graph.subjects(RDF_type, SH_JSRule))
        use_JSRule: Union[bool, Type] = JSRule
    else:
        use_JSRule = False
        js_rule_nodes = set()
    overlaps = triple_rule_nodes.intersection(sparql_rule_nodes)
    if len(overlaps) > 0:
        raise RuleLoadError(
            "A SHACL Rule cannot be both a TripleRule and a SPARQLRule.",
            "https://www.w3.org/TR/shacl-af/#rules-syntax",
        )
    overlaps = triple_rule_nodes.intersection(js_rule_nodes)
    if len(overlaps) > 0:
        raise RuleLoadError(
            "A SHACL Rule cannot be both a TripleRule and a JSRule.",
            "https://www.w3.org/TR/shacl-af/#rules-syntax",
        )
    overlaps = sparql_rule_nodes.intersection(js_rule_nodes)
    if len(overlaps) > 0:
        raise RuleLoadError(
            "A SHACL Rule cannot be both a SPARQLRule and a JSRule.",
            "https://www.w3.org/TR/shacl-af/#rules-syntax",
        )
    used_rules = shacl_graph.subject_objects(SH_rule)
    ret_rules = defaultdict(list)
    for sub, obj in used_rules:
        try:
            shape: Shape = shacl_graph.lookup_shape_from_node(sub)
        except (AttributeError, KeyError):
            raise RuleLoadError(
                "The shape that rule is attached to is not a valid SHACL Shape.",
                "https://www.w3.org/TR/shacl-af/#rules-syntax",
            )
        if obj in triple_rule_nodes:
            rule: SHACLRule = TripleRule(shape, obj, iterate=iterate_rules)
        elif obj in sparql_rule_nodes:
            rule = SPARQLRule(shape, obj)
        elif use_JSRule and callable(use_JSRule) and obj in js_rule_nodes:
            rule = use_JSRule(shape, obj)
        else:
            raise RuleLoadError(
                "when using sh:rule, the Rule must be defined as either a TripleRule or SPARQLRule.",
                "https://www.w3.org/TR/shacl-af/#rules-syntax",
            )
        ret_rules[shape].append(rule)
    return ret_rules


def apply_rules(shapes_rules: Dict, data_graph: GraphLike, iterate=False) -> int:
    # short the shapes dict by shapes sh:order before execution
    sorted_shapes_rules: List[Tuple[Any, Any]] = sorted(shapes_rules.items(), key=lambda x: x[0].order)
    total_modified = 0
    for shape, rules in sorted_shapes_rules:
        # sort the rules by the sh:order before execution
        rules = sorted(rules, key=lambda x: x.order)
        iterate_limit = 100
        while True:
            if iterate_limit < 1:
                raise ReportableRuntimeError("SHACL Shape Rule iteration exceeded iteration limit of 100.")
            iterate_limit -= 1
            this_modified = 0
            for r in rules:
                if r.deactivated:
                    continue
                n_modified = r.apply(data_graph)
                this_modified += n_modified
            if this_modified > 0:
                total_modified += this_modified
                if iterate:
                    continue
                else:
                    break
            break
    return total_modified
