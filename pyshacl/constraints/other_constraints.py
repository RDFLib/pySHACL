# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-others
"""
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError

SH_InConstraintComponent = SH.term('InConstraintComponent')
SH_in = SH.term('in')


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
        in_vals = set(self.shape.sg.items(self.in_list))
        for f, value_nodes in focus_value_nodes.items():
            for v in value_nodes:
                if v not in in_vals:
                    non_conformant = True
                    rept = self.make_v_report(f, value_node=v)
                    reports.append(rept)
        return (not non_conformant), reports

