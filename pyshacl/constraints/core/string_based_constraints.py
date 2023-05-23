# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#core-components-string
"""
import re
from typing import Dict, List

import rdflib
from rdflib.namespace import XSD

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import RDF, SH, XSD_WHOLE_INTEGERS
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node

RDF_langString = RDF.langString
XSD_string = XSD.string

SH_PatternConstraintComponent = SH.PatternConstraintComponent
SH_MinLengthConstraintComponent = SH.MinLengthConstraintComponent
SH_MaxLengthConstraintComponent = SH.MaxLengthConstraintComponent
SH_LanguageInConstraintComponent = SH.LanguageInConstraintComponent
SH_UniqueLangConstraintComponent = SH.UniqueLangConstraintComponent
SH_pattern = SH.pattern
SH_flags = SH.flags
SH_minLength = SH.minLength
SH_maxLength = SH.maxLength
SH_languageIn = SH.languageIn
SH_uniqueLang = SH.uniqueLang


class StringBasedConstraintBase(ConstraintComponent):
    """
    https://www.w3.org/TR/shacl/#core-components-string
    """

    shacl_constraint_component = rdflib.URIRef("urn:notimplemented")

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
    def value_node_to_string(cls, v):
        if isinstance(v, rdflib.Literal):
            if v.value is not None and (v.datatype in (None, RDF_langString, XSD_string)):
                v_string = str(v.value)
            else:
                v_string = str(v)
        elif isinstance(v, rdflib.URIRef):
            v_string = str(v)
        else:
            v_string = str(v)
        return v_string

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        raise NotImplementedError()

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type target_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
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

    shacl_constraint_component = SH_MinLengthConstraintComponent

    def __init__(self, shape):
        super(MinLengthConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        patterns_found = list(self.shape.objects(SH_minLength))
        if len(patterns_found) < 1:
            raise ConstraintLoadError(
                "MinLengthConstraintComponent must have at least one sh:minLength predicate.",
                "https://www.w3.org/TR/shacl/#MinLengthConstraintComponent",
            )
        elif len(patterns_found) > 1:
            raise ConstraintLoadError(
                "MinLengthConstraintComponent must have at most one sh:minLength predicate.",
                "https://www.w3.org/TR/shacl/#MinLengthConstraintComponent",
            )
        for s_r in patterns_found:
            if (
                (not isinstance(s_r, rdflib.Literal))
                or getattr(s_r, "ill_typed", False)
                or s_r.datatype is None
                or s_r.datatype not in XSD_WHOLE_INTEGERS
            ):
                raise ConstraintLoadError(
                    "sh:minLength value must be a literal value with an integer.",
                    "https://www.w3.org/TR/shacl/#MinLengthConstraintComponent",
                )
            elif s_r.datatype in (XSD.negativeInteger, XSD.nonPositiveInteger) or s_r.value < 0:
                raise ConstraintLoadError(
                    "sh:minLength value must be a positive integer.",
                    "https://www.w3.org/TR/shacl/#MinLengthConstraintComponent",
                )

        self.string_rules = patterns_found

    @classmethod
    def constraint_parameters(cls):
        return [SH_minLength]

    @classmethod
    def constraint_name(cls):
        return "MinLengthConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        m = "String length not >= {}".format(stringify_node(datagraph, self.string_rules[0]))
        return [rdflib.Literal(m)]

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(r, rdflib.Literal)
        min_len = r.value
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
                    rept = self.make_v_result(target_graph, f, value_node=v)
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

    shacl_constraint_component = SH_MaxLengthConstraintComponent

    def __init__(self, shape):
        super(MaxLengthConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        patterns_found = list(self.shape.objects(SH_maxLength))
        if len(patterns_found) < 1:
            raise ConstraintLoadError(
                "MaxLengthConstraintComponent must have at least one sh:maxLength predicate.",
                "https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent",
            )
        elif len(patterns_found) > 1:
            raise ConstraintLoadError(
                "MaxLengthConstraintComponent must have at most one sh:maxLength predicate.",
                "https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent",
            )
        for s_r in patterns_found:
            if (
                (not isinstance(s_r, rdflib.Literal))
                or getattr(s_r, "ill_typed", False)
                or s_r.datatype is None
                or s_r.datatype not in XSD_WHOLE_INTEGERS
            ):
                raise ConstraintLoadError(
                    "sh:maxLength value must be a literal value with an integer.",
                    "https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent",
                )
            elif s_r.datatype in (XSD.negativeInteger, XSD.nonPositiveInteger) or s_r.value < 0:
                raise ConstraintLoadError(
                    "sh:maxLength value must be a positive integer.",
                    "https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent",
                )
        self.string_rules = patterns_found

    @classmethod
    def constraint_parameters(cls):
        return [SH_maxLength]

    @classmethod
    def constraint_name(cls):
        return "MaxLengthConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        m = "String length not <= {}".format(stringify_node(datagraph, self.string_rules[0]))
        return [rdflib.Literal(m)]

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        assert isinstance(r, rdflib.Literal)
        max_len = r.value
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
                    rept = self.make_v_result(target_graph, f, value_node=v)
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

    shacl_constraint_component = SH_PatternConstraintComponent

    def __init__(self, shape):
        super(PatternConstraintComponent, self).__init__(shape)
        patterns_found = list(self.shape.objects(SH_pattern))
        if len(patterns_found) < 1:
            raise ConstraintLoadError(
                "PatternConstraintComponent must have at least one sh:pattern predicate.",
                "https://www.w3.org/TR/shacl/#PatternConstraintComponent",
            )
        for p in patterns_found:
            if not isinstance(p, rdflib.Literal):
                raise ConstraintLoadError(
                    "PatternConstraintComponent sh:pattern must be a RDF Literal node.",
                    "https://www.w3.org/TR/shacl/#PatternConstraintComponent",
                )
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

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        if len(self.string_rules) < 2:
            m = "Value does not match pattern '{}'".format(str(self.string_rules[0].value))
        else:
            rules = "', '".join(str(c.value) for c in self.string_rules)
            m = "Value does not match every pattern in ('{}')".format(rules)
        return [rdflib.Literal(m)]

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
                    rept = self.make_v_result(target_graph, f, value_node=v)
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

    shacl_constraint_component = SH_LanguageInConstraintComponent
    shape_expecting = False
    list_taking = True

    def __init__(self, shape):
        super(LanguageInConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        language_ins_found = list(self.shape.objects(SH_languageIn))
        if len(language_ins_found) < 1:
            raise ConstraintLoadError(
                "LanguageInConstraintComponent must have at least one sh:languageIn predicate.",
                "https://www.w3.org/TR/shacl/#LanguageInConstraintComponent",
            )
        elif len(language_ins_found) > 1:
            raise ConstraintLoadError(
                "LanguageInConstraintComponent must have at most one sh:languageIn predicate.",
                "https://www.w3.org/TR/shacl/#LanguageInConstraintComponent",
            )
        self.string_rules = language_ins_found

    @classmethod
    def constraint_parameters(cls):
        return [SH_languageIn]

    @classmethod
    def constraint_name(cls):
        return "LanguageInConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        m = "String language is not in {}".format(stringify_node(datagraph, self.string_rules[0]))
        return [rdflib.Literal(m)]

    def _evaluate_string_rule(self, r, target_graph, f_v_dict):
        reports = []
        non_conformant = False
        languages_need = set()
        sg = self.shape.sg.graph
        try:
            for lang_in in iter(sg.items(r)):
                try:
                    if not isinstance(lang_in, rdflib.Literal) or not isinstance(lang_in.value, str):
                        raise ReportableRuntimeError(
                            "All languages in sh:LanugageIn must be a Literal with type xsd:string"
                        )
                except (AssertionError, AttributeError):
                    raise ReportableRuntimeError(
                        "All languages in sh:LanugageIn must be a Literal with type xsd:string"
                    )
                languages_need.add(str(lang_in.value).lower())
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
                    rept = self.make_v_result(target_graph, f, value_node=v)
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

    shacl_constraint_component = SH_UniqueLangConstraintComponent

    def __init__(self, shape):
        super(UniqueLangConstraintComponent, self).__init__(shape)
        self.allow_multi_rules = False
        is_unique_lang = set(self.shape.objects(SH_uniqueLang))
        if len(is_unique_lang) < 1:
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent must have at least one sh:uniqueLang predicate.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent",
            )
        elif len(is_unique_lang) > 1:
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent must have at most one sh:uniqueLang predicate.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent",
            )
        if not shape.is_property_shape:
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent can only be present on a PropertyShape, not a NodeShape.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent",
            )
        is_unique_lang = next(iter(is_unique_lang))
        if not isinstance(is_unique_lang, rdflib.Literal) or not isinstance(is_unique_lang.value, bool):
            raise ConstraintLoadError(
                "UniqueLangConstraintComponent must have an RDF Literal of type boolean as its sh:uniqueLang.",
                "https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent",
            )
        self.string_rules = {is_unique_lang.value}

    @classmethod
    def constraint_parameters(cls):
        return [SH_uniqueLang]

    @classmethod
    def constraint_name(cls):
        return "UniqueLangConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[rdflib.Literal]:
        return [rdflib.Literal("More than one String shares the same Language")]

    def _evaluate_string_rule(self, is_unique_lang, target_graph, f_v_dict):
        if not is_unique_lang:
            # why even have the constraint if it is set to false?
            return False, []
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            found_langs = dict()
            found_duplicates = set()
            for v in value_nodes:
                if isinstance(v, rdflib.Literal):
                    lang = v.language
                    if lang:
                        low_lang = str(lang).lower()
                        if low_lang in found_langs:
                            found_duplicates.add(low_lang)
                        else:
                            found_langs[low_lang] = lang
                        # TODO: determine if there is duplicate matching on parts of multi-part langs.
                        #  lang_parts = str(lang).split('-')
                        #  first_part = lang_parts[0]
                        #  if str(first_part).lower() in languages_need:
                        #      flag = True
            for d in iter(found_duplicates):
                non_conformant = True
                # Adding value_node here causes SHT validation to fail.
                # IMHO it should be present
                # rept = self.make_v_result(target_graph, f, value_node=found_langs[d])
                rept = self.make_v_result(target_graph, f, value_node=None)
                reports.append(rept)
        return non_conformant, reports
