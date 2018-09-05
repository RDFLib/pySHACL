# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-string
"""
import rdflib
import re
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_property, SH_node
from pyshacl.errors import ConstraintLoadError

SH_PatternConstraintComponent = SH.term('PatternConstraintComponent')
SH_pattern = SH.term('pattern')
SH_flags = SH.term('flags')


class PatternConstraintComponent(ConstraintComponent):
    """
    sh:property can be used to specify that each value node has a given property shape.
    Link:
    https://www.w3.org/TR/shacl/#PropertyShapeComponent
    Textual Definition:
    For each value node v: A failure MUST be produced if the validation of v as focus node against the property shape $property produces a failure. Otherwise, the validation results are the results of validating v as focus node against the property shape $property.
    """

    def __init__(self, shape):
        super(PatternConstraintComponent, self).__init__(shape)
        patterns_found = list(self.shape.objects(SH_pattern))
        if len(patterns_found) < 1:
            raise ConstraintLoadError(
                "PatternConstraintComponent must have at least one sh:pattern predicate.",
                "https://www.w3.org/TR/shacl/#PatternConstraintComponent")
        self.patterns = patterns_found
        flags_found = set(self.shape.objects(SH_flags))
        if len(flags_found) > 0:
            # Just get the first found flags
            self.flags = next(iter(flags_found))
        else:
            self.flags = None

    @classmethod
    def constraint_parameters(cls):
        return [SH_pattern]

    @classmethod
    def constraint_name(cls):
        return "PatternConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_PatternConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        fails = []
        non_conformant = False

        for pattern in self.patterns:
            _nc, _f = self._evaluate_pattern(pattern, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            fails.extend(_f)
        return (not non_conformant), fails

    def _evaluate_pattern(self, pattern, target_graph, f_v_dict):
        fails = []
        non_conformant = False
        assert isinstance(pattern, rdflib.Literal)
        re_flags = 0
        if self.flags:
            flags = str(self.flags.value).lower()
            case_insensitive = 'i' in flags
            if case_insensitive:
                re_flags |= re.I
            m = 'm' in flags
            if m:
                re_flags |= re.M
        re_pattern = str(pattern.value)
        re_matcher = re.compile(re_pattern, re_flags)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                print(pattern, v)
                if isinstance(v, rdflib.Literal):
                    v_string = str(v.value)
                else:
                    v_string = str(v)
                match = re_matcher.match(v_string)
                if not match:
                    non_conformant = True
                    fail = self.make_failure(f, value_node=v)
                    fails.append(fail)
        return non_conformant, fails

