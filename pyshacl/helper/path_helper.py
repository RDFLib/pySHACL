from typing import TYPE_CHECKING, Dict, Union

import rdflib

from pyshacl.consts import SH_alternativePath, SH_inversePath, SH_oneOrMorePath, SH_zeroOrMorePath, SH_zeroOrOnePath
from pyshacl.errors import ReportableRuntimeError

if TYPE_CHECKING:
    from pyshacl.shape import ShapesGraph


def shacl_path_to_sparql_path(
    shapes_graph: 'ShapesGraph', path_node, prefixes: Union[None, Dict] = None, recursion: int = 0
):
    """
    :param shapes_graph:
    :type shapes_graph: ShapesGraph
    :param path_node:
    :type path_node: rdflib.term.Node
    :param prefixes:
    :type prefixes: Union[None, Dict]
    :param recursion:
    :type recursion: int
    :returns: string
    :rtype: str
    """
    # Link: https://www.w3.org/TR/shacl/#property-paths
    if isinstance(path_node, rdflib.URIRef):
        string_uri = str(path_node)
        if prefixes is not None and len(prefixes) > 0:
            for p, ns in prefixes.items():
                if string_uri.startswith(ns):
                    string_uri = ':'.join([p, string_uri.replace(ns, '')])
                    return string_uri
        return f"<{string_uri}>"
    elif isinstance(path_node, rdflib.Literal):
        raise ReportableRuntimeError("Values of a property path cannot be a Literal.")
    # At this point, path_val _must_ be a BNode
    # TODO, the path_val BNode must be value of exactly one sh:path subject in the SG.
    if recursion >= 12:
        raise ReportableRuntimeError("Path traversal depth is too much!")
    top_level = recursion == 0
    sequence_list = list(shapes_graph.graph.items(path_node))
    if len(sequence_list) > 0:
        all_collected = []
        for s in sequence_list:
            seq1_string = shacl_path_to_sparql_path(shapes_graph, s, prefixes=prefixes, recursion=recursion + 1)
            all_collected.append(seq1_string)
        if len(all_collected) < 2:
            raise ReportableRuntimeError("List of SHACL sequence paths must have alt least two path items.")
        sequence_joined = " / ".join(all_collected)
        if top_level:
            return sequence_joined
        else:
            return f"({sequence_joined})"

    find_inverse = set(shapes_graph.objects(path_node, SH_inversePath))
    if len(find_inverse) > 0:
        inverse_path = find_inverse.pop()
        inverse_path_string = shacl_path_to_sparql_path(
            shapes_graph, inverse_path, prefixes=prefixes, recursion=recursion + 1
        )
        return f"^{inverse_path_string}"

    find_alternatives = set(shapes_graph.objects(path_node, SH_alternativePath))
    if len(find_alternatives) > 0:
        alternatives_list = find_alternatives.pop()
        all_collected = []
        for a in shapes_graph.graph.items(alternatives_list):
            alt1_string = shacl_path_to_sparql_path(shapes_graph, a, prefixes=prefixes, recursion=recursion + 1)
            all_collected.append(alt1_string)
        if len(all_collected) < 2:
            raise ReportableRuntimeError("List of SHACL alternate paths must have alt least two path items.")
        collected_joined = " | ".join(all_collected)
        if top_level:
            return collected_joined
        else:
            return f"({collected_joined})"

    find_zero_or_more = set(shapes_graph.objects(path_node, SH_zeroOrMorePath))
    if len(find_zero_or_more) > 0:
        zero_or_more_path = find_zero_or_more.pop()
        zom_path_string = shacl_path_to_sparql_path(
            shapes_graph, zero_or_more_path, prefixes=prefixes, recursion=recursion + 1
        )
        return f"{zom_path_string}*"

    find_zero_or_one = set(shapes_graph.objects(path_node, SH_zeroOrOnePath))
    if len(find_zero_or_one) > 0:
        zero_or_one_path = find_zero_or_one.pop()
        zoo_path_string = shacl_path_to_sparql_path(
            shapes_graph, zero_or_one_path, prefixes=prefixes, recursion=recursion + 1
        )
        return f"{zoo_path_string}?"

    find_one_or_more = set(shapes_graph.objects(path_node, SH_oneOrMorePath))
    if len(find_one_or_more) > 0:
        one_or_more_path = find_one_or_more.pop()
        oom_path_string = shacl_path_to_sparql_path(
            shapes_graph, one_or_more_path, prefixes=prefixes, recursion=recursion + 1
        )
        return f"{oom_path_string}+"

    raise NotImplementedError("That path method to get value nodes of property shapes is not yet implemented.")
