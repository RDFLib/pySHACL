# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, RDFS_subClassOf, RDF_type

SH_class = SH.term('class')


class ClassConstraintComponent(ConstraintComponent):
    """
    The condition specified by sh:class is that each value node is a SHACL instance of a given type.
    Definition:
    For each value node that is either a literal, or a non-literal that is not a SHACL instance of $class in the data graph, there is a validation result with the value node as sh:value.
    """

    def __init__(self, shape):
        super(ClassConstraintComponent, self).__init__(shape)
        class_rules = list(self.shape.objects(SH_class))
        if len(class_rules) > 1:
            #TODO: Make a new error type for this
            raise RuntimeError("sh:class must only have one value.")
        self.class_rule = class_rules[0]

    @classmethod
    def constraint_parameters(cls):
        return [SH_class]

    def evaluate(self, target_graph, value_nodes):
        """

        :type value_nodes: list | set
        :type target_graph: rdflib.Graph
        """
        fails = []
        for f in value_nodes:
            t = target_graph.objects(f, RDF_type)
            for ctype in iter(t):
                if ctype == self.class_rule:
                    continue
                subclasses = target_graph.objects(ctype, RDFS_subClassOf)
                if self.class_rule in iter(subclasses):
                    continue
            fails.append(f)
        if len(fails) > 0:
            return False, fails
        return True, None

