# -*- coding: utf-8 -*-
import rdflib
from pyshacl.consts import *
import logging

from pyshacl.errors import ShapeLoadError
from pyshacl.constraints import ALL_CONSTRAINT_PARAMETERS, CONSTRAINT_PARAMETERS_MAP

log = logging.getLogger(__name__)


class Shape(object):
    all_shapes = {}

    def __init__(self, sg, node, p=False, path=None):
        """

        :type sg: rdflib.Graph
        :type node: rdflib.term.Node
        :type p: bool
        """
        self.sg = sg
        self.node = node
        self._p = p
        self._path = path
        self.__class__.all_shapes[(id(sg), node)] = self

    def get_other_shape(self, shape_node):
        try:
            return self.__class__.all_shapes[(id(self.sg), shape_node)]
        except (KeyError, AttributeError):
            return None

    @property
    def is_property_shape(self):
        return bool(self._p)

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

    def implicit_class_targets(self):
        types = self.sg.objects(self.node, RDF_type)
        if RDFS_Class in iter(types):
            return [self.node]
        return []

    def target_objects_of(self):
        return self.sg.objects(self.node, SH_targetObjectsOf)

    def target_subjects_of(self):
        return self.sg.objects(self.node, SH_targetSubjectsOf)

    def path(self):
        if not self.is_property_shape:
            return None
        if self._path is not None:
            return self._path
        return next(list(self.objects(SH_path)))

    def severity(self):
        severity = list(self.objects(SH_severity))
        if len(severity):
            return severity[0]
        else:
            return SH_Violation

    def target(self):
        """

        :type target_graph: rdflib.Graph
        """
        target_nodes = self.target_nodes()
        target_classes = self.target_classes()
        implicit_targets = self.implicit_class_targets()
        target_objects_of = self.target_objects_of()
        target_subjects_of = self.target_subjects_of()
        return (target_nodes, target_classes, implicit_targets,
                target_objects_of, target_subjects_of)


    def focus_nodes(self, target_graph):
        """
        The set of focus nodes for a shape may be identified as follows:

        specified in a shape using target declarations
        specified in any constraint that references a shape in parameters of shape-expecting constraint parameters (e.g. sh:node)
        specified as explicit input to the SHACL processor for validating a specific RDF term against a shape
        :return:
        """
        (target_nodes, target_classes, implicit_classes, _, _) = self.target()
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
        target_classes = set(target_classes)
        target_classes.update(set(implicit_classes))
        found_target_instances = set()
        for tc in target_classes:
            s = target_graph.subjects(RDF_type, tc)
            for subject in iter(s):
                found_target_instances.add(subject)
            subc = target_graph.subjects(RDFS_subClassOf, tc)
            for subclass in iter(subc):
                s1 = target_graph.subjects(RDF_type, subclass)
                for subject in iter(s1):
                    found_target_instances.add(subject)
        # TODO: The other two types of targets
        return found_node_targets.union(found_target_instances)

    def value_nodes(self, target_graph, focus):
        """
        For each focus node, you can get a set of value nodes.
        For a Node Shape, each focus node has just one value node,
            which is just the focus_node
        :param target_graph:
        :param focus:
        :return:
        """
        if not isinstance(focus, (tuple, list, set)):
            focus = [focus]
        if not self.is_property_shape:
            return {f: set((f,)) for f in focus}
        path = self.path()
        focus_dict = {}
        for f in focus:
            if isinstance(path, rdflib.URIRef):
                values = set(target_graph.objects(f, path))
            else:
                raise NotImplementedError("value nodes of property shapes are not yet implmented.")
            focus_dict[f] = values
        return focus_dict


    def validate(self, target_graph, focus=None, bail_on_error=False):
        assert isinstance(target_graph, rdflib.Graph)
        if focus is not None:
            if not isinstance(focus, (tuple, list, set)):
                focus = [focus]
        else:
            focus = self.focus_nodes(target_graph)
        if len(focus) < 1:
            # Its possible for shapes to have _no_ focus nodes
            # (they are called in other ways)
            return True, []
        run_count = 0
        parameters = self.parameters()
        fails = []
        focus_value_nodes = self.value_nodes(target_graph, focus)
        non_conformant = False
        done_constraints = set()
        for p in iter(parameters):
            constraint_component = CONSTRAINT_PARAMETERS_MAP[p]
            if constraint_component in done_constraints:
                continue
            c = constraint_component(self)
            _is_conform, _fails = c.evaluate(target_graph, focus_value_nodes)
            non_conformant = non_conformant or (not _is_conform)
            fails.extend(_fails)
            run_count += 1
            done_constraints.add(constraint_component)
            if non_conformant and bail_on_error:
                break
        if run_count < 1:
            raise RuntimeError("A SHACL Shape should have at least one parameter or attached property shape.")
        return (not non_conformant), fails

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
    found_prop_shapes_paths = dict()
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
        found_prop_shapes_paths[s] = path_vals[0]

    has_target_class = {s for s, o in g.subject_objects(SH_targetClass)}
    has_target_node = {s for s, o in g.subject_objects(SH_targetNode)}
    has_target_objects_of = {s for s, o in g.subject_objects(SH_targetObjectsOf)}
    has_target_subjects_of = {s for s, o in g.subject_objects(SH_targetSubjectsOf)}
    subject_shapes = set(has_target_class).union(set(has_target_node).union(set(has_target_objects_of).union(set(has_target_subjects_of))))

    value_of_property = {o for s, o in g.subject_objects(SH_property)}
    value_of_node = {o for s, o in g.subject_objects(SH_node)}
    value_of_shapes = set(value_of_property).union(set(value_of_node))

    if infer_shapes:
        log.warning("Inferring shapes is not yet supported")

    found_node_shapes = set()
    found_prop_shapes = set()
    for s in subject_shapes:
        if s in defined_node_shapes or s in defined_prop_shapes:
            continue
        path_vals = list(g.objects(s, SH_path))
        if len(path_vals) < 1:
            found_node_shapes.add(s)
        elif len(path_vals) > 1:
            raise ShapeLoadError(
                "An implicit PropertyShape cannot have more than one 'sh:path' predicate.",
                "https://www.w3.org/TR/shacl/#property-shapes")
        else:
            found_prop_shapes.add(s)
            found_prop_shapes_paths[s] = path_vals[0]
    for s in value_of_shapes:
        if s in defined_node_shapes or s in defined_prop_shapes or \
                s in found_prop_shapes or s in found_node_shapes:
            continue
        path_vals = list(g.objects(s, SH_path))
        if len(path_vals) < 1:
            found_node_shapes.add(s)
        elif len(path_vals) > 1:
            raise ShapeLoadError(
                "An implicit PropertyShape cannot have more than one 'sh:path' predicate.",
                "https://www.w3.org/TR/shacl/#property-shapes")
        else:
            found_prop_shapes.add(s)
            found_prop_shapes_paths[s] = path_vals[0]
    created_node_shapes = set()
    for node_shape in defined_node_shapes.union(found_node_shapes):
        s = Shape(g, node_shape, False)
        created_node_shapes.add(s)
    created_prop_shapes = set()
    for prop_shape in defined_prop_shapes.union(found_prop_shapes):
        prop_shape_path = found_prop_shapes_paths[prop_shape]
        s = Shape(g, prop_shape, True, path=prop_shape_path)
        created_prop_shapes.add(s)
    return list(created_node_shapes.union(created_prop_shapes))
