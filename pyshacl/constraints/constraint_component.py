# -*- coding: utf-8 -*-
#
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import abc
import re
import typing
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set, Tuple

from rdflib import BNode, Literal, URIRef

from pyshacl.consts import (
    SH,
    RDF_type,
    SH_ask,
    SH_focusNode,
    SH_jsFunctionName,
    SH_NodeConstraintComponent,
    SH_parameter,
    SH_path,
    SH_PropertyConstraintComponent,
    SH_resultMessage,
    SH_resultPath,
    SH_resultSeverity,
    SH_select,
    SH_sourceConstraint,
    SH_sourceConstraintComponent,
    SH_sourceShape,
    SH_ValidationResult,
    SH_value,
    SH_Violation,
)
from pyshacl.errors import ConstraintLoadError
from pyshacl.parameter import SHACLParameter
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import stringify_node

if TYPE_CHECKING:
    from pyshacl.pytypes import RDFNode
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph


class ConstraintComponent(object, metaclass=abc.ABCMeta):
    __slots__ = ('shape',)

    """
    Abstract Constraint Component Class
    All Constraint Components must inherit from this class.
    """

    # True if constraint component is defined as "shape-expecting"
    shape_expecting = False

    # True if constraint component is defined as "list-taking"
    list_taking = False

    shacl_constraint_component: URIRef = URIRef("urn:notimplemented")

    def __init__(self, shape: 'Shape'):
        """

        :param shape:
        :type shape: Shape
        """
        self.shape = shape  # type: Shape

    @classmethod
    @abc.abstractmethod
    def constraint_parameters(cls):
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def constraint_name(cls):
        raise NotImplementedError()  # pragma: no cover

    @abc.abstractmethod
    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        raise NotImplementedError()  # pragma: no cover

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        return []

    def __str__(self):
        c_name = str(self.__class__.__name__)
        shape_id = str(self.shape)
        return "<{} on {}>".format(c_name, shape_id)

    def recursion_triggers(self, _evaluation_path, trigger_depth=3) -> Optional[List['RDFNode']]:
        shape = self.shape
        eval_length = len(_evaluation_path)
        if eval_length < 4:
            return None
        maybe_recursive = []
        _shape, _self = _evaluation_path[eval_length - 2 :]
        if _shape is not shape or _self is not self:
            raise RuntimeError("Bad evaluation path construction")
        prev_shape, prev_constraint = _evaluation_path[eval_length - 4 : eval_length - 2]
        lookback_len = trigger_depth * 2
        if isinstance(prev_constraint, ConstraintComponent):
            if (
                self.shacl_constraint_component is SH_PropertyConstraintComponent
                and prev_constraint.shacl_constraint_component is SH_NodeConstraintComponent
            ) or (
                self.shacl_constraint_component is SH_NodeConstraintComponent
                and prev_constraint.shacl_constraint_component is SH_PropertyConstraintComponent
            ):
                lookback_len = trigger_depth * 4
        if eval_length < lookback_len:
            return None
        seen_before = [i for i, x in enumerate(_evaluation_path[: eval_length - 2]) if x is shape]
        for s in seen_before:
            for i, p in enumerate(_evaluation_path[s + 1 : -2]):
                if isinstance(p, ConstraintComponent):
                    if p.shape is shape and p.__class__ == self.__class__:
                        try:
                            next_shape = _evaluation_path[s + 1 + i + 1]
                            maybe_recursive.append(next_shape)
                        except IndexError:
                            pass
                    break
        return maybe_recursive

    def make_v_result_description(
        self,
        datagraph: GraphLike,
        focus_node: 'RDFNode',
        severity: URIRef,
        value_node: Optional['RDFNode'],
        messages: List[str],
        result_path=None,
        constraint_component=None,
        source_constraint=None,
        extra_messages: Optional[Iterable] = None,
        bound_vars=None,
    ):
        """
        :param datagraph:
        :type datagraph: rdflib.Graph | rdflib.ConjunctiveGraph | rdflib.Dataset
        :param focus_node:
        :type focus_node: RDFNode
        :param severity:
        :type value_node: rdflib.URIRef
        :param value_node:
        :type value_node: rdflib.term.Identifier | None
        :param messages:
        :type messages: List[str]
        :param result_path:
        :param bound_vars:
        :param constraint_component:
        :param source_constraint:
        :param extra_messages:
        :type extra_messages: collections.abc.Iterable | None
        :return:
        """
        sg = self.shape.sg.graph
        constraint_component = constraint_component or self.shacl_constraint_component
        constraint_name = self.constraint_name()
        if severity == SH_Violation:
            severity_desc = "Constraint Violation"
        else:
            severity_desc = "Validation Result"
        source_shape_text = stringify_node(sg, self.shape.node)
        severity_node_text = stringify_node(sg, severity)
        focus_node_text = stringify_node(datagraph or sg, focus_node)
        desc = "{} in {} ({}):\n\tSeverity: {}\n\tSource Shape: {}\n\tFocus Node: {}\n".format(
            severity_desc,
            constraint_name,
            str(constraint_component),
            severity_node_text,
            source_shape_text,
            focus_node_text,
        )
        if value_node is not None:
            val_node_string = stringify_node(datagraph or sg, value_node)
            desc += "\tValue Node: {}\n".format(val_node_string)
        if result_path is None and self.shape.is_property_shape:
            result_path = self.shape.path()
        if result_path:
            result_path_text = stringify_node(sg, result_path)
            desc += "\tResult Path: {}\n".format(result_path_text)
        if source_constraint:
            sc_text = stringify_node(sg, source_constraint)
            desc += "\tSource Constraint: {}\n".format(sc_text)
        if extra_messages:
            for m in iter(extra_messages):
                if m in messages:
                    continue
                if isinstance(m, Literal):
                    msg = str(m.value)
                    if bound_vars is not None:
                        msg = self._format_sparql_based_result_message(msg, bound_vars)
                    desc += "\tMessage: {}\n".format(msg)
                else:  # pragma: no cover
                    desc += "\tMessage: {}\n".format(str(m))
        for m in messages:
            if isinstance(m, Literal):
                msg = str(m.value)
                if bound_vars is not None:
                    msg = self._format_sparql_based_result_message(msg, bound_vars)
                desc += "\tMessage: {}\n".format(msg)
            else:  # pragma: no cover
                desc += "\tMessage: {}\n".format(str(m))
        return desc

    def make_v_result(
        self,
        datagraph: GraphLike,
        focus_node: 'RDFNode',
        value_node: Optional['RDFNode'] = None,
        result_path: Optional['RDFNode'] = None,
        constraint_component: Optional['RDFNode'] = None,
        source_constraint: Optional['RDFNode'] = None,
        extra_messages: Optional[Iterable] = None,
        bound_vars=None,
    ):
        """
        :param datagraph:
        :type datagraph: rdflib.Graph | rdflib.ConjunctiveGraph | rdflib.Dataset
        :param focus_node:
        :type focus_node: RDFNode
        :param value_node:
        :type value_node: RDFNode | None
        :param result_path:
        :type result_path: RDFNode | None
        :param constraint_component:
        :param source_constraint:
        :param extra_messages:
        :type extra_messages: collections.abc.Iterable | None
        :param bound_vars:
        :return:
        """
        constraint_component = constraint_component or self.shacl_constraint_component
        severity = self.shape.severity
        sg = self.shape.sg.graph
        r_triples: List[Tuple[RDFNode, RDFNode, Any]] = list()
        r_node = BNode()
        r_triples.append((r_node, RDF_type, SH_ValidationResult))
        r_triples.append((r_node, SH_sourceConstraintComponent, (sg, constraint_component)))
        r_triples.append((r_node, SH_sourceShape, (sg, self.shape.node)))
        r_triples.append((r_node, SH_resultSeverity, severity))
        r_triples.append((r_node, SH_focusNode, (datagraph or sg, focus_node)))
        if value_node is not None:
            r_triples.append((r_node, SH_value, (datagraph, value_node)))
        if result_path is None and self.shape.is_property_shape:
            result_path = self.shape.path()
        if result_path is not None:
            r_triples.append((r_node, SH_resultPath, (sg, result_path)))
        if source_constraint is not None:
            r_triples.append((r_node, SH_sourceConstraint, (sg, source_constraint)))
        messages = list(self.shape.message)
        if extra_messages:
            for m in iter(extra_messages):
                if m in messages:
                    continue
                if isinstance(m, Literal):
                    msg = str(m.value)
                    if bound_vars is not None:
                        msg = self._format_sparql_based_result_message(msg, bound_vars)
                        m = Literal(msg)
                r_triples.append((r_node, SH_resultMessage, m))
        elif not messages:
            messages = self.make_generic_messages(datagraph, focus_node, value_node) or messages
        for m in messages:
            if isinstance(m, Literal):
                msg = str(m.value)
                if bound_vars is not None:
                    msg = self._format_sparql_based_result_message(msg, bound_vars)
                    m = Literal(msg)
            r_triples.append((r_node, SH_resultMessage, m))
        desc = self.make_v_result_description(
            datagraph,
            focus_node,
            severity,
            value_node,
            messages,
            result_path=result_path,
            constraint_component=constraint_component,
            source_constraint=source_constraint,
            extra_messages=extra_messages,
            bound_vars=bound_vars,
        )
        return desc, r_node, r_triples

    def _format_sparql_based_result_message(self, msg, bound_vars):
        if bound_vars is None:
            return msg
        fdict = {}
        if isinstance(bound_vars, (tuple, list)):
            if len(bound_vars) == 4:
                fdict.update(bound_vars[3])
                bound_vars = bound_vars[:3]
            if len(bound_vars) == 3:
                if bound_vars[0] is not None:
                    fdict['this'] = bound_vars[0]
                if bound_vars[1] is not None:
                    fdict['path'] = bound_vars[1]
                if bound_vars[2] is not None:
                    fdict['value'] = bound_vars[2]

        elif isinstance(bound_vars, dict):
            fdict.update(bound_vars)
        else:
            return msg
        for var, val in fdict.items():
            substring = "{{[?$]{}}}".format(var)
            msg = re.sub(substring, str(val), msg)
        return msg


SH_nodeValidator = SH.nodeValidator
SH_propertyValidator = SH.propertyValidator
SH_validator = SH.validator
SH_optional = SH.optional
SH_SPARQLSelectValidator = SH.SPARQLSelectValidator
SH_SPARQLAskValidator = SH.SPARQLAskValidator
SH_JSValidator = SH.JSValidator


class CustomConstraintComponentFactory(object):
    __slots__: Tuple = tuple()

    def __new__(cls, shacl_graph: 'ShapesGraph', node):
        self: List[Any] = list()
        self.append(shacl_graph)
        self.append(node)
        optional_params = []
        mandatory_params = []
        param_nodes = set(shacl_graph.objects(node, SH_parameter))
        if len(param_nodes) < 1:
            # TODO:coverage: we don't have any tests for invalid constraints
            raise ConstraintLoadError(
                "A sh:ConstraintComponent must have at least one value for sh:parameter",
                "https://www.w3.org/TR/shacl/#constraint-components-parameters",
            )
        for param_node in iter(param_nodes):
            path_nodes = set(shacl_graph.objects(param_node, SH_path))
            if len(path_nodes) < 1:
                # TODO:coverage: we don't have any tests for invalid constraints
                raise ConstraintLoadError(
                    "A sh:ConstraintComponent parameter value must have at least one value for sh:path",
                    "https://www.w3.org/TR/shacl/#constraint-components-parameters",
                )
            elif len(path_nodes) > 1:
                # TODO:coverage: we don't have any tests for invalid constraints
                raise ConstraintLoadError(
                    "A sh:ConstraintComponent parameter value must have at most one value for sh:path",
                    "https://www.w3.org/TR/shacl/#constraint-components-parameters",
                )
            path = next(iter(path_nodes))
            parameter = SHACLParameter(shacl_graph, param_node, path=path, logger=None)  # pass in logger?
            if parameter.optional:
                optional_params.append(parameter)
            else:
                mandatory_params.append(parameter)
        if len(mandatory_params) < 1:
            # TODO:coverage: we don't have any tests for invalid constraint components
            raise ConstraintLoadError(
                "A sh:ConstraintComponent must have at least one non-optional parameter.",
                "https://www.w3.org/TR/shacl/#constraint-components-parameters",
            )
        self.append(mandatory_params + optional_params)

        validator_node_set = set(shacl_graph.graph.objects(node, SH_validator))
        node_val_node_set = set(shacl_graph.graph.objects(node, SH_nodeValidator))
        prop_val_node_set = set(shacl_graph.graph.objects(node, SH_propertyValidator))
        validator_node_set = validator_node_set.difference(node_val_node_set)
        validator_node_set = validator_node_set.difference(prop_val_node_set)
        self.append(validator_node_set)
        self.append(node_val_node_set)
        self.append(prop_val_node_set)
        is_sparql_constraint_component = False
        is_js_constraint_component = False
        for s in (validator_node_set, node_val_node_set, prop_val_node_set):
            for v in s:
                v_types = set(shacl_graph.graph.objects(v, RDF_type))
                if SH_SPARQLAskValidator in v_types or SH_SPARQLSelectValidator in v_types:
                    is_sparql_constraint_component = True
                    break
                elif SH_JSValidator in v_types:
                    is_js_constraint_component = True
                    break
                v_props = set(p[0] for p in shacl_graph.graph.predicate_objects(v))
                if SH_ask in v_props or SH_select in v_props:
                    is_sparql_constraint_component = True
                    break
                elif SH_jsFunctionName in v_props:
                    is_js_constraint_component = True
                    break
                if is_sparql_constraint_component:
                    raise ConstraintLoadError(
                        "Found a mix of SPARQL-based validators and non-SPARQL validators on a SPARQLConstraintComponent.",  # noqa
                        'https://www.w3.org/TR/shacl/#constraint-components-validators',
                    )
                elif is_js_constraint_component:
                    raise ConstraintLoadError(
                        "Found a mix of JS-based validators and non-JS validators on a JSConstraintComponent.",
                        'https://www.w3.org/TR/shacl/#constraint-components-validators',
                    )
        if is_sparql_constraint_component:
            from pyshacl.constraints.sparql.sparql_based_constraint_components import SPARQLConstraintComponent

            return SPARQLConstraintComponent(*self)
        elif is_js_constraint_component and shacl_graph.js_enabled:
            from pyshacl.extras.js.constraint_component import JSConstraintComponent

            return JSConstraintComponent(*self)
        else:
            return CustomConstraintComponent(*self)


class CustomConstraintComponent(object):
    __slots__: Tuple = ('sg', 'node', 'parameters', 'validators', 'node_validators', 'property_validators')

    if typing.TYPE_CHECKING:
        sg: ShapesGraph
        node: Any
        parameters: List[SHACLParameter]
        validators: Set
        node_validators: Set
        property_validators: Set

    def __new__(cls, shacl_graph: 'ShapesGraph', node, parameters, validators, node_validators, property_validators):
        self = super(CustomConstraintComponent, cls).__new__(cls)
        self.sg = shacl_graph
        self.node = node
        self.parameters = parameters
        self.validators = validators
        self.node_validators = node_validators
        self.property_validators = property_validators
        return self

    def make_validator_for_shape(self, shape: 'Shape'):
        raise NotImplementedError()
