# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#sparql-constraint-components
"""
from typing import Dict, List, Tuple, Union

import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.constraints.sparql.sparql_based_constraints import SPARQLQueryHelper
from pyshacl.consts import SH, RDF_type, SH_ask, SH_message, SH_parameter, SH_path, SH_select
from pyshacl.errors import ConstraintLoadError, ValidationFailure
from pyshacl.parameter import SHACLParameter
from pyshacl.pytypes import GraphLike


SH_nodeValidator = SH.term('nodeValidator')
SH_propertyValidator = SH.term('propertyValidator')
SH_validator = SH.term('validator')
SH_optional = SH.term('optional')

SH_ConstraintComponent = SH.term('ConstraintComponent')
SH_SPARQLSelectValidator = SH.term('SPARQLSelectValidator')
SH_SPARQLAskValidator = SH.term('SPARQLAskValidator')


class BoundShapeValidatorComponent(ConstraintComponent):
    def __init__(self, constraint, shape, validator):
        """
        Create a new custom constraint, by applying a ConstraintComponent and a Validator to a Shape
        :param constraint: The source ConstraintComponent, this is needed to bind the parameters in the query_helper
        :type constraint: SPARQLConstraintComponent
        :param shape:
        :type shape: pyshacl.shape.Shape
        :param validator:
        :type validator: AskConstraintValidator | SelectConstraintValidator
        """
        super(BoundShapeValidatorComponent, self).__init__(shape)
        self.constraint = constraint
        self.validator = validator
        params = constraint.parameters
        self.query_helper = SPARQLQueryHelper(
            self.shape, validator.node, validator.query_text, params, messages=validator.messages
        )
        # Setting self.shape into QueryHelper automatically applies query_helper.bind_params and bind_messages
        self.query_helper.collect_prefixes()

    @classmethod
    def constraint_parameters(cls):
        # TODO:coverage: this is never used for this constraint?
        return [SH_validator, SH_nodeValidator, SH_propertyValidator]

    @classmethod
    def constraint_name(cls):
        return "ConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        # TODO:coverage: this is never used for this constraint?
        return SH_ConstraintComponent

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False
        extra_messages = self.query_helper.messages or None
        rept_kwargs = {
            # TODO, determine if we need sourceConstraint here
            #  'source_constraint': self.validator.node,
            'constraint_component': self.constraint.node,
            'extra_messages': extra_messages,
        }
        for f, value_nodes in focus_value_nodes.items():
            # we don't use value_nodes in the sparql constraint
            # All queries are done on the corresponding focus node.
            try:
                violations = self.validator.validate(f, value_nodes, target_graph, self.query_helper)
            except ValidationFailure as e:
                raise e
            if not self.shape.is_property_shape:
                result_val = f
            else:
                result_val = None
            for v in violations:
                non_conformant = True
                if isinstance(v, bool) and v is True:
                    # TODO:coverage: No test for when violation is `True`
                    rept = self.make_v_result(target_graph, f, value_node=result_val, **rept_kwargs)
                elif isinstance(v, tuple):
                    t, p, v = v
                    if v is None:
                        v = result_val
                    rept = self.make_v_result(target_graph, t or f, value_node=v, result_path=p, **rept_kwargs)
                else:
                    rept = self.make_v_result(target_graph, f, value_node=v, **rept_kwargs)
                reports.append(rept)
        return (not non_conformant), reports


class SPARQLConstraintComponentValidator(object):
    validator_cache: Dict[Tuple[int, str], Union['SelectConstraintValidator', 'AskConstraintValidator']] = {}

    def __new__(cls, shacl_graph, node, *args, **kwargs):
        cache_key = (id(shacl_graph.graph), str(node))
        found_in_cache = cls.validator_cache.get(cache_key, False)
        if found_in_cache:
            return found_in_cache
        sg = shacl_graph.graph
        type_vals = set(sg.objects(node, RDF_type))
        validator_type = None
        if len(type_vals) > 0:
            if SH_SPARQLSelectValidator in type_vals:
                validator_type = SelectConstraintValidator
            elif SH_SPARQLAskValidator in type_vals:
                validator_type = AskConstraintValidator
        if not validator_type:
            sel_nodes = set(sg.objects(node, SH_select))
            if len(sel_nodes) > 0:
                # TODO:coverage: No test for this case
                validator_type = SelectConstraintValidator
        if not validator_type:
            ask_nodes = set(sg.objects(node, SH_ask))
            if len(ask_nodes) > 0:
                validator_type = AskConstraintValidator

        if not validator_type:
            # TODO:coverage: No test for this case
            raise ConstraintLoadError(
                "Validator must be of type sh:SPARQLSelectValidator or sh:SPARQLAskValidator and must have either a sh:select or a sh:ask predicate.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )
        validator = validator_type(shacl_graph, node, *args, **kwargs)
        cls.validator_cache[cache_key] = validator
        return validator

    def apply_to_shape_via_constraint(self, constraint, shape, **kwargs) -> BoundShapeValidatorComponent:
        """
        Create a new Custom Constraint (BoundShapeValidatorComponent)
        :param constraint:
        :type constraint: SPARQLConstraintComponent
        :param shape:
        :type shape: pyshacl.shape.Shape
        :param kwargs:
        :return:
        """
        must_be_ask_val = kwargs.pop('must_be_ask_val', False)
        if must_be_ask_val and not (isinstance(self, AskConstraintValidator)):
            # TODO:coverage: No test for this case, do we need to test this?
            raise ConstraintLoadError(
                "Validator not for NodeShape or a PropertyShape must be of type SPARQLAskValidator.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )
        must_be_select_val = kwargs.pop('must_be_select_val', False)
        if must_be_select_val and not (isinstance(self, SelectConstraintValidator)):
            # TODO:coverage: No test for this case, do we need to test this?
            raise ConstraintLoadError(
                "Validator for a NodeShape or a PropertyShape must be of type SPARQLSelectValidator.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )

        return BoundShapeValidatorComponent(constraint, shape, self)

    def __init__(self, shacl_graph, node, **kwargs):
        initialised = getattr(self, 'initialised', False)
        if initialised:
            return
        self.shacl_graph = shacl_graph
        self.node = node
        sg = shacl_graph.graph
        message_nodes = set(sg.objects(node, SH_message))
        for m in message_nodes:
            if not (isinstance(m, rdflib.Literal) and isinstance(m.value, str)):
                # TODO:coverage: No test for when SPARQL-based constraint is RDF Literal is is not of type string
                raise ConstraintLoadError(
                    "Validator sh:message must be an RDF Literal of type xsd:string.",
                    "https://www.w3.org/TR/shacl/#ConstraintComponent",
                )
        self.messages = message_nodes
        self.initialised = True


class AskConstraintValidator(SPARQLConstraintComponentValidator):
    def __new__(cls, shacl_graph, node, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, shacl_graph, node, *args, **kwargs):
        super(AskConstraintValidator, self).__init__(shacl_graph, node, **kwargs)
        g = shacl_graph.graph
        ask_vals = set(g.objects(node, SH_ask))
        if len(ask_vals) < 1 or len(ask_vals) > 1:
            # TODO:coverage: No test for this case
            raise ConstraintLoadError(
                "AskValidator must have exactly one value for sh:ask.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )
        ask_val = next(iter(ask_vals))
        if not (isinstance(ask_val, rdflib.Literal) and isinstance(ask_val.value, str)):
            # TODO:coverage: No test for this case
            raise ConstraintLoadError(
                "AskValidator sh:ask must be an RDF Literal of type xsd:string.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )
        self.query_text = ask_val.value

    def validate(self, focus, value_nodes, target_graph, query_helper=None, new_bind_vals=None):
        """

        :param focus:
        :param value_nodes:
        :param query_helper:
        :param target_graph:
        :type target_graph: rdflib.Graph
        :param new_bind_vals:
        :return:
        """
        param_bind_vals = query_helper.param_bind_map if query_helper else {}
        new_bind_vals = new_bind_vals or {}
        bind_vals = param_bind_vals.copy()
        bind_vals.update(new_bind_vals)
        violations = []
        for v in value_nodes:
            if query_helper is None:
                # TODO:coverage: No test for this case when query_helper is None
                init_binds = {}
                sparql_text = self.query_text
            else:
                init_binds, sparql_text = query_helper.pre_bind_variables(
                    focus, valuenode=v, extravars=bind_vals.keys()
                )
                sparql_text = query_helper.apply_prefixes(sparql_text)
                init_binds.update(bind_vals)
            try:
                result = target_graph.query(sparql_text, initBindings=init_binds)
                answer = result.askAnswer
            except (KeyError, AttributeError):
                # TODO:coverage: Can this ever actually happen?
                raise ValidationFailure("ASK Query did not return an askAnswer.")
            if answer is False:
                violations.append(v)
        return violations


class SelectConstraintValidator(SPARQLConstraintComponentValidator):
    def __new__(cls, shacl_graph, node, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, shacl_graph, node, *args, **kwargs):
        super(SelectConstraintValidator, self).__init__(shacl_graph, node, **kwargs)
        g = shacl_graph.graph
        select_vals = set(g.objects(node, SH_select))
        if len(select_vals) < 1 or len(select_vals) > 1:
            # TODO:coverage: No test for this case, do we need to test this?
            raise ConstraintLoadError(
                "SelectValidator must have exactly one value for sh:select.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )
        select_val = next(iter(select_vals))
        if not (isinstance(select_val, rdflib.Literal) and isinstance(select_val.value, str)):
            # TODO:coverage: No test for the case when sh:select is not a literal of type string
            raise ConstraintLoadError(
                "SelectValidator sh:select must be an RDF Literal of type xsd:string.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )
        self.query_text = select_val.value

    def validate(self, focus, value_nodes, target_graph, query_helper=None, new_bind_vals=None):
        """

        :param focus:
        :param value_nodes:
        :param query_helper:
        :param target_graph:
        :type target_graph: rdflib.Graph
        :param new_bind_vals:
        :return:
        """
        param_bind_vals = query_helper.param_bind_map if query_helper else {}
        new_bind_vals = new_bind_vals or {}
        bind_vals = param_bind_vals.copy()
        bind_vals.update(new_bind_vals)
        for v in value_nodes:
            if query_helper is None:
                # TODO:coverage: No test for this case when query_helper is None
                init_binds = {}
                sparql_text = self.query_text
            else:
                init_binds, sparql_text = query_helper.pre_bind_variables(
                    focus, valuenode=v, extravars=bind_vals.keys()
                )
                sparql_text = query_helper.apply_prefixes(sparql_text)
                init_binds.update(bind_vals)
            results = target_graph.query(sparql_text, initBindings=init_binds)
            if not results or len(results.bindings) < 1:
                return []
            violations = set()
            for r in results:
                try:
                    p = r['path']
                except KeyError:
                    p = None
                try:
                    v = r['value']
                except KeyError:
                    v = None
                try:
                    t = r['this']
                except KeyError:
                    # TODO:coverage: No test for when result has no 'this' key
                    t = None
                if p or v or t:
                    violations.add((t, p, v))
                else:
                    # TODO:coverage: No test for generic failure, when
                    #  'path' and 'value' and 'this' are not returned.
                    #  here 'failure' must exist
                    try:
                        _ = r['failure']
                        violations.add(True)
                    except KeyError:
                        pass
            return violations


class SPARQLConstraintComponent(object):
    """
    SPARQL-based constraints provide a lot of flexibility but may be hard to understand for some people or lead to repetition. This section introduces SPARQL-based constraint components as a way to abstract the complexity of SPARQL and to declare high-level reusable components similar to the Core constraint components. Such constraint components can be declared using the SHACL RDF vocabulary and thus shared and reused.
    Link:
    https://www.w3.org/TR/shacl/#sparql-constraint-components
    """

    def __init__(self, shacl_graph, node):
        self.sg = shacl_graph
        self.node = node
        optional_params = []
        mandatory_params = []
        param_nodes = set(self.sg.objects(self.node, SH_parameter))
        if len(param_nodes) < 1:
            # TODO:coverage: we don't have any tests for invalid constraints
            raise ConstraintLoadError(
                "A sh:ConstraintComponent must have at least one value for sh:parameter",
                "https://www.w3.org/TR/shacl/#constraint-components-parameters",
            )
        for param_node in iter(param_nodes):
            path_nodes = set(self.sg.objects(param_node, SH_path))
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
            parameter = SHACLParameter(self.sg, param_node, path=path, logger=None)  # pass in logger?
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
        self.parameters = mandatory_params + optional_params
        validator_node_list = set(self.sg.graph.objects(node, SH_validator))
        node_val_node_list = set(self.sg.graph.objects(node, SH_nodeValidator))
        prop_val_node_list = set(self.sg.graph.objects(node, SH_propertyValidator))
        self.validator_nodes = validator_node_list
        self.node_validator_nodes = node_val_node_list
        self.prop_validator_nodes = prop_val_node_list
        val_count = len(self.validator_nodes)
        node_val_count = len(self.node_validator_nodes)
        prop_val_count = len(self.prop_validator_nodes)
        if (val_count + node_val_count + prop_val_count) < 1:
            # TODO:coverage: No test for this case, do we need to test this?
            raise ConstraintLoadError(
                "ConstraintComponent must have at least one sh:validator, "
                "sh:nodeValidator, or sh:propertyValidator predicates.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent",
            )

    def make_validator_for_shape(self, shape):
        """
        :param shape:
        :type shape: pyshacl.shape.Shape
        :return:
        """
        val_count = len(self.validator_nodes)
        node_val_count = len(self.node_validator_nodes)
        prop_val_count = len(self.prop_validator_nodes)
        must_be_select_val = False
        must_be_ask_val = False
        if shape.is_property_shape and prop_val_count > 0:
            validator_node = next(iter(self.prop_validator_nodes))
            must_be_select_val = True
        elif (not shape.is_property_shape) and node_val_count > 0:
            validator_node = next(iter(self.node_validator_nodes))
            must_be_select_val = True
        elif val_count > 0:
            validator_node = next(iter(self.validator_nodes))
            must_be_ask_val = True
        else:
            raise ConstraintLoadError(
                "Cannot select a validator to use, according to the rules.",
                "https://www.w3.org/TR/shacl/#constraint-components-validators",
            )

        validator = SPARQLConstraintComponentValidator(self.sg, validator_node)
        applied_validator = validator.apply_to_shape_via_constraint(
            self, shape, must_be_ask_val=must_be_ask_val, must_be_select_val=must_be_select_val
        )
        return applied_validator
