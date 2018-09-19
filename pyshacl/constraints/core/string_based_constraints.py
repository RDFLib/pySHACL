# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-string
"""
import rdflib
import re
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_property, SH_node
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError

SH_PatternConstraintComponent = SH.term('PatternConstraintComponent')
SH_MinLengthConstraintComponent = SH.term('MinLengthConstraintComponent')
SH_MaxLengthConstraintComponent = SH.term('MaxLengthConstraintComponent')
SH_LanguageInConstraintComponent = SH.term('LanguageInConstraintComponent')
SH_UniqueLangConstraintComponent = SH.term('UniqueLangConstraintComponent')
SH_pattern = SH.term('pattern')
SH_flags = SH.term('flags')
SH_minLength = SH.term('minLength')
SH_maxLength = SH.term('maxLength')
SH_languageIn = SH.term('languageIn')
SH_uniqueLang = SH.term('uniqueLang')

class StringBasedConstraintBase(ConstraintComponent):
    """
    https://www.w3.org/TR/shacl/#core-components-string
    """

    def __init__(self, shape):
        super(StringBasedConstraintBase, self).__init__(shape)
        self.string_rules = []
        self.allow_multi_rules = True

    @classmethod
    def constraint_parameters(cls):
        raise NotImplementedError()

    @classmethod
    def constraint_name(cls):
        raise NotImplementedError()

    @classmethod
    def shacl_constraint_class(cls):
        raise NotImplementedError()

    @classmethod
    def value_node_to_string(cls, v):
        if isinstance(v, rdflib.Literal):
            v_string = str(v.value)
        elif isinstance(v, rdflib.URIRef):
            v_string = str(v)
        else:
            v_string = str(v)
        return v_string

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        raise NotImplementedError()

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for r in self.string_rules:
            _nc, _r = self._evaluate_string_rule(r, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
            if not self.allow_multi_rules:
                break
        return (not non_conformant), reports


class MinLengthConstraintComponent(StringBasedConstraintBase):
    """
    sh:minLength specifies the minimum string length of each value node that satisfies the condition. This can be applied to any literals and IRIs, but not to blank nodes.
    Link:
    https://www.w3.org/TR/shacl/#MinLengthConstraintComponent
    Textual Definition:
    For each value node v where the length (as defined by the SPARQL STRLEN function) of the string representation of v (as defined by the SPARQL str function) is less than $minLength, or where v is a blank node, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(MinLengthConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        patterns_found = list(self.shape.objects(SH_minLength))
        if len(patterns_found) < 1:
            raise ConstraintLoadError(
                "MinLengthConstraintComponent must have at least one sh:minLength predicate.",
                "https://www.w3.org/TR/shacl/#MinLengthConstraintComponent")
        elif len(patterns_found) > 1:
            raise ConstraintLoadError(
                "MinLengthConstraintComponent must have at most one sh:minLength predicate.",
                "https://www.w3.org/TR/shacl/#MinLengthConstraintComponent")
        self.string_rules = patterns_found

    @classmethod
    def constraint_parameters(cls):
        return [SH_minLength]

    @classmethod
    def constraint_name(cls):
        return "MinLengthConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MinLengthConstraintComponent

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(r, rdflib.Literal)
        min_len = int(r.value)
        if min_len < 0:
            raise ReportableRuntimeError("Minimum length cannot be less than zero!")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if min_len == 0:
                    flag = True  # min len zero always passes
                elif isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass minLen validation
                    pass
                else:
                    v_string = self.value_node_to_string(v)
                    flag = len(v_string) >= min_len
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class MaxLengthConstraintComponent(StringBasedConstraintBase):
    """
    sh:maxLength specifies the maximum string length of each value node that satisfies the condition. This can be applied to any literals and IRIs, but not to blank nodes.
    Link:
    https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent
    Textual Definition:
    For each value node v where the length (as defined by the SPARQL STRLEN function) of the string representation of v (as defined by the SPARQL str function) is greater than $maxLength, or where v is a blank node, there is a validation result with v as sh:value.
    """

    def __init__(self, shape):
        super(MaxLengthConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        patterns_found = list(self.shape.objects(SH_maxLength))
        if len(patterns_found) < 1:
            raise ConstraintLoadError(
                "MaxLengthConstraintComponent must have at least one sh:maxLength predicate.",
                "https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent")
        elif len(patterns_found) > 1:
            raise ConstraintLoadError(
                "MaxLengthConstraintComponent must have at most one sh:maxLength predicate.",
                "https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent")
        self.string_rules = patterns_found

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxLength]

    @classmethod
    def constraint_name(cls):
        return "MaxLengthConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_MaxLengthConstraintComponent

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(r, rdflib.Literal)
        max_len = int(r.value)
        if max_len < 0:
            raise ReportableRuntimeError("Maximum length cannot be less than zero!")
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass minLen validation
                    pass
                else:
                    v_string = self.value_node_to_string(v)
                    flag = len(v_string) <= max_len
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class PatternConstraintComponent(StringBasedConstraintBase):
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
        self.string_rules = patterns_found
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

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(r, rdflib.Literal)
        re_flags = 0
        if self.flags:
            flags = str(self.flags.value).lower()
            case_insensitive = 'i' in flags
            if case_insensitive:
                re_flags |= re.I
            m = 'm' in flags
            if m:
                re_flags |= re.M
        re_pattern = str(r.value)
        re_matcher = re.compile(re_pattern, re_flags)
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                match = False
                if isinstance(v, rdflib.BNode):
                    # blank nodes cannot pass pattern validation
                    pass
                else:
                    v_string = self.value_node_to_string(v)
                    match = re_matcher.match(v_string)
                    if not match:
                        match = re_matcher.search(v_string)
                if not match:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class LanguageInConstraintComponent(StringBasedConstraintBase):
    """
    The condition specified by sh:languageIn is that the allowed language tags for each value node are limited by a given list of language tags.
    Link:
    https://www.w3.org/TR/shacl/#LanguageInConstraintComponent
    Textual Definition:
    For each value node that is either not a literal or that does not have a language tag matching any of the basic language ranges that are the members of $languageIn following the filtering schema defined by the SPARQL langMatches function, there is a validation result with the value node as sh:value.
    """

    def __init__(self, shape):
        super(LanguageInConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        language_ins_found = list(self.shape.objects(SH_languageIn))
        if len(language_ins_found) < 1:
            raise ConstraintLoadError(
                "LanguageInConstraintComponent must have at least one sh:languageIn predicate.",
                "https://www.w3.org/TR/shacl/#LanguageInConstraintComponent")
        elif len(language_ins_found) > 1:
            raise ConstraintLoadError(
                "LanguageInConstraintComponent must have at most one sh:languageIn predicate.",
                "https://www.w3.org/TR/shacl/#LanguageInConstraintComponent")
        self.string_rules = language_ins_found

    @classmethod
    def constraint_parameters(cls):
        return [SH_languageIn]

    @classmethod
    def constraint_name(cls):
        return "LanguageInConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_LanguageInConstraintComponent

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        languages_need = set()
        sg = self.shape.sg.graph
        try:
            for l in iter(sg.items(r)):
                try:
                    assert isinstance(l, rdflib.Literal)
                    assert isinstance(l.value, str)
                except (AssertionError, AttributeError):
                    raise ReportableRuntimeError(
                        "All languages in sh:LanugageIn must be a Literal "
                        "with type xsd:string")
                languages_need.add(str(l.value).lower())
        except (KeyError, AttributeError, ValueError):
            raise ReportableRuntimeError("Value of sh:LanguageIn must be a RDF List")
        wildcard = False
        if '*' in languages_need:
            wildcard = True
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                flag = False
                if isinstance(v, rdflib.Literal):
                    lang = v.language
                    if lang:
                        if wildcard:
                            flag = True
                        elif str(lang).lower() in languages_need:
                            flag = True
                        else:
                            lang_parts = str(lang).split('-')
                            first_part = lang_parts[0]
                            if str(first_part).lower() in languages_need:
                                flag = True
                if not flag:
                    non_conformant = True
                    rept = self.make_v_result(f, value_node=v)
                    reports.append(rept)
        return non_conformant, reports


class UniqueLangConstraintComponent(StringBasedConstraintBase):
    """
    The property sh:uniqueLang can be set to true to specify that no pair of value nodes may use the same language tag.
    Link:
    https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent
    Textual Definition:
    If $uniqueLang is true then for each non-empty language tag that is used by at least two value nodes, there is a validation result.
    """

    def __init__(self, shape):
        super(UniqueLangConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        is_unique_lang = set(self.shape.objects(SH_uniqueLang))
        if len(is_unique_lang) < 1:
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent must have at least one sh:uniqueLang predicate.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent")
        elif len(is_unique_lang) > 1:
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent must have at most one sh:uniqueLang predicate.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent")
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent")
        is_unique_lang = next(iter(is_unique_lang))
        try:
            assert isinstance(is_unique_lang, rdflib.Literal)
            assert isinstance(is_unique_lang.value, bool)
        except (AssertionError, AttributeError):
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent must have an RDF Literal of type boolean as its sh:uniqueLang.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent")
        self.string_rules = {is_unique_lang.value}

    @classmethod
    def constraint_parameters(cls):
        return [SH_uniqueLang]

    @classmethod
    def constraint_name(cls):
        return "UniqueLangConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_UniqueLangConstraintComponent

    def _evaluate_string_rule(self, is_unique_lang, target_graph, f_v_dict):
        if not is_unique_lang:
            # why even have the constraint if it is set to false?
            return False, []
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            found_langs = set()
            found_duplicates = set()
            for v in value_nodes:
                if isinstance(v, rdflib.Literal):
                    lang = v.language
                    if lang:
                        low_lang = str(lang).lower()
                        if low_lang in found_langs:
                            found_duplicates.add(low_lang)
                        found_langs.add(low_lang)
                        # TODO: determine if there is duplicate matching on parts of multi-part langs.
                        # lang_parts = str(lang).split('-')
                        # first_part = lang_parts[0]
                        # if str(first_part).lower() in languages_need:
                        #     flag = True
            for d in iter(found_duplicates):
                non_conformant = True
                rept = self.make_v_result(f)
                reports.append(rept)
        return non_conformant, reports
