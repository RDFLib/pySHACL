from itertools import chain
from typing import TYPE_CHECKING, Dict, Optional, Union

import rdflib
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID
from rdflib.namespace import NamespaceManager

from .clone import clone_blank_node, clone_graph, clone_node
from .consts import OWL, RDF, ConjunctiveLike, GraphLike, OWL_classes, OWL_properties, RDFS_classes, RDFS_properties

if TYPE_CHECKING:
    from rdflib import BNode

    from .consts import RDFNode

OWLNamedIndividual = OWL.NamedIndividual


def inoculate(data_graph: rdflib.Graph, ontology: rdflib.Graph):
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
    base_ds: ConjunctiveLike, ontology_ds: GraphLike, target_ds: Optional[Union[ConjunctiveLike, str]] = None
):
    """
    Make a clone of base_ds (dataset) and add RDFS and OWL triples from ontology_ds
    :param base_ds:
    :type base_ds: rdflib.Dataset
    :param ontology_ds:
    :type ontology_ds: rdflib.Dataset
    :param target_ds:
    :type target_ds: rdflib.Dataset|str|NoneType
    :return: The cloned Dataset with ontology triples from ontology_ds
    :rtype: rdflib.Dataset
    """

    # TODO: Decide whether we need to clone base_ds before calling this,
    # or we clone base_ds as part of this function
    default_union = base_ds.default_union
    base_named_graphs = [
        rdflib.Graph(base_ds.store, i, namespace_manager=base_ds.namespace_manager)  # type: ignore[arg-type]
        if not isinstance(i, rdflib.Graph)
        else i
        for i in base_ds.store.contexts(None)
    ]
    if isinstance(base_ds, rdflib.Dataset) and len(base_named_graphs) < 1:
        base_named_graphs = [
            rdflib.Graph(base_ds.store, DATASET_DEFAULT_GRAPH_ID, namespace_manager=base_ds.namespace_manager)
        ]
    base_default_context_id = base_ds.default_context.identifier
    if target_ds is None:
        target_ds = rdflib.Dataset(default_union=default_union)
        target_ds.namespace_manager = NamespaceManager(target_ds, 'core')
        target_ds.default_context.namespace_manager = target_ds.namespace_manager
    elif target_ds == "inplace" or target_ds == "base":
        target_ds = base_ds
    elif isinstance(target_ds, str):
        raise RuntimeError("target_ds cannot be a string (unless it is 'inplace' or 'base')")
    if isinstance(target_ds, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        if not isinstance(target_ds, rdflib.Dataset):
            raise RuntimeError("Cannot inoculate ConjunctiveGraph, use Dataset instead.")
    else:
        raise RuntimeError("Cannot inoculate datasets if target_ds passed in is not a Dataset itself.")
    if isinstance(ontology_ds, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
        ont_graphs = [
            rdflib.Graph(ontology_ds.store, i, namespace_manager=ontology_ds.namespace_manager)  # type: ignore[arg-type]
            if not isinstance(i, rdflib.Graph)
            else i
            for i in ontology_ds.store.contexts(None)
        ]
        ont_default_context_id = ontology_ds.default_context.identifier
    else:
        ont_graphs = [ontology_ds]
        ont_default_context_id = None
    if target_ds is base_ds or target_ds == "inplace" or target_ds == "base":
        target_ds = base_ds
        for bg in base_named_graphs:
            if len(base_named_graphs) > 1 and bg.identifier == base_default_context_id and len(bg) < 1:
                # skip empty default named graph in base_graph
                continue
            for og in ont_graphs:
                if len(ont_graphs) > 1 and og.identifier == ont_default_context_id and len(og) < 1:
                    # skip empty default named graph in ontology_graph
                    continue
                inoculate(bg, og)
    else:
        inoculated_graphs = {}
        for bg in base_named_graphs:
            if len(base_named_graphs) > 1 and bg.identifier == base_default_context_id and len(bg) < 1:
                # skip empty default named graph in base_graph
                continue
            target_g = rdflib.Graph(store=target_ds.store, identifier=bg.identifier)
            clone_g = clone_graph(bg, target_graph=target_g)
            for og in ont_graphs:
                if len(ont_graphs) > 1 and og.identifier == ont_default_context_id and len(og) < 1:
                    # skip empty default named graph in ontology_graph
                    continue
                inoculate(clone_g, og)
            inoculated_graphs[bg.identifier] = clone_g

        base_graph_identifiers = [bg.identifier for bg in base_named_graphs]
        base_default_context_id = base_ds.default_context.identifier
        target_default_context_id = target_ds.default_context.identifier
        if base_default_context_id != target_default_context_id:
            old_target_default_context = target_ds.default_context
            old_target_default_context_id = old_target_default_context.identifier
            if isinstance(target_ds, rdflib.Dataset):
                new_target_default_context = target_ds.graph(base_default_context_id)
            else:
                new_target_default_context = target_ds.get_context(base_default_context_id)
                target_ds.store.add_graph(new_target_default_context)
            target_ds.default_context = new_target_default_context
            if old_target_default_context_id not in base_graph_identifiers:
                if isinstance(target_ds, rdflib.Dataset):
                    target_ds.remove_graph(old_target_default_context)
                else:
                    target_ds.store.remove_graph(old_target_default_context)
            target_default_context_id = new_target_default_context.identifier
        else:
            if isinstance(target_ds, rdflib.Dataset):
                _ = target_ds.graph(target_default_context_id)
            else:
                t_default = target_ds.get_context(target_default_context_id)
                target_ds.store.add_graph(t_default)
        for i, ig in inoculated_graphs.items():
            if ig == target_ds.default_context or i == target_default_context_id:
                continue
            if isinstance(target_ds, rdflib.Dataset):
                _ = target_ds.graph(ig)  # alias to Dataset.add_graph()
            else:
                target_ds.store.add_graph(ig)

    return target_ds
