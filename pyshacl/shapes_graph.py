# -*- coding: utf-8 -*-
import logging
import warnings
from typing import TYPE_CHECKING, Dict, Optional, Union

import rdflib

from .constraints.constraint_component import CustomConstraintComponentFactory
from .constraints.core.logical_constraints import SH_and, SH_not, SH_or, SH_xone
from .constraints.core.shape_based_constraints import SH_qualifiedValueShape
from .consts import (
    SH,
    OWL_Class,
    OWL_DatatypeProperty,
    RDF_Property,
    RDF_type,
    RDFS_Class,
    RDFS_subClassOf,
    SH_ConstraintComponent,
    SH_node,
    SH_NodeShape,
    SH_path,
    SH_property,
    SH_PropertyShape,
    SH_targetClass,
    SH_targetNode,
    SH_targetObjectsOf,
    SH_targetSubjectsOf,
)
from .errors import ShapeLoadError
from .shape import Shape

if TYPE_CHECKING:
    from .pytypes import RDFNode


class ShapesGraph(object):
    system_triples = [(OWL_Class, RDFS_subClassOf, RDFS_Class), (OWL_DatatypeProperty, RDFS_subClassOf, RDF_Property)]

    def __init__(self, graph, debug: Optional[Union[bool, int]] = False, logger: Optional[logging.Logger] = None):
        """
        ShapesGraph
        :param graph:
        :type graph: rdflib.Graph
        :param debug:
        :type debug: bool|int|None
        :param logger:
        :type logger: logging.Logger|None
        """
        assert isinstance(graph, (rdflib.Dataset, rdflib.ConjunctiveGraph, rdflib.Graph))
        self.graph = graph
        if isinstance(self.graph, rdflib.Dataset):
            self.graph.default_union = True
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self.debug = debug
        self._node_shape_cache: Dict['RDFNode', Shape] = {}
        self._shapes = None
        self._custom_constraints = None
        self._shacl_functions: Dict[str, tuple] = {}
        self._shacl_target_types: Dict[str, 'RDFNode'] = {}
        self._use_js = False
        self._add_system_triples()

    def enable_js(self):
        self._use_js = True

    @property
    def js_enabled(self):
        return bool(self._use_js)

    def _add_system_triples(self):
        if isinstance(self.graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            g = next(iter(self.graph.contexts()))
        else:
            g = self.graph
        for t in self.system_triples:
            g.add(t)

    def subjects(self, p, o):
        return self.graph.subjects(p, o)

    def predicates(self, s, o):
        return self.graph.predicates(s, o)

    def objects(self, s, p):
        return self.graph.objects(s, p)

    def subject_objects(self, p):
        return self.graph.subject_objects(p)

    def subject_predicates(self, o):
        return self.graph.subject_predicates(o)

    def predicate_objects(self, s):
        return self.graph.predicate_objects(s)

    @property
    def custom_constraints(self):
        if self._custom_constraints is None:
            self._custom_constraints = self._find_custom_constraints()
        return self._custom_constraints

    def _find_custom_constraints(self):
        g = self.graph
        constraint_component_set = set(g.subjects(RDF_type, SH_ConstraintComponent))
        constraint_subclasses = set(g.subjects(RDFS_subClassOf, SH_ConstraintComponent))
        for sc in iter(constraint_subclasses):
            subclass_components = set(g.subjects(RDF_type, sc))
            constraint_component_set.update(subclass_components)
        components = set()
        for c in iter(constraint_component_set):
            if c.startswith(SH):
                # ignore all constraint components from shacl.ttl, these are all hardcoded into PySHACL
                continue
            components.add(CustomConstraintComponentFactory(self, c))
        return components

    def add_shacl_function(self, uri: Union[str, 'RDFNode'], function, optionals):
        uri_str = str(uri)
        if uri_str in self._shacl_functions:
            warnings.warn(Warning("SHACLFunction {} is already registered.".format(uri)))
        else:
            self._shacl_functions[uri_str] = (function, optionals)

    def get_shacl_function(self, uri: Union[str, 'RDFNode']):
        uri_str = str(uri)
        try:
            f = self._shacl_functions[uri_str]
        except LookupError:
            raise KeyError("SHACLFunction {} not found.".format(uri))
        return f

    def remove_shacl_function(self, uri, function):
        uri = str(uri)
        try:
            f, _ = self.get_shacl_function(uri)
            if f != function:
                warnings.warn(
                    Warning("Cannot remove a different function than what was registered for {}.".format(uri))
                )
                return
        except KeyError:
            return  # Not registered
        del self._shacl_functions[uri]

    def add_shacl_target_type(self, uri: Union[str, 'RDFNode'], tt):
        uri_str = str(uri)
        if uri_str in self._shacl_target_types:
            warnings.warn(Warning("SHACL TargetType {} is already registered.".format(uri)))
        else:
            self._shacl_target_types[uri_str] = tt

    def get_shacl_target_type(self, uri: Union[str, 'RDFNode']):
        uri_str = str(uri)
        try:
            tt = self._shacl_target_types[uri_str]
        except LookupError:
            raise KeyError("SHACL TargetType {} not found.".format(uri))
        return tt

    @property
    def shapes(self):
        """

        :returns: [Shape]
        :rtype: list(pyshacl.shape.Shape)
        """
        if len(self._node_shape_cache) < 1:
            self._build_node_shape_cache()
        return self._node_shape_cache.values()

    def lookup_shape_from_node(self, node) -> Shape:
        # This will throw a KeyError if it is not found. This is intentionally not caught here.
        return self._node_shape_cache[node]

    """
    A shape is an IRI or blank node s that fulfills at least one of the following conditions in the shapes graph:

        s is a SHACL instance of sh:NodeShape or sh:PropertyShape.
        s is subject of a triple that has sh:targetClass, sh:targetNode, sh:targetObjectsOf or sh:targetSubjectsOf as predicate.
        s is subject of a triple that has a parameter as predicate.
        s is a value of a shape-expecting, non-list-taking parameter such as sh:node, or a member of a SHACL list that is a value of a shape-expecting and list-taking parameter such as sh:or.
    """

    def _build_node_shape_cache(self):
        """
        :returns: None
        :rtype: NoneType
        """
        g = self.graph
        defined_node_shapes = set(g.subjects(RDF_type, SH_NodeShape))
        if self.debug:
            self.logger.debug(f"Found {len(defined_node_shapes)} SHACL Shapes defined with type sh:NodeShape.")
        for s in defined_node_shapes:
            path_vals = list(g.objects(s, SH_path))
            if len(path_vals) > 0:
                # TODO:coverage: we don't have any tests for invalid shapes
                raise ShapeLoadError(
                    "A shape defined as a NodeShape cannot be the subject of a 'sh:path' predicate.",
                    "https://www.w3.org/TR/shacl/#node-shapes",
                )
        defined_prop_shapes = set(g.subjects(RDF_type, SH_PropertyShape))
        if self.debug:
            self.logger.debug(f"Found {len(defined_prop_shapes)} SHACL Shapes defined with type sh:PropertyShape.")
        found_prop_shapes_paths = dict()
        for s in defined_prop_shapes:
            if s in defined_node_shapes:
                # TODO:coverage: we don't have any tests for invalid shapes
                raise ShapeLoadError(
                    "A shape defined as a NodeShape cannot also be defined as a PropertyShape.",
                    "https://www.w3.org/TR/shacl/#node-shapes",
                )
            path_vals = list(g.objects(s, SH_path))
            if len(path_vals) < 1:
                # TODO:coverage: we don't have any tests for invalid shapes
                raise ShapeLoadError(
                    "A shape defined as a PropertyShape must include one `sh:path` property.",
                    "https://www.w3.org/TR/shacl/#property-shapes",
                )
            elif len(path_vals) > 1:
                # TODO:coverage: we don't have any tests for invalid shapes
                raise ShapeLoadError(
                    "A shape defined as a PropertyShape cannot have more than one 'sh:path' property.",
                    "https://www.w3.org/TR/shacl/#property-shapes",
                )
            found_prop_shapes_paths[s] = path_vals[0]
        if self.debug:
            self.logger.debug(f"Found {len(found_prop_shapes_paths)} property paths to follow.")
        has_target_class = {s for s, o in g.subject_objects(SH_targetClass)}
        has_target_node = {s for s, o in g.subject_objects(SH_targetNode)}
        has_target_objects_of = {s for s, o in g.subject_objects(SH_targetObjectsOf)}
        has_target_subjects_of = {s for s, o in g.subject_objects(SH_targetSubjectsOf)}
        subject_shapes = set(has_target_class).union(
            set(has_target_node).union(set(has_target_objects_of).union(set(has_target_subjects_of)))
        )
        # implicit shapes: their subjects must be shapes
        subject_of_property = {s for s, o in g.subject_objects(SH_property)}
        subject_of_node = {s for s, o in g.subject_objects(SH_node)}
        subject_shapes = subject_shapes.union(set(subject_of_property).union(set(subject_of_node)))
        if self.debug:
            self.logger.debug(f"Found {len(subject_shapes)} implied SHACL Shapes based on their properties.")

        # shape-expecting properties, their values must be shapes.
        value_of_property = {o for s, o in g.subject_objects(SH_property)}
        value_of_node = {o for s, o in g.subject_objects(SH_node)}
        value_of_not = {o for s, o in g.subject_objects(SH_not)}
        value_of_qvs = {o for s, o in g.subject_objects(SH_qualifiedValueShape)}
        value_of_shape_expecting = set(value_of_property).union(
            set(value_of_node).union(set(value_of_not).union(set(value_of_qvs)))
        )

        value_of_and = {o for s, o in g.subject_objects(SH_and)}
        value_of_or = {o for s, o in g.subject_objects(SH_or)}
        value_of_xone = {o for s, o in g.subject_objects(SH_xone)}
        value_of_s_list_expecting = set(value_of_and).union(set(value_of_or).union(set(value_of_xone)))

        for lst in value_of_s_list_expecting:
            list_contents = set(g.items(lst))
            if len(list_contents) < 1:
                # TODO:coverage: we don't have any tests for invalid shape lists
                raise ShapeLoadError(
                    "A Shape-Expecting & List-Expecting predicate should get a well-formed RDF list with 1 or more members.",
                    "https://www.w3.org/TR/shacl/#shapes-recursion",
                )
            for s in list_contents:
                value_of_shape_expecting.add(s)

        if self.debug:
            self.logger.debug(
                f"Found {len(value_of_shape_expecting)} implied SHACL Shapes used as values in shape-expecting constraints."
            )
        found_node_shapes = set()
        found_prop_shapes = set()
        for s in subject_shapes:
            if s in defined_node_shapes or s in defined_prop_shapes:
                continue
            path_vals = list(g.objects(s, SH_path))
            if len(path_vals) < 1:
                found_node_shapes.add(s)
            elif len(path_vals) > 1:
                # TODO:coverage: we don't have any tests for invalid implicit shapes
                raise ShapeLoadError(
                    "An implicit PropertyShape cannot have more than one 'sh:path' predicate.",
                    "https://www.w3.org/TR/shacl/#property-shapes",
                )
            else:
                # TODO:coverage: we don't have this case where an implicit shape is a property shape.
                found_prop_shapes.add(s)
                found_prop_shapes_paths[s] = path_vals[0]
        for s in value_of_shape_expecting:
            if (
                s in defined_node_shapes
                or s in defined_prop_shapes
                or s in found_prop_shapes
                or s in found_node_shapes
            ):
                continue
            path_vals = list(g.objects(s, SH_path))
            if len(path_vals) < 1:
                found_node_shapes.add(s)
            elif len(path_vals) > 1:
                # TODO:coverage: we don't have any tests for invalid implicit shapes
                raise ShapeLoadError(
                    "An implicit PropertyShape cannot have more than one 'sh:path' predicate.",
                    "https://www.w3.org/TR/shacl/#property-shapes",
                )
            else:
                found_prop_shapes.add(s)
                found_prop_shapes_paths[s] = path_vals[0]
        node_shape_count = 0
        property_shape_count = 0
        for node_shape in defined_node_shapes.union(found_node_shapes):
            if node_shape in self._node_shape_cache:
                # TODO:coverage: we don't have any tests where a shape is loaded twice
                raise ShapeLoadError("That shape has already been loaded!", "None")
            s = Shape(self, node_shape, p=False, logger=self.logger)
            self._node_shape_cache[node_shape] = s
            node_shape_count += 1
        for prop_shape in defined_prop_shapes.union(found_prop_shapes):
            if prop_shape in self._node_shape_cache:
                # TODO:coverage: we don't have any tests where a shape is loaded twice
                raise ShapeLoadError("That shape has already been loaded!", "None")
            prop_shape_path = found_prop_shapes_paths[prop_shape]
            s = Shape(self, prop_shape, p=True, path=prop_shape_path, logger=self.logger)
            self._node_shape_cache[prop_shape] = s
            property_shape_count += 1
        if self.debug:
            self.logger.debug(
                f"Cached {node_shape_count} unique NodeShapes and {property_shape_count} unique PropertyShapes."
            )
