# -*- coding: utf-8 -*-
import rdflib
from pyshacl.consts import *
import logging

from pyshacl.errors import ShapeLoadError
from pyshacl.constraints import ALL_CONSTRAINT_PARAMETERS, CONSTRAINT_PARAMETERS_MAP

log = logging.getLogger(__name__)


class Shape(object):
    def __init__(self, sg, node, p=False):
        """

        :type sg: rdflib.Graph
        :type node: rdflib.term.Node
        :type p: bool
        """
        self.sg = sg
        self.node = node
        self.p = p

    @property
    def is_property_shape(self):
        return bool(self.p)

    def property_shapes(self):
        return self.sg.objects(self.node, SH_property)

    def parameters(self):
        return (p for p, v in self.sg.predicate_objects(self.node)
                if p in ALL_CONSTRAINT_PARAMETERS)

    def objects(self, predicate=None):
        return self.sg.objects(self.node, predicate)

    def target_nodes(self):
        return self.sg.objects(self.node, SH_targetNode)

    def target_classes(self):
        return self.sg.objects(self.node, SH_targetClass)

    def target_objects_of(self):
        return self.sg.objects(self.node, SH_targetObjectsOf)

    def target_subjects_of(self):
        return self.sg.objects(self.node, SH_targetSubjectsOf)

    def target(self):
        """

        :type target_graph: rdflib.Graph
        """
        target_nodes = self.target_nodes()
        target_classes = self.target_classes()
        target_objects_of = self.target_objects_of()
        target_subjects_of = self.target_objects_of()
        return (target_nodes, target_classes,
                target_objects_of, target_subjects_of)


    def focus_nodes(self, target_graph):
        """
        The set of focus nodes for a shape may be identified as follows:

        specified in a shape using target declarations
        specified in any constraint that references a shape in parameters of shape-expecting constraint parameters (e.g. sh:node)
        specified as explicit input to the SHACL processor for validating a specific RDF term against a shape
        :return:
        """
        (target_nodes, target_classes, _, _) = self.target()
        found_node_targets = set()
        for n in iter(target_nodes):
            # Note, a node_target _can_ be a literal.
            if n in iter(target_graph.subjects()):
                found_node_targets.add(n)
                continue
            elif n in iter(target_graph.predicates()):
                found_node_targets.add(n)
                continue
            elif n in iter(target_graph.objects()):
                found_node_targets.add(n)
                continue
        found_target_classes = set()
        for tc in iter(target_classes):
            s = target_graph.subjects(RDF_type, tc)
            for subject in iter(s):
                found_target_classes.add(subject)
            subc = target_graph.subjects(RDFS_subClassOf, tc)
            for subclass in iter(subc):
                s1 = target_graph.subjects(RDF_type, subclass)
                for subject in iter(s1):
                    found_target_classes.add(subject)
        # TODO: The other two types of targets
        return found_node_targets.union(found_target_classes)

    def value_nodes(self, target_graph, focus):
        if not isinstance(focus, (tuple, list, set)):
            focus = [focus]
        if self.is_property_shape:
            raise NotImplementedError("value nodes of property shapes are not yet implmented.")
        else:
            return focus

    def validate(self, target_graph, focus=None):
        assert isinstance(target_graph, rdflib.Graph)
        if focus is not None:
            if not isinstance(focus, (tuple, list, set)):
                focus = [focus]
        else:
            focus = self.focus_nodes(target_graph)
        run_count = 0
        parameters = self.parameters()
        results = {}
        value_nodes = self.value_nodes(target_graph, focus)
        for p in iter(parameters):
            constraint_component = CONSTRAINT_PARAMETERS_MAP[p]
            c = constraint_component(self)
            res = c.evaluate(target_graph, value_nodes)
            results[p] = res
            run_count += 1
        if run_count < 1:
            raise RuntimeError("A SHACL Shape should have at least one parameter or attached property shape.")
        return results

"""
A shape is an IRI or blank node s that fulfills at least one of the following conditions in the shapes graph:

    s is a SHACL instance of sh:NodeShape or sh:PropertyShape.
    s is subject of a triple that has sh:targetClass, sh:targetNode, sh:targetObjectsOf or sh:targetSubjectsOf as predicate.
    s is subject of a triple that has a parameter as predicate.
    s is a value of a shape-expecting, non-list-taking parameter such as sh:node, or a member of a SHACL list that is a value of a shape-expecting and list-taking parameter such as sh:or.
"""

def find_shapes(g, infer_shapes=False):
    """
    :param g: The Shapes Graph (SG)
    :type g: rdflib.Graph
    :returns: [Shape]
    """
    defined_node_shapes = set(g.subjects(RDF_type, SH_NodeShape))
    for s in defined_node_shapes:
        path_vals = list(g.objects(s, SH_path))
        if len(path_vals) > 0:
            raise ShapeLoadError(
                "A shape defined as a NodeShape cannot be the subject of a 'sh:path' predicate.",
                "https://www.w3.org/TR/shacl/#node-shapes")

    defined_prop_shapes = set(g.subjects(RDF_type, SH_PropertyShape))
    for s in defined_prop_shapes:
        if s in defined_node_shapes:
            raise ShapeLoadError(
                "A shape defined as a NodeShape cannot also be defined as a PropertyShape.",
                "https://www.w3.org/TR/shacl/#node-shapes")
        path_vals = list(g.objects(s, SH_path))
        if len(path_vals) < 1:
            raise ShapeLoadError(
                "A shape defined as a PropertyShape must be the subject of a 'sh:path' predicate.",
                "https://www.w3.org/TR/shacl/#property-shapes")
        elif len(path_vals) > 1:
            raise ShapeLoadError(
                "A shape defined as a PropertyShape cannot have more than one 'sh:path' predicate.",
                "https://www.w3.org/TR/shacl/#property-shapes")

    has_target_class = {s for s, o in g.subject_objects(SH_targetClass)}
    has_target_node = {s for s, o in g.subject_objects(SH_targetNode)}
    has_target_objects_of = {s for s, o in g.subject_objects(SH_targetObjectsOf)}
    has_target_subjects_of = {s for s, o in g.subject_objects(SH_targetSubjectsOf)}

    if infer_shapes:
        log.warning("Inferring shapes is not yet supported")

    other_shapes = set(has_target_class).union(set(has_target_node).union(set(has_target_objects_of).union(set(has_target_subjects_of))))
    found_node_shapes = set()
    found_prop_shapes = set()
    for s in other_shapes:
        if s in defined_node_shapes or s in defined_prop_shapes:
            continue
        path_vals = list(g.objects(s, SH_path))
        if len(path_vals) < 1:
            found_node_shapes.add(s)
        elif len(path_vals) > 1:
            raise ShapeLoadError(
                "A PropertyShape cannot have more than one 'sh:path' predicate.",
                "https://www.w3.org/TR/shacl/#property-shapes")
        else:
            found_prop_shapes.add(s)
    created_node_shapes = {Shape(g, s, False) for s in defined_node_shapes.union(found_node_shapes)}
    created_prop_shapes = {Shape(g, s, True) for s in defined_prop_shapes.union(found_prop_shapes)}
    return list(created_node_shapes.union(created_prop_shapes))