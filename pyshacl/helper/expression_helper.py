import itertools
import operator
from typing import TYPE_CHECKING, List, Set, Union
from warnings import warn

import rdflib
from rdflib import Literal, URIRef

from pyshacl.consts import (
    RDF,
    SH_alternativePath,
    SH_filterShape,
    SH_intersection,
    SH_inversePath,
    SH_message,
    SH_nodes,
    SH_oneOrMorePath,
    SH_path,
    SH_this,
    SH_union,
    SH_zeroOrMorePath,
    SH_zeroOrOnePath,
)
from pyshacl.errors import ReportableRuntimeError, ShapeLoadError

if TYPE_CHECKING:
    from pyshacl.pytypes import GraphLike, RDFNode
    from pyshacl.shapes_graph import ShapesGraph


def value_nodes_from_path(sg, focus, path_val, target_graph, recursion=0):
    # Link: https://www.w3.org/TR/shacl/#property-paths
    if isinstance(path_val, URIRef):
        return set(target_graph.objects(focus, path_val))
    elif isinstance(path_val, Literal):
        raise ShapeLoadError(
            "Values of a property path cannot be a Literal.",
            "https://www.w3.org/TR/shacl/#property-paths",
        )
    # At this point, path_val _must_ be a BNode
    # TODO, the path_val BNode must be value of exactly one sh:path subject in the SG.
    if recursion >= 10:
        raise ReportableRuntimeError("Path traversal depth is too much!")
    find_list = set(sg.graph.objects(path_val, RDF.first))
    if len(find_list) > 0:
        first_node = next(iter(find_list))
        rest_nodes = set(sg.graph.objects(path_val, RDF.rest))
        go_deeper = True
        if len(rest_nodes) < 1:
            if recursion == 0:
                raise ReportableRuntimeError("A list of SHACL Paths must contain at least two path items.")
            else:
                go_deeper = False
        rest_node = next(iter(rest_nodes))
        if rest_node == RDF.nil:
            if recursion == 0:
                raise ReportableRuntimeError("A list of SHACL Paths must contain at least two path items.")
            else:
                go_deeper = False
        this_level_nodes = value_nodes_from_path(sg, focus, first_node, target_graph, recursion=recursion + 1)
        if not go_deeper:
            return this_level_nodes
        found_value_nodes = set()
        for tln in iter(this_level_nodes):
            value_nodes = value_nodes_from_path(sg, tln, rest_node, target_graph, recursion=recursion + 1)
            found_value_nodes.update(value_nodes)
        return found_value_nodes

    find_inverse = set(sg.graph.objects(path_val, SH_inversePath))
    if len(find_inverse) > 0:
        inverse_path = next(iter(find_inverse))
        return set(target_graph.subjects(inverse_path, focus))

    find_alternatives = set(sg.graph.objects(path_val, SH_alternativePath))
    if len(find_alternatives) > 0:
        alternatives_list = next(iter(find_alternatives))
        all_collected = set()
        visited_alternatives = 0
        for a in sg.graph.items(alternatives_list):
            found_nodes = value_nodes_from_path(sg, focus, a, target_graph, recursion=recursion + 1)
            visited_alternatives += 1
            all_collected.update(found_nodes)
        if visited_alternatives < 2:
            raise ReportableRuntimeError("List of SHACL alternate paths must have at least two path items.")
        return all_collected

    find_zero_or_more = set(sg.graph.objects(path_val, SH_zeroOrMorePath))
    if len(find_zero_or_more) > 0:
        zm_path = next(iter(find_zero_or_more))
        collection_set = set()
        # Note, the zero-or-more path always includes the current subject too!
        collection_set.add(focus)
        found_nodes = value_nodes_from_path(sg, focus, zm_path, target_graph, recursion=recursion + 1)
        search_deeper_nodes = set(iter(found_nodes))
        while len(search_deeper_nodes) > 0:
            current_node = search_deeper_nodes.pop()
            if current_node in collection_set:
                continue
            collection_set.add(current_node)
            found_more_nodes = value_nodes_from_path(sg, current_node, zm_path, target_graph, recursion=recursion + 1)
            search_deeper_nodes.update(found_more_nodes)
        return collection_set

    find_one_or_more = set(sg.graph.objects(path_val, SH_oneOrMorePath))
    if len(find_one_or_more) > 0:
        one_or_more_path = next(iter(find_one_or_more))
        collection_set = set()
        found_nodes = value_nodes_from_path(sg, focus, one_or_more_path, target_graph, recursion=recursion + 1)
        # Note, the one-or-more path should _not_ include the current focus
        search_deeper_nodes = set(iter(found_nodes))
        while len(search_deeper_nodes) > 0:
            current_node = search_deeper_nodes.pop()
            if current_node in collection_set:
                continue
            collection_set.add(current_node)
            found_more_nodes = value_nodes_from_path(
                sg, current_node, one_or_more_path, target_graph, recursion=recursion + 1
            )
            search_deeper_nodes.update(found_more_nodes)
        return collection_set

    find_zero_or_one = set(sg.graph.objects(path_val, SH_zeroOrOnePath))
    if len(find_zero_or_one) > 0:
        zero_or_one_path = next(iter(find_zero_or_one))
        collection_set = set()
        # Note, the zero-or-one path always includes the current subject too!
        collection_set.add(focus)
        found_nodes = value_nodes_from_path(sg, focus, zero_or_one_path, target_graph, recursion=recursion + 1)
        collection_set.update(found_nodes)
        return collection_set
    remaining = set(sg.graph.predicate_objects(path_val))
    if len(remaining) > 0:
        raise ShapeLoadError(
            "{} is not a known property for a sh:path. Malformed shape?".format(str(next(iter(remaining))[0])),
            "https://www.w3.org/TR/shacl/#property-paths",
        )

    raise ShapeLoadError(
        "Cannot get any values from sh:path property. Malformed shape?", "https://www.w3.org/TR/shacl/#property-paths"
    )


def nodes_from_node_expression(
    expr, focus_node, data_graph: 'GraphLike', sg: 'ShapesGraph', recurse_depth=0
) -> Union[Set[Union['RDFNode', None]], List[Union['RDFNode', None]]]:
    # https://www.w3.org/TR/shacl-af/#node-expressions
    if expr == SH_this:
        return [focus_node]
    if isinstance(expr, (rdflib.URIRef, rdflib.Literal)):
        return [expr]
    elif isinstance(expr, rdflib.BNode):
        unions = set(sg.objects(expr, SH_union))
        intersections = set(sg.objects(expr, SH_intersection))
        if len(unions) and len(intersections):
            raise ReportableRuntimeError("Cannot have sh:intersection and sh:union on the same bnode.")
        if recurse_depth > 8 and (len(unions) or len(intersections)):
            warn(Warning("sh:union, sh:intersection, or sh:function args depth too deep. Won't capture all of it!"))
            return []
        if len(unions):
            union_list = next(iter(unions))
            parts = list(sg.graph.items(union_list))
            all_nodes: Set[Union['RDFNode', None]] = set()
            for p in parts:
                new_parts = nodes_from_node_expression(p, focus_node, data_graph, sg, recurse_depth=recurse_depth + 1)
                all_nodes = all_nodes.union(new_parts)
            return all_nodes
        if len(intersections):
            inter_list = next(iter(intersections))
            parts = list(data_graph.items(inter_list))
            inter_nodes: Set[Union['RDFNode', None]] = set()
            new = True
            for p in parts:
                new_parts = nodes_from_node_expression(p, focus_node, data_graph, sg, recurse_depth=recurse_depth + 1)
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
                vals = value_nodes_from_path(sg, focus_node, p, data_graph)
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
            to_filter = nodes_from_node_expression(
                nodes_expr, focus_node, data_graph, sg, recurse_depth=recurse_depth + 1
            )
            passes = set()
            for n in to_filter:
                conforms, reports = filter_shape.validate(data_graph, n)
                if conforms:
                    passes.add(n)
            return passes
        # Got to here, the only other possibility is this is a FunctionExpression.
        remain_pairs = set(sg.predicate_objects(expr))
        fn_pairs = set()
        for rk, rv in remain_pairs:
            if rk == SH_message:
                # expressions can have a message, it doesn't affect the function
                continue
            elif isinstance(rv, rdflib.Literal):
                # pair is not list-valued, it can't be a function
                continue
            else:
                has_first = list(sg.objects(rv, RDF.first))
                if len(has_first) > 0:
                    fn_pairs.add((rk, rv))
        if len(fn_pairs) > 1:
            warn(Warning("More than one FunctionExpression found. Using the first one."))
        fnexpr, fnargslist = next(iter(fn_pairs))
        # find the function!
        try:
            function, optionals = sg.get_shacl_function(fnexpr)
        except KeyError:
            raise ReportableRuntimeError(
                "The SHACLFunction {} was not defined in this SHACL Shapes file.".format(fnexpr)
            )
        argslist_parts = list(sg.graph.items(fnargslist))
        args_sets: List[Union[List[Union['RDFNode', None]], Set[Union['RDFNode', None]]]] = [
            nodes_from_node_expression(p, focus_node, data_graph, sg, recurse_depth=recurse_depth + 1)
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
        for permus in args_permutations:
            result = function(data_graph, *permus)
            responses.add(result)
        return responses
    else:
        raise NotImplementedError("Unsupported expression {}".format(expr))
