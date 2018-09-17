# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#sparql-constraint-components
"""
import rdflib

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.constraints.sparql.sparql_based_constraints import SH_select
from pyshacl.consts import SH, RDF_type
from pyshacl.errors import ConstraintLoadError, ValidationFailure, ReportableRuntimeError

SH_nodeValidator = SH.term('nodeValidator')
SH_propertyValidator = SH.term('propertyValidator')
SH_validator = SH.term('validator')
SH_parameter = SH.term('parameter')
SH_optional = SH.term('optional')
SH_ask = SH.term('ask')


SH_ConstraintComponent = SH.term('ConstraintComponent')
SH_SPARQLSelectValidator = SH.term('SPARQLSelectValidator')
SH_SPARQLAskValidator = SH.term('SPARQLAskValidator')


invalid_parameter_names = {
                           'this', 'shapesGraph', 'currentShape', 'path',
                           'PATH', 'value'
                          }


class SPARQLConstraintComponentValidator(object):
    def __new__(cls, shape, node, *args, **kwargs):
        sg = shape.sg
        type_vals = set(sg.objects(node, RDF_type))
        validator_type = None
        if len(type_vals) > 0:
            if SH_SPARQLSelectValidator in type_vals:
                validator_type = SelectConstraintValidator
            elif SH_SPARQLAskValidator in type_vals:
                validator_type = AskConstraintValidator

        sel_nodes = set(sg.objects(node, SH_select))
        if len(sel_nodes) > 0:
            validator_type = SelectConstraintValidator
        ask_nodes = set(sg.objects(node, SH_ask))
        if len(ask_nodes) > 0:
            validator_type = AskConstraintValidator

        if not validator_type:
            raise ConstraintLoadError("Validator must be of type SPARQLSelectValidator or SPARQLAskValidator and must have either a sh:select or a sh:ask predicate.",
                                      "https://www.w3.org/TR/shacl/#ConstraintComponent")
        return validator_type.__new__(shape, node, *args, **kwargs)

    def __init__(self, shape, node, deactivated=False):
        self.shape = shape
        self.node = node
        self.deactivated = deactivated


class AskConstraintValidator(SPARQLConstraintComponentValidator):
    def __new__(cls, shape, node, *args, **kwargs):
        pass
    pass


class SelectConstraintValidator(SPARQLConstraintComponentValidator):
    def __new__(cls, shape, node, *args, **kwargs):
        pass
    pass


class SPARQLConstraintComponent(ConstraintComponent):
    """
    SPARQL-based constraints provide a lot of flexibility but may be hard to understand for some people or lead to repetition. This section introduces SPARQL-based constraint components as a way to abstract the complexity of SPARQL and to declare high-level reusable components similar to the Core constraint components. Such constraint components can be declared using the SHACL RDF vocabulary and thus shared and reused.
    Link:
    https://www.w3.org/TR/shacl/#sparql-constraint-components
    """

    def __init__(self, shape):
        super(SPARQLConstraintComponent, self).__init__(shape)
        validator_node_list = set(self.shape.objects(SH_validator))
        node_val_node_list = set(self.shape.objects(SH_nodeValidator))
        prop_val_node_list = set(self.shape.objects(SH_propertyValidator))
        val_count = len(validator_node_list)
        node_val_count = len(node_val_node_list)
        prop_val_count = len(prop_val_node_list)
        if (val_count + node_val_count + prop_val_count) < 1:
            raise ConstraintLoadError(
                "ConstraintComponent must have at least one sh:validator, "
                "sh:nodeValidator, or sh:propertyValidator predicates.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")

        must_be_select_val = False
        must_be_ask_val = False
        if shape.is_property_shape and prop_val_count > 0:
            validator_node = next(iter(prop_val_node_list))
            must_be_select_val = True
        elif (not shape.is_property_shape) and node_val_count > 0:
            validator_node = next(iter(node_val_node_list))
            must_be_select_val = True
        elif val_count > 0:
            validator_node = next(iter(validator_node_list))
            must_be_ask_val = True
        else:
            raise ConstraintLoadError(
                "Cannot select a validator to use, according to the rules.",
                "https://www.w3.org/TR/shacl/#constraint-components-validators")

        self.validator = SPARQLConstraintComponentValidator(self.shape, validator_node)


    @classmethod
    def constraint_parameters(cls):
        return [SH_validator, SH_nodeValidator,
                SH_propertyValidator, SH_parameter]

    @classmethod
    def constraint_name(cls):
        return "ConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_ConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for sparql_constraint in self.sparql_constraints:
            if sparql_constraint.deactivated:
                continue
            _nc, _r = self._evaluate_sparql_constraint(
                sparql_constraint, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_sparql_constraint(self, sparql_constraint,
                                    target_graph, f_v_dict):
        reports = []
        non_conformant = False
        extra_messages = sparql_constraint.messages or None
        rept_kwargs = {
            'source_constraint': sparql_constraint.node,
            'extra_messages': extra_messages
        }
        for f, value_nodes in f_v_dict.items():
            # we don't use value_nodes in the sparql constraint
            # All queries are done on the corresponding focus node.
            init_binds, sparql_text = sparql_constraint.pre_bind_variables(f)
            sparql_text = sparql_constraint.apply_prefixes(sparql_text)

            try:
                violating_vals = self._validate_sparql_query(
                    sparql_text, init_binds, target_graph)

            except ValidationFailure as e:
                raise e
            for v in violating_vals:
                non_conformant = True
                if isinstance(v, bool) and v is True:
                    rept = self.make_v_result(
                        f, **rept_kwargs)
                elif isinstance(v, tuple):
                    rept = self.make_v_result(
                        f, value_node=v[0], result_path=v[1],
                        **rept_kwargs)
                else:
                    rept = self.make_v_result(
                        f, value_node=v,
                        **rept_kwargs)
                reports.append(rept)
        return non_conformant, reports

    def _validate_sparql_query(self, query, init_binds, target_graph):
        results = target_graph.query(query, initBindings=init_binds)
        if not results or len(results.bindings) < 1:
            return []
        violations = set()
        for r in results:
            try:
                p = r['path']
            except KeyError:
                p = False
            try:
                v = r['value']
                if p:
                    v = (v, p)
                violations.add(v)
            except KeyError:
                pass
            try:
                f = r['failure']
                violations.add(True)
            except KeyError:
                pass
        return violations


