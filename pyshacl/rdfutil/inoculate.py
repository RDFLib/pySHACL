from itertools import chain
from typing import TYPE_CHECKING, Dict, Optional, Union

import rdflib

from .clone import clone_blank_node, clone_dataset, clone_node
from .consts import OWL, RDF, ConjunctiveLike, GraphLike, OWL_classes, OWL_properties, RDFS_classes, RDFS_properties

if TYPE_CHECKING:
    from rdflib import BNode
    from rdflib.term import URIRef

    from .consts import RDFNode

OWLNamedIndividual = OWL.NamedIndividual


def inoculate(data_graph: rdflib.Graph, ontology: GraphLike) -> rdflib.Graph:
    """
    Copies all RDFS and OWL axioms (classes, relationship definitions, and properties)
    from the ontology graph into the data_graph.
    :param data_graph:
    :type data_graph:
    :param ontology:
    :type ontology:
    :return:
    :rtype:
    """
    copied_bnode_map: Dict[RDFNode, BNode] = {}
    copied_named_map: Dict[RDFNode, Union[BNode, RDFNode]] = {}
    ontology_ns = ontology.namespace_manager
    data_graph_ns = data_graph.namespace_manager

    if isinstance(ontology, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        # always set default_union true on the ontology DS
        ontology.default_union = True
    # Bind any missing ontology namespaces in the DataGraph NS manager.
    if ontology_ns is not data_graph_ns:
        data_graph_prefixes = {p: n for (p, n) in data_graph_ns.namespaces()}
        for p, n in ontology_ns.namespaces():
            if p not in data_graph_prefixes:
                data_graph_ns.bind(p, n)

    for ont_class in chain(RDFS_classes, OWL_classes):
        found_s = list(ontology.subjects(RDF.type, ont_class))
        for s in found_s:
            if isinstance(s, rdflib.BNode):
                if s in copied_bnode_map:
                    new_bnode = copied_bnode_map[s]
                else:
                    new_bnode = clone_blank_node(ontology, s, data_graph)
                    copied_bnode_map[s] = new_bnode
                data_graph.add((new_bnode, RDF.type, ont_class))
            else:
                if ont_class is OWLNamedIndividual:
                    if s in copied_named_map:
                        new_s = copied_named_map[s]
                    else:
                        # Whole node of NamedIndividual needs to be cloned
                        new_s = clone_node(ontology, s, data_graph, deep_clone=True)
                        copied_named_map[s] = new_s
                else:
                    # Shallow-copy this node from the ontology graph to the data graph
                    new_s = clone_node(ontology, s, data_graph, deep_clone=False)
                data_graph.add((new_s, RDF.type, ont_class))

    for ont_property in chain(RDFS_properties, OWL_properties):
        found_s_o = list(ontology.subject_objects(ont_property))
        for s2, o2 in found_s_o:
            if isinstance(s2, rdflib.BNode):
                if s2 in copied_bnode_map:
                    new_bnode = copied_bnode_map[s2]
                else:
                    new_bnode = clone_blank_node(ontology, s2, data_graph)
                    copied_bnode_map[s2] = new_bnode
                new_s = new_bnode
            else:
                new_s = s2
            if isinstance(o2, rdflib.BNode):
                if o2 in copied_bnode_map:
                    new_bnode = copied_bnode_map[o2]
                else:
                    new_bnode = clone_blank_node(ontology, o2, data_graph)
                    copied_bnode_map[o2] = new_bnode
                data_graph.add((new_s, ont_property, new_bnode))
            else:
                data_graph.add((new_s, ont_property, o2))

    # Finally add in any triples where a known NamedIndividual is the Object.
    for ni in copied_named_map.keys():
        found_s_p = list(ontology.subject_predicates(object=ni))
        for s3, p3 in found_s_p:
            if isinstance(p3, (rdflib.Literal, rdflib.BNode)):
                # predicates pointing to NamedIndividual should not be BNode or Literal
                continue
            if isinstance(s3, rdflib.BNode):
                if s3 in copied_bnode_map:
                    new_bnode = copied_bnode_map[s3]
                else:
                    new_bnode = clone_blank_node(ontology, s3, data_graph)
                    copied_bnode_map[s3] = new_bnode
                new_s = new_bnode
            else:
                new_s = s3

            data_graph.add((new_s, p3, ni))

    return data_graph


def inoculate_dataset(
    base_ds: ConjunctiveLike,
    ontology_ds: GraphLike,
    target_ds: Optional[Union[ConjunctiveLike, str]] = None,
    target_graph_identifier: Optional['URIRef'] = None,
):
    """
    Make a clone of base_ds (dataset) and add RDFS and OWL triples from ontology_ds
    :param base_ds:
    :type base_ds: rdflib.Dataset
    :param ontology_ds:
    :type ontology_ds: rdflib.Dataset|rdflib.ConjunctiveGraph|rdflib.Graph
    :param target_ds:
    :type target_ds: rdflib.Dataset|str|NoneType
    :param target_graph_identifier:
    :type target_graph_identifier: rdflib.URIRef | None
    :return: The cloned Dataset with ontology triples from ontology_ds
    :rtype: rdflib.Dataset
    """

    if target_ds is None:
        target_ds = clone_dataset(base_ds)
    elif target_ds is base_ds:
        pass
    elif target_ds == "inplace" or target_ds == "base":
        target_ds = base_ds
    elif isinstance(target_ds, str):
        raise RuntimeError("target_ds cannot be a string (unless it is 'inplace' or 'base')")

    if isinstance(target_ds, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        if not isinstance(target_ds, rdflib.Dataset):
            raise RuntimeError("Cannot inoculate ConjunctiveGraph, use Dataset instead.")
    else:
        raise RuntimeError("Cannot inoculate datasets if target_ds passed in is not a Dataset itself.")

    if target_graph_identifier:
        dest_graph = target_ds.get_context(target_graph_identifier)
    else:
        dest_graph = target_ds.default_context

    # inoculate() routine will set default_union on the ontology_ds if it is a Dataset
    inoculate(dest_graph, ontology_ds)

    return target_ds
