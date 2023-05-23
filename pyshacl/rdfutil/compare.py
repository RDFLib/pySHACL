# -*- coding: utf-8 -*-
#
import datetime
from typing import List

import rdflib

from .consts import RDF_first, RDFS_Resource
from .stringify import stringify_node

# RDFLib 5.0+ has TOTAL_ORDER_CASTERS to force order on normally unorderable types,
# like datetimes and times. We specifically _dont_ want that here when comparing literals.
_FORCE_COMPARE_LITERAL_VALUE = [
    datetime.datetime,
    datetime.time,
]


def compare_blank_node(graph1: rdflib.Graph, bnode1, graph2: rdflib.Graph, bnode2, recursion=0):
    if not isinstance(graph1, rdflib.Graph) or not isinstance(graph2, rdflib.Graph):
        raise RuntimeError("Comparing blank nodes, graph1 and graph2 must must be RDFLib Graphs")
    if not isinstance(bnode1, rdflib.BNode) or not isinstance(bnode2, rdflib.BNode):
        raise RuntimeError("Comparing blank nodes, bnode1 and bnode2 must must be RDFLib BNodes")
    if recursion >= 10:
        return 1  # Cannot compare this deep

    def compare_list(l_node1, l_node2):
        # TODO, determine if lists must be ordered
        list_1_items = list(graph1.items(l_node1))
        list_2_items = list(graph2.items(l_node2))
        if len(list_1_items) > len(list_2_items):
            return 1
        elif len(list_2_items) > len(list_1_items):
            return -1
        eq = 0
        for i1 in list_1_items:
            found = None
            for i2 in list_2_items:
                eq = compare_node(graph1, i1, graph2, i2, recursion=recursion + 1)
                if eq == 0:
                    found = i2
                    break
            if found is not None:
                list_2_items.remove(found)
            else:
                eq = 1
                break
        return eq

    predicates1 = set(graph1.predicates(bnode1))
    predicates2 = set(graph2.predicates(bnode2))
    in_ps1_but_not_in_ps2: List = list()
    in_ps2_but_not_in_ps1: List = list()
    pred_objs_in_bnode1_but_not_bnode2: List = list()
    pred_objs_in_bnode2_but_not_bnode1: List = list()

    def return_eq(direction):
        nonlocal graph1, graph2, recursion, in_ps2_but_not_in_ps1, in_ps1_but_not_in_ps2
        nonlocal pred_objs_in_bnode1_but_not_bnode2, pred_objs_in_bnode2_but_not_bnode1
        if direction == 0:
            return direction
        if recursion <= 1:
            # TODO: Add a way to turn off this wall of text
            if direction < 0:
                print("BNode1 is smaller.")
            else:
                print("BNode1 is larger.")
            print("BNode1:")
            print(stringify_node(graph1, bnode1))
            print("BNode2:")
            print(stringify_node(graph2, bnode2))
            if len(in_ps1_but_not_in_ps2) > 0:
                print("In predicates of BNode1, but not in predicates of BNode2:")
                for p in in_ps1_but_not_in_ps2:
                    print("predicate: {}".format(stringify_node(graph1, p)))
            if len(in_ps2_but_not_in_ps1) > 0:
                print("In predicates of BNode2, but not in predicates of BNode1:")
                for p in in_ps2_but_not_in_ps1:
                    print("predicate: {}".format(stringify_node(graph2, p)))
            if len(pred_objs_in_bnode1_but_not_bnode2) > 0:
                print("In predicate/objects of BNode1, but not in predicate/objects of BNode2:")
                for p, o in pred_objs_in_bnode1_but_not_bnode2:
                    print("predicate: {} object: {}".format(stringify_node(graph1, p), stringify_node(graph1, o)))
            if len(pred_objs_in_bnode2_but_not_bnode1) > 0:
                print("In predicate/objects of BNode2, but not in predicate/objects of BNode1:")
                for p, o in pred_objs_in_bnode2_but_not_bnode1:
                    print("predicate: {} object: {}".format(stringify_node(graph2, p), stringify_node(graph2, o)))
        return direction

    if len(predicates1) < 1 and len(predicates2) < 1:
        return return_eq(0)
    elif len(predicates1) < 1:
        return return_eq(-1)
    elif len(predicates2) < 1:
        return return_eq(1)

    if RDF_first in predicates1 and RDF_first in predicates2:
        return compare_list(bnode1, bnode2)
    elif RDF_first in predicates1:
        return return_eq(1)
    elif RDF_first in predicates2:
        return return_eq(-1)

    bnode1_eq = 0
    for p1 in predicates1:
        if isinstance(p1, rdflib.URIRef):
            if p1 in predicates2:
                o1_list = list(graph1.objects(bnode1, p1))
                o2_list = list(graph2.objects(bnode2, p1))

                for o1 in o1_list:
                    if o1 == RDFS_Resource:
                        continue
                    found = None
                    for o2 in o2_list:
                        eq = compare_node(graph1, o1, graph2, o2, recursion=recursion + 1)
                        if eq == 0:
                            found = o2
                            break
                    if found is not None:
                        o2_list.remove(found)
                    else:
                        pred_objs_in_bnode1_but_not_bnode2.append((p1, o1))

                if len(pred_objs_in_bnode1_but_not_bnode2) > 0:
                    bnode1_eq = 1
            else:
                in_ps1_but_not_in_ps2.append(p1)
                bnode1_eq = 1
        else:
            raise NotImplementedError("Don't know to compare non-uri predicates on a blank node.")

    bnode2_eq = 0
    for p2 in predicates2:
        if isinstance(p2, rdflib.URIRef):
            if p2 in predicates1:
                o1_list = list(graph1.objects(bnode1, p2))
                o2_list = list(graph2.objects(bnode2, p2))

                for o2 in o2_list:
                    if o2 == RDFS_Resource:
                        continue
                    found = None
                    for o1 in o1_list:
                        eq = compare_node(graph2, o2, graph1, o1, recursion=recursion + 1)
                        if eq == 0:
                            found = o1
                            break
                    if found is not None:
                        o1_list.remove(found)
                    else:
                        pred_objs_in_bnode2_but_not_bnode1.append((p2, o2))

                if len(pred_objs_in_bnode2_but_not_bnode1) > 0:
                    bnode2_eq = 1
            else:
                in_ps2_but_not_in_ps1.append(p2)
                bnode2_eq = 1
        else:
            raise NotImplementedError("Don't know to compare non-uri predicates on a blank node.")

    if bnode1_eq == 0 and bnode2_eq == 0:
        return return_eq(0)
    if bnode1_eq == 1 and bnode2_eq == 1:
        return return_eq(2)
    if bnode1_eq == -1 and bnode2_eq == -1:
        return return_eq(-2)
    if bnode1_eq == 1 and bnode2_eq == 0:
        return return_eq(1)
    if bnode1_eq == 0 and bnode2_eq == 1:
        return return_eq(-1)
    if bnode1_eq == 0 and bnode2_eq == -1:
        return return_eq(1)
    if bnode1_eq == -1 and bnode2_eq == 0:
        return return_eq(-1)
    return return_eq(bnode1_eq)


def compare_literal(l1, l2):
    if l1.eq(l2):
        return 0
    # If we are not equal, but didn't get TypeError not NotImplementedError
    # then we know these are compatible/comparable datatypes already
    if l1.value.__class__ in _FORCE_COMPARE_LITERAL_VALUE:
        if l1.value == l2.value:
            return 0
        elif l1.value > l2.value:
            return 1
    elif l1 > l2:
        return 1
    return -1


def order_graph_literal(graph1: rdflib.Graph, lit1: rdflib.Literal, graph2: rdflib.Graph, lit2: rdflib.Literal):
    if not isinstance(graph1, rdflib.Graph) or not isinstance(graph2, rdflib.Graph):
        raise RuntimeError("Comparing ordered literals, graph1 and graph2 must must be RDFLib Graphs")
    if not isinstance(lit1, rdflib.Literal) or not isinstance(lit2, rdflib.Literal):
        raise RuntimeError("Comparing ordered literals, lit1 and lit2 must must be RDFLib Literals")
    try:
        order = compare_literal(lit1, lit2)
    except (TypeError, NotImplementedError):
        order = 1  # 1 = not-equal
    return order


def compare_node(graph1: rdflib.Graph, node1, graph2: rdflib.Graph, node2, recursion=0):
    if not isinstance(graph1, rdflib.Graph) or not isinstance(graph2, rdflib.Graph):
        raise RuntimeError("Comparing nodes, graph1 and graph2 must must be RDFLib Graphs")
    if not isinstance(node1, rdflib.term.Identifier) or not isinstance(node2, rdflib.term.Identifier):
        raise RuntimeError("Comparing nodes, node1 and node2 must must be RDFLib Identifiers")
    if isinstance(node1, rdflib.Literal) and isinstance(node2, rdflib.Literal):
        order = order_graph_literal(graph1, node1, graph2, node2)
    elif isinstance(node1, rdflib.Literal):
        order = 1  # node1 being a literal is greater
    elif isinstance(node2, rdflib.Literal):
        order = -1  # node2 being a literal is greater
    elif isinstance(node1, rdflib.BNode) and isinstance(node2, rdflib.BNode):
        order = compare_blank_node(graph1, node1, graph2, node2, recursion=recursion + 1)
    elif isinstance(node1, rdflib.BNode):
        order = 1  # node1 being a BNode is greater
    elif isinstance(node2, rdflib.BNode):
        order = -1  # node2 being a BNode is greater
    elif isinstance(node1, rdflib.URIRef) and isinstance(node2, rdflib.URIRef):
        s1 = str(node1)
        s2 = str(node2)
        if s1 > s2:
            order = 1
        elif s2 > s1:
            order = -1
        else:
            order = 0
    else:
        s1 = str(node1)
        s2 = str(node2)
        if s1 > s2:
            order = 1
        elif s2 > s1:
            order = -1
        else:
            order = 0
    return order
