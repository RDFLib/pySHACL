# -*- coding: utf-8 -*-
import rdflib
import logging

from pyshacl.constraints.core.logical_constraints import SH_not, SH_and, SH_or, SH_xone
from pyshacl.constraints.core.shape_based_constraints import SH_qualifiedValueShape
from pyshacl.constraints.sparql.sparql_based_constraint_components import SH_ConstraintComponent, SH_parameter, \
    SH_optional, SPARQLConstraintComponent
from pyshacl.consts import RDF_type, SH_path, SH_NodeShape, SH_PropertyShape, SH_targetClass, SH_targetNode, \
    SH_targetObjectsOf, SH_targetSubjectsOf, SH_property, SH_node, RDFS_subClassOf
from pyshacl.errors import ShapeLoadError, ConstraintLoadError
from pyshacl.shape import Shape


class SHACLGraph(object):
    def __init__(self, graph, logger=None):
        """

        :param graph:
        :type graph: rdflib.Graph
        """
        assert isinstance(graph, rdflib.Graph)
        self.graph = graph
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self._shapes = None
        self._custom_constraints = None

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
            optional_params = []
            mandatory_params = []
            param_nodes = set(g.objects(c, SH_parameter))
            if len(param_nodes) < 1:
                raise ConstraintLoadError(
                    "A sh:ConstraintComponent must have at least one value for sh:parameter",
                    "https://www.w3.org/TR/shacl/#constraint-components-parameters")
            for p in iter(param_nodes):
                path_nodes = set(g.objects(p, SH_path))
                if len(path_nodes) < 1:
                    raise ConstraintLoadError(
                        "A sh:ConstraintComponent parameter value must have at least one value for sh:path",
                        "https://www.w3.org/TR/shacl/#constraint-components-parameters")
                elif len(path_nodes) > 1:
                    raise ConstraintLoadError(
                        "A sh:ConstraintComponent parameter value must have at most one value for sh:path",
                        "https://www.w3.org/TR/shacl/#constraint-components-parameters")
                path = next(iter(path_nodes))
                is_optional = False
                optional = set(g.objects(p, SH_optional))
                for o in iter(optional):
                    if not (isinstance(o, rdflib.Literal) and isinstance(o.value, bool)):
                        raise ConstraintLoadError(
                            "A sh:Parameter value for sh:optional must be a valid RDF Literal of type xsd:boolean.",
                            "https://www.w3.org/TR/shacl/#constraint-components-parameters")
                    is_optional = o.value
                parameter = Shape(self, p=True, node=p, path=path, logger=self.logger)
                if is_optional:
                    optional_params.append(parameter)
                else:
                    mandatory_params.append(parameter)
            if len(mandatory_params) < 1:
                raise ConstraintLoadError(
                    "A sh:ConstraintComponent must have at least one non-optional parameter.",
                    "https://www.w3.org/TR/shacl/#constraint-components-parameters")
            component = SPARQLConstraintComponent(self, c, mandatory_params, optional_params)
            components.add(component)
        return components

    @property
    def shapes(self):
        """

        :returns: [Shape]
        :rtype: list(pyshacl.shape.Shape)
        """
        if self._shapes is None:
            self._shapes = self._find_shapes()
        return self._shapes

    """
    A shape is an IRI or blank node s that fulfills at least one of the following conditions in the shapes graph:

        s is a SHACL instance of sh:NodeShape or sh:PropertyShape.
        s is subject of a triple that has sh:targetClass, sh:targetNode, sh:targetObjectsOf or sh:targetSubjectsOf as predicate.
        s is subject of a triple that has a parameter as predicate.
        s is a value of a shape-expecting, non-list-taking parameter such as sh:node, or a member of a SHACL list that is a value of a shape-expecting and list-taking parameter such as sh:or.
    """

    def _find_shapes(self):
        """
        :returns: [Shape]
        :rtype: list(pyshacl.shape.Shape)
        """
        g = self.graph
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
        subject_shapes = set(has_target_class).union(
            set(has_target_node).union(
                set(has_target_objects_of).union(
                    set(has_target_subjects_of))))

        value_of_property = {o for s, o in g.subject_objects(SH_property)}
        value_of_node = {o for s, o in g.subject_objects(SH_node)}
        value_of_not = {o for s, o in g.subject_objects(SH_not)}
        value_of_qvs = {o for s, o in g.subject_objects(SH_qualifiedValueShape)}
        value_of_shape_expecting = set(value_of_property).union(
            set(value_of_node).union(
                set(value_of_not).union(
                    set(value_of_qvs))))

        value_of_and = {o for s, o in g.subject_objects(SH_and)}
        value_of_or = {o for s, o in g.subject_objects(SH_or)}
        value_of_xone = {o for s, o in g.subject_objects(SH_xone)}
        value_of_s_list_expecting = set(value_of_and).union(
            set(value_of_or).union(
                set(value_of_xone)))

        for l in value_of_s_list_expecting:
            list_contents = set(g.items(l))
            if len(list_contents) < 1:
                raise ShapeLoadError(
                    "A Shape-Expecting & List-Expecting predicate should get a well-formed RDF list with 1 or more members.",
                    "https://www.w3.org/TR/shacl/#shapes-recursion")
            for s in list_contents:
                value_of_shape_expecting.add(s)

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
        for s in value_of_shape_expecting:
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
            s = Shape(self, node_shape, False, logger=self.logger)
            created_node_shapes.add(s)
        created_prop_shapes = set()
        for prop_shape in defined_prop_shapes.union(found_prop_shapes):
            prop_shape_path = found_prop_shapes_paths[prop_shape]
            s = Shape(self, prop_shape, True, path=prop_shape_path, logger=self.logger)
            created_prop_shapes.add(s)
        return list(created_node_shapes.union(created_prop_shapes))

