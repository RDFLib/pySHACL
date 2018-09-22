# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-others
"""
import rdflib
from rdflib.namespace import RDF, RDFS
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import RDF_type, SH, SH_property, SH_path
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError

SH_InConstraintComponent = SH.term('InConstraintComponent')
SH_ClosedConstraintComponent = SH.term('ClosedConstraintComponent')
SH_HasValueConstraintComponent = SH.term('HasValueConstraintComponent')
SH_in = SH.term('in')
SH_closed = SH.term('closed')
SH_ignoredProperties = SH.term('ignoredProperties')
SH_hasValue = SH.term('hasValue')


class InConstraintComponent(ConstraintComponent):
    """

    Link:
    https://www.w3.org/TR/shacl/#InConstraintComponent
    Textual Definition:
    For each value node v where the SPARQL expression $minExclusive < v does not return true, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(InConstraintComponent, self).__init__(shape)
        in_vals = list(self.shape.objects(SH_in))
        if len(in_vals) < 1:
            raise ConstraintLoadError(
                "InConstraintComponent must have at least one sh:in predicate.",
                "https://www.w3.org/TR/shacl/#InConstraintComponent")
        elif len(in_vals) > 1:
            raise ConstraintLoadError(
                "InConstraintComponent must have at most one sh:in predicate.",
                "https://www.w3.org/TR/shacl/#InConstraintComponent")
        self.in_list = in_vals[0]

    @classmethod
    def constraint_parameters(cls):
        return [SH_in]

    @classmethod
    def constraint_name(cls):
        return "InConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_InConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False
        sg = self.shape.sg.graph
        in_vals = set(sg.items(self.in_list))
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                if v not in in_vals:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return (not non_conformant), reports


class ClosedConstraintComponent(ConstraintComponent):
    """
    The RDF data model offers a huge amount of flexibility. Any node can in principle have values for any property. However, in some cases it makes sense to specify conditions on which properties can be applied to nodes. The SHACL Core language includes a property called sh:closed that can be used to specify the condition that each value node has values only for those properties that have been explicitly enumerated via the property shapes specified for the shape via sh:property.
    Link:
    https://www.w3.org/TR/shacl/#InConstraintComponent
    Textual Definition:
    If $closed is true then there is a validation result for each triple that has a value node as its subject and a predicate that is not explicitly enumerated as a value of sh:path in any of the property shapes declared via sh:property at the current shape. If $ignoredProperties has a value then the properties enumerated as members of this SHACL list are also permitted for the value node. The validation result MUST have the predicate of the triple as its sh:resultPath, and the object of the triple as its sh:value.
    """
    ALWAYS_IGNORE = {(RDF_type, RDFS.term('Resource'))}


    def __init__(self, shape):
        super(ClosedConstraintComponent, self).__init__(shape)
        sg = self.shape.sg.graph
        closed_vals = list(self.shape.objects(SH_closed))
        if len(closed_vals) < 1:
            raise ConstraintLoadError(
                "ClosedConstraintComponent must have at least one sh:closed predicate.",
                "https://www.w3.org/TR/shacl/#ClosedConstraintComponent")
        elif len(closed_vals) > 1:
            raise ConstraintLoadError(
                "ClosedConstraintComponent must have at most one sh:closed predicate.",
                "https://www.w3.org/TR/shacl/#ClosedConstraintComponent")
        assert isinstance(closed_vals[0], rdflib.Literal), "sh:closed must take a xsd:boolean literal."
        self.is_closed = bool(closed_vals[0].value)
        ignored_vals = list(self.shape.objects(SH_ignoredProperties))
        self.ignored_props = set()
        for i in ignored_vals:
            try:
                items = set(sg.items(i))
                for list_item in items:
                    self.ignored_props.add(list_item)
            except ValueError:
                continue
        self.property_shapes = list(self.shape.objects(SH_property))



    @classmethod
    def constraint_parameters(cls):
        return [SH_closed, SH_ignoredProperties]

    @classmethod
    def constraint_name(cls):
        return "ClosedConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_ClosedConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False
        if not self.is_closed:
            return True, []

        working_shapes = set()
        for p_shape in self.property_shapes:
            property_shape = self.shape.get_other_shape(p_shape)
            if not property_shape or not property_shape.is_property_shape:
                raise ReportableRuntimeError(
                    "The shape pointed to by sh:property does "
                    "not exist, or is not a well defined SHACL PropertyShape.")
            working_shapes.add(property_shape)
        working_paths = set()
        for w in working_shapes:
            p = w.path()
            if p:
                working_paths.add(p)

        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                pred_obs = self.shape.sg.predicate_objects(v)
                for p, o in pred_obs:
                    if (p, o) in self.ALWAYS_IGNORE:
                        continue
                    elif p in self.ignored_props:
                        continue
                    elif p in working_paths:
                        continue
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=o, result_path=p)
                    reports.append(rept)
        return (not non_conformant), reports


class HasValueConstraintComponent(ConstraintComponent):
    """
    sh:equals specifies the condition that the set of all value nodes is equal to the set of objects of the triples that have the focus node as subject and the value of sh:equals as predicate.
    Link:
    https://www.w3.org/TR/shacl/#HasValueConstraintComponent
    Textual Definition:
    For each value node that does not exist as a value of the property $equals at the focus node, there is a validation result with the value node as sh:value. For each value of the property $equals at the focus node that is not one of the value nodes, there is a validation result with the value as sh:value.
    """

    def __init__(self, shape):
        super(HasValueConstraintComponent, self).__init__(shape)
        has_value_set = set(self.shape.objects(SH_hasValue))
        if len(has_value_set) < 1:
            raise ConstraintLoadError(
                "HasValueConstraintComponent must have at least one sh:hasValue predicate.",
                "https://www.w3.org/TR/shacl/#HasValueConstraintComponent")
        self.has_value_set = has_value_set


    @classmethod
    def constraint_parameters(cls):
        return [SH_hasValue]

    @classmethod
    def constraint_name(cls):
        return "HasValueConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_HasValueConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for hv in iter(self.has_value_set):
            _nc, _r = self._evaluate_has_value(hv, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_has_value(self, hv, f_v_dict):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            conformant = False
            for v_node in value_nodes:
                if v_node == hv:
                    conformant = True
                    break
            if not conformant:
                non_conformant = True
                # Note, including the value here causes this constraint to not pass SHT validation
                # if len(value_nodes) == 1:
                #     a_value_node = next(iter(value_nodes))
                #     rept = self.make_v_result(f, value_node=a_value_node)
                # else:
                if not self.shape.is_property_shape:
                    rept = self.make_v_result(f, value_node=f)
                else:
                    rept = self.make_v_result(f, value_node=None)
                reports.append(rept)
        return non_conformant, reports
