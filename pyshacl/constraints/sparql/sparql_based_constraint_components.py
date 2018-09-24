# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#sparql-constraint-components
"""
import re
import rdflib
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.constraints.sparql.sparql_based_constraints import SH_select, SPARQLQueryHelper
from pyshacl.consts import SH, RDF_type, SH_message
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
    validator_cache = {}

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
                validator_type = SelectConstraintValidator
        if not validator_type:
            ask_nodes = set(sg.objects(node, SH_ask))
            if len(ask_nodes) > 0:
                validator_type = AskConstraintValidator

        if not validator_type:
            raise ConstraintLoadError("Validator must be of type sh:SPARQLSelectValidator or sh:SPARQLAskValidator and must have either a sh:select or a sh:ask predicate.",
                                      "https://www.w3.org/TR/shacl/#ConstraintComponent")
        validator = validator_type(shacl_graph, node, *args, **kwargs)
        cls.validator_cache[cache_key] = validator
        return validator

    def apply_to_shape_via_constraint(self, constraint, shape, **kwargs):
        """

        :param constraint:
        :type constraint: SPARQLConstraintComponent
        :param shape:
        :type shape: pyshacl.shape.Shape
        :param kwargs:
        :return:
        """
        must_be_ask_val = kwargs.pop('must_be_ask_val', False)
        if must_be_ask_val and not(isinstance(self, AskConstraintValidator)):
            raise ConstraintLoadError(
                "Validator not for NodeShape or a PropertyShape must be of type SPARQLAskValidator.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")
        must_be_select_val = kwargs.pop('must_be_select_val', False)
        if must_be_select_val and not (isinstance(self, SelectConstraintValidator)):
            raise ConstraintLoadError(
                "Validator for a NodeShape or a PropertyShape must be of type SPARQLSelectValidator.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")
        bind_map = {}
        for m in constraint.mandatory_parameters:
            name = constraint.parameter_name(m)
            if name in invalid_parameter_names:
                raise ReportableRuntimeError("Parameter name {} cannot be used.".format(name))
            shape_params = set(shape.objects(m.path()))
            if len(shape_params) < 1:
                raise ReportableRuntimeError(
                    "Shape does not have mandatory parameter {}.".format(str(m.path())))
            # TODO: Can shapes have more than one value for the predicate?
            # Just use one for now.
            bind_map[name] = next(iter(shape_params))
        for o in constraint.optional_parameters:
            name = constraint.parameter_name(o)
            if name in invalid_parameter_names:
                raise ReportableRuntimeError("Parameter name {} cannot be used.".format(name))
            shape_params = set(shape.objects(o.path()))
            if len(shape_params) > 0:
                # TODO: Can shapes have more than one value for the predicate?
                # Just use one for now.
                bind_map[name] = next(iter(shape_params))
        return BoundShapeValidatorComponent(constraint, shape, self, bind_map)

    def __init__(self, shacl_graph, node, **kwargs):
        initialised = getattr(self, 'initialised', False)
        if initialised:
            return
        self.shacl_graph = shacl_graph
        self.node = node
        sg = shacl_graph.graph
        message_nodes = set(sg.objects(node, SH_message))
        for m in message_nodes:
            if not (isinstance(m, rdflib.Literal) and
                    isinstance(m.value, str)):
                raise ConstraintLoadError(
                    "Validator sh:message must be an RDF Literal of type xsd:string.",
                    "https://www.w3.org/TR/shacl/#ConstraintComponent")
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
            raise ConstraintLoadError(
                "AskValidator must have exactly one value for sh:ask.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")
        ask_val = next(iter(ask_vals))
        if not (isinstance(ask_val, rdflib.Literal) and
                isinstance(ask_val.value, str)):
            raise ConstraintLoadError(
                "AskValidator sh:ask must be an RDF Literal of type xsd:string.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")
        self.query_text = ask_val.value

    def validate(self, focus, value_nodes, target_graph, query_helper=None, bind_vals=None):
        """

        :param focus:
        :param value_nodes:
        :param query_helper:
        :param target_graph:
        :type target_graph: rdflib.Graph
        :param bind_vals:
        :return:
        """
        if bind_vals is None:
            bind_vals = {}
        violations = []
        for v in value_nodes:
            if query_helper is None:
                init_binds = {}
                sparql_text = self.query_text
            else:
                init_binds, sparql_text = query_helper.pre_bind_variables(focus, valuenode=v, extravars=bind_vals.keys())
                sparql_text = query_helper.apply_prefixes(sparql_text)
                init_binds.update(bind_vals)
            try:
                result = target_graph.query(sparql_text, initBindings=init_binds)
                answer = result.askAnswer
            except (KeyError, AttributeError):
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
            raise ConstraintLoadError(
                "SelectValidator must have exactly one value for sh:select.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")
        select_val = next(iter(select_vals))
        if not (isinstance(select_val, rdflib.Literal) and
                isinstance(select_val.value, str)):
            raise ConstraintLoadError(
                "SelectValidator sh:select must be an RDF Literal of type xsd:string.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")
        self.query_text = select_val.value

    def validate(self, focus, value_nodes, target_graph, query_helper=None, bind_vals=None):
        """

        :param focus:
        :param value_nodes:
        :param query_helper:
        :param target_graph:
        :type target_graph: rdflib.Graph
        :param bind_vals:
        :return:
        """
        if bind_vals is None:
            bind_vals = {}
        for v in value_nodes:
            if query_helper is None:
                init_binds = {}
                sparql_text = self.query_text
            else:
                init_binds, sparql_text = query_helper.pre_bind_variables(focus, valuenode=v)
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
                    pass
                try:
                    t = r['this']
                except KeyError:
                    t = None
                if p or v or t:
                    violations.add((t, p, v))
                else:
                    try:
                        f = r['failure']
                        violations.add(True)
                    except KeyError:
                        pass
            return violations


class BoundShapeValidatorComponent(ConstraintComponent):
    def __init__(self, constraint, shape, validator, param_bind_map):
        """

        :param constraint:
        :type constraint: SPARQLConstraintComponent
        :param shape:
        :type shape: pyshacl.shape.Shape
        :param validator:
        :type validator: AskConstraintValidator | SelectConstraintValidator
        :param param_bind_map:
        :type param_bind_map: dict
        """
        super(BoundShapeValidatorComponent, self).__init__(shape)
        self.constraint = constraint
        self.validator = validator
        self.param_bind_map = param_bind_map
        self.query_helper = SPARQLQueryHelper(
            self.shape, validator.node,
            validator.query_text, messages=validator.messages)
        self.query_helper.collect_prefixes()
        self.message_bind_map = {}
        message_var_finder = re.compile(r"([\s()\"\'])\{[\$\?](\w+)\}", flags=re.M)
        var_replacers = {}
        self.messages = set()
        for m in self.query_helper.messages:
            m_val = str(m.value)
            finds = message_var_finder.findall(m_val)
            if len(finds) < 1:
                self.messages.add(m)
                continue
            for f in finds:
                variable = f[1]
                if variable not in param_bind_map.keys():
                    continue
                try:
                    replacer = var_replacers[variable]
                except KeyError:
                    replacer = re.compile(r"([\s()\"\'])\{[\$\?]"+f[1]+"\}", flags=re.M)
                    var_replacers[variable] = replacer
                m_val = replacer.sub(
                    "\g<1>{}".format(param_bind_map[variable].value),
                    m_val, 1)
            self.messages.add(rdflib.Literal(m_val, lang=m.language, datatype=m.datatype))



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
        extra_messages = self.messages or None
        rept_kwargs = {
            # TODO, determine if we need sourceConstraint here
            #'source_constraint': self.validator.node,
            'constraint_component': self.constraint.node,
            'extra_messages': extra_messages
        }
        for f, value_nodes in focus_value_nodes.items():
            # we don't use value_nodes in the sparql constraint
            # All queries are done on the corresponding focus node.
            try:
                violations = self.validator.validate(
                    f, value_nodes, target_graph, self.query_helper,
                    self.param_bind_map)
            except ValidationFailure as e:
                raise e
            if not self.shape.is_property_shape:
                result_val = f
            else:
                result_val = None
            for v in violations:
                non_conformant = True
                if isinstance(v, bool) and v is True:
                    rept = self.make_v_result(
                        f, value_node=result_val, **rept_kwargs)
                elif isinstance(v, tuple):
                    t, p, v = v
                    if v is None:
                        v = result_val
                    rept = self.make_v_result(
                        t or f, value_node=v, result_path=p,
                        **rept_kwargs)
                else:
                    rept = self.make_v_result(
                        f, value_node=v,
                        **rept_kwargs)
                reports.append(rept)
        return (not non_conformant), reports


class SPARQLConstraintComponent(object):
    """
    SPARQL-based constraints provide a lot of flexibility but may be hard to understand for some people or lead to repetition. This section introduces SPARQL-based constraint components as a way to abstract the complexity of SPARQL and to declare high-level reusable components similar to the Core constraint components. Such constraint components can be declared using the SHACL RDF vocabulary and thus shared and reused.
    Link:
    https://www.w3.org/TR/shacl/#sparql-constraint-components
    """

    def __init__(self, shacl_graph, node, mandatory_parameters, optional_parameters):
        self.sg = shacl_graph
        self.node = node
        self.mandatory_parameters = mandatory_parameters
        self.optional_parameters = optional_parameters
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
            raise ConstraintLoadError(
                "ConstraintComponent must have at least one sh:validator, "
                "sh:nodeValidator, or sh:propertyValidator predicates.",
                "https://www.w3.org/TR/shacl/#ConstraintComponent")

    @classmethod
    def parameter_name(cls, parameter):
        path = str(parameter.path())
        hash_index = path.find('#')
        if hash_index > 0:
            ending = path[hash_index+1:]
            return ending
        right_slash_index = path.rfind('/')
        if right_slash_index > 0:
            ending = path[right_slash_index+1:]
            return ending
        raise ReportableRuntimeError("Cannot get a local name for {}".format(path))

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
                "https://www.w3.org/TR/shacl/#constraint-components-validators")

        validator = SPARQLConstraintComponentValidator(self.sg, validator_node)
        applied_validator = validator.apply_to_shape_via_constraint(
            self, shape, must_be_ask_val=must_be_ask_val,
            must_be_select_val=must_be_select_val)
        return applied_validator

