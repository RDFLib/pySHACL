# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple, Type, Union

from rdflib import BNode, URIRef

from pyshacl.consts import RDF_type, SH_rule, SH_SPARQLRule, SH_TripleRule
from pyshacl.errors import ReportableRuntimeError, RuleLoadError
from pyshacl.pytypes import GraphLike, RDFNode, SHACLExecutor
from pyshacl.rules.sparql import SPARQLRule
from pyshacl.rules.triple import TripleRule

if TYPE_CHECKING:
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph

    from .shacl_rule import SHACLRule


def gather_rules(
    executor: SHACLExecutor,
    shacl_graph: 'ShapesGraph',
    from_shapes: Union[Sequence[Union[URIRef, BNode]], None] = None,
) -> Dict['Shape', List['SHACLRule']]:
    """
    :param executor:
    :type executor: SHACLExecutor
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
        if from_shapes is not None and sub not in from_shapes:
            # Skipping rule that is not in the whitelist of Shapes to use
            continue
        try:
            shape: Shape = shacl_graph.lookup_shape_from_node(sub)
        except (AttributeError, KeyError):
            raise RuleLoadError(
                "The shape that rule is attached to is not a valid SHACL Shape.",
                "https://www.w3.org/TR/shacl-af/#rules-syntax",
            )
        if obj in triple_rule_nodes:
            rule: SHACLRule = TripleRule(executor, shape, obj, iterate=executor.iterate_rules)
        elif obj in sparql_rule_nodes:
            rule = SPARQLRule(executor, shape, obj)
        elif use_JSRule and callable(use_JSRule) and obj in js_rule_nodes:
            rule = use_JSRule(executor, shape, obj)
        else:
            raise RuleLoadError(
                "when using sh:rule, the Rule must be defined as either a TripleRule or SPARQLRule.",
                "https://www.w3.org/TR/shacl-af/#rules-syntax",
            )
        ret_rules[shape].append(rule)
    return ret_rules


RULES_ITERATE_LIMIT = 100


def apply_rules(
    executor: SHACLExecutor,
    shapes_rules: Dict,
    data_graph: GraphLike,
    focus_nodes: Union[Sequence[RDFNode], None] = None,
) -> int:
    # short the shapes dict by shapes sh:order before execution
    sorted_shapes_rules: List[Tuple[Any, Any]] = sorted(shapes_rules.items(), key=lambda x: x[0].order)
    total_modified = 0
    for shape, rules in sorted_shapes_rules:
        # sort the rules by the sh:order before execution
        rules = sorted(rules, key=lambda x: x.order)
        _iterate_limit = int(RULES_ITERATE_LIMIT)
        while True:
            if _iterate_limit < 1:
                raise ReportableRuntimeError(
                    f"SHACL Shape Rule iteration exceeded iteration limit of {RULES_ITERATE_LIMIT}."
                )
            _iterate_limit -= 1
            this_modified = 0
            for r in rules:
                if r.deactivated:
                    continue
                n_modified = r.apply(data_graph, focus_nodes=focus_nodes)
                this_modified += n_modified
            if this_modified > 0:
                total_modified += this_modified
                if executor.iterate_rules:
                    continue
                else:
                    break
            break
    return total_modified
