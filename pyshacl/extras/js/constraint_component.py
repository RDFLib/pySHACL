#
#
import typing
from typing import Any, Dict, List, Tuple, Union

from rdflib import Literal

from pyshacl.constraints import ConstraintComponent
from pyshacl.constraints.constraint_component import CustomConstraintComponent
from pyshacl.consts import SH, SH_ConstraintComponent, SH_message
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError, ValidationFailure
from pyshacl.pytypes import GraphLike

from .js_executable import JSExecutable

if typing.TYPE_CHECKING:
    from pyshacl.shape import Shape
    from pyshacl.shapes_graph import ShapesGraph


SH_JSConstraint = SH.JSConstraint
SH_JSConstraintComponent = SH.JSConstraintComponent


class BoundShapeJSValidatorComponent(ConstraintComponent):
    invalid_parameter_names = {'this', 'shapesGraph', 'currentShape', 'path', 'PATH', 'value'}

    shacl_constraint_component = SH_ConstraintComponent

    def __init__(self, constraint, shape: 'Shape', validator):
        """
        Create a new custom constraint, by applying a ConstraintComponent and a Validator to a Shape
        :param constraint: The source ConstraintComponent, this is needed to bind the parameters in the query_helper
        :type constraint: SPARQLConstraintComponent
        :param shape:
        :type shape: Shape
        :param validator:
        :type validator: AskConstraintValidator | SelectConstraintValidator
        """
        super(BoundShapeJSValidatorComponent, self).__init__(shape)
        self.constraint = constraint
        self.validator = validator
        self.param_bind_map: Dict[str, Any] = {}
        self.messages: List[Any] = []
        self.bind_params()

    def bind_params(self):
        bind_map = {}
        shape = self.shape
        for p in self.constraint.parameters:
            name = p.localname
            if name in self.invalid_parameter_names:
                # TODO:coverage: No test for this case
                raise ReportableRuntimeError("Parameter name {} cannot be used.".format(name))
            shape_params = set(shape.objects(p.path()))
            if len(shape_params) < 1:
                if not p.optional:
                    # TODO:coverage: No test for this case
                    raise ReportableRuntimeError("Shape does not have mandatory parameter {}.".format(str(p.path())))
                continue
            # TODO: Can shapes have more than one value for the predicate?
            # Just use one for now.
            # TODO: Check for sh:class and sh:nodeKind on the found param value
            bind_map[name] = next(iter(shape_params))
        self.param_bind_map = bind_map

    @classmethod
    def constraint_parameters(cls):
        # TODO:coverage: this is never used for this constraint?
        return []

    @classmethod
    def constraint_name(cls):
        return "ConstraintComponent"

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        return [Literal("Parameterised Javascript Function generated constraint validation reports.")]

    def evaluate(self, data_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type focus_value_nodes: dict
        :type data_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False
        extra_messages = self.messages or []
        rept_kwargs = {
            'constraint_component': self.constraint.node,
            'extra_messages': extra_messages,
        }
        for f, value_nodes in focus_value_nodes.items():
            try:
                p = self.shape.path()
                results = self.validator.validate(f, value_nodes, p, data_graph, self.param_bind_map)
            except ValidationFailure as e:
                raise e
            for v, result in results:
                if result is True:
                    continue
                args_map = self.param_bind_map.copy()
                args_map.update({"this": f, "value": v})
                if self.shape.is_property_shape:
                    args_map['path'] = self.shape.path()
                bound_messages = self.validator.make_messages(args_map)
                failed = False
                if isinstance(result, list):
                    pass
                else:
                    result = [result]
                for res in result:
                    if isinstance(res, Literal):
                        res = res.value
                    if isinstance(res, bool):
                        if res:
                            continue
                        else:
                            failed = True
                            new_kwargs = rept_kwargs.copy()
                            new_kwargs['extra_messages'].extend(bound_messages)
                            reports.append(self.make_v_result(data_graph, f, value_node=v, **new_kwargs))
                    elif isinstance(res, str):
                        failed = True
                        m = Literal(res)
                        new_kwargs = rept_kwargs.copy()
                        new_kwargs['extra_messages'].append(m)
                        new_kwargs['extra_messages'].extend(bound_messages)
                        reports.append(self.make_v_result(data_graph, f, value_node=v, **new_kwargs))
                    elif isinstance(res, dict):
                        failed = True
                        args_map2 = args_map.copy()
                        val = res.get('value', None)
                        if val is None:
                            val = v
                        args_map2['value'] = val
                        path = res.get('path', None) if not self.shape.is_property_shape else None
                        if path is not None:
                            args_map2['value'] = path
                        msgs = self.validator.make_messages(args_map2)
                        message = res.get('message', None)
                        if message is not None:
                            msgs.append(Literal(message))
                        new_kwargs = rept_kwargs.copy()
                        new_kwargs['extra_messages'].extend(msgs)
                        reports.append(
                            self.make_v_result(data_graph, f, value_node=val, result_path=path, **new_kwargs)
                        )
                if failed:
                    non_conformant = True
        return (not non_conformant), reports


class JSConstraintComponent(CustomConstraintComponent):
    """
    SPARQL-based constraints provide a lot of flexibility but may be hard to understand for some people or lead to repetition. This section introduces SPARQL-based constraint components as a way to abstract the complexity of SPARQL and to declare high-level reusable components similar to the Core constraint components. Such constraint components can be declared using the SHACL RDF vocabulary and thus shared and reused.
    Link:
    https://www.w3.org/TR/shacl-js/#js-components
    """

    __slots__: Tuple = tuple()

    def __new__(cls, shacl_graph, node, parameters, validators, node_validators, property_validators):
        return super(JSConstraintComponent, cls).__new__(
            cls, shacl_graph, node, parameters, validators, node_validators, property_validators
        )

    def make_validator_for_shape(self, shape: 'Shape'):
        """
        :param shape:
        :type shape: Shape
        :return:
        """
        val_count = len(self.validators)
        node_val_count = len(self.node_validators)
        prop_val_count = len(self.property_validators)
        is_property_val = False
        if shape.is_property_shape and prop_val_count > 0:
            validator_node = next(iter(self.property_validators))
            is_property_val = True
        elif (not shape.is_property_shape) and node_val_count > 0:
            validator_node = next(iter(self.node_validators))
        elif val_count > 0:
            validator_node = next(iter(self.validators))
        else:
            raise ConstraintLoadError(
                "Cannot select a validator to use, according to the rules.",
                "https://www.w3.org/TR/shacl/#constraint-components-validators",
            )
        if is_property_val:
            validator: Union[
                JSConstraintComponentValidator, JSConstraintComponentPathValidator
            ] = JSConstraintComponentPathValidator(self.sg, validator_node)
        else:
            validator = JSConstraintComponentValidator(self.sg, validator_node)
        applied_validator = validator.apply_to_shape_via_constraint(self, shape)
        return applied_validator


class JSConstraintComponentValidator(JSExecutable):
    __slots__ = ("messages", "initialised")

    validator_cache: Dict[Tuple[int, str], 'JSConstraintComponentValidator'] = {}

    def __new__(cls, shacl_graph: 'ShapesGraph', node, *args, **kwargs):
        cache_key = (id(shacl_graph.graph), str(node))
        found_in_cache = cls.validator_cache.get(cache_key, False)
        if found_in_cache:
            return found_in_cache
        self = super(JSConstraintComponentValidator, cls).__new__(cls, shacl_graph, node)
        cls.validator_cache[cache_key] = self
        return self

    def __init__(self, shacl_graph: 'ShapesGraph', node, *args, **kwargs):
        initialised = getattr(self, 'initialised', False)
        if initialised:
            return
        super(JSConstraintComponentValidator, self).__init__(shacl_graph, node)
        sg = shacl_graph.graph
        message_nodes = set(sg.objects(node, SH_message))
        for m in message_nodes:
            if not (isinstance(m, Literal) and isinstance(m.value, str)):
                # TODO:coverage: No test for when SPARQL-based constraint is RDF Literal is is not of type string
                raise ConstraintLoadError(
                    "Validator sh:message must be an RDF Literal of type xsd:string.",
                    "https://www.w3.org/TR/shacl/#ConstraintComponent",
                )
        self.messages = message_nodes
        self.initialised = True

    def make_messages(self, args_map=None):
        if args_map is None:
            return self.messages
        ret_msgs = []
        for m in self.messages:
            this_m = m.value[:]
            for a, v in args_map.items():
                replace_me = "{$" + str(a) + "}"
                if isinstance(v, Literal):
                    v = v.value
                this_m = this_m.replace(replace_me, str(v))
            ret_msgs.append(Literal(this_m))
        return ret_msgs

    def validate(self, f, value_nodes, path, data_graph, param_bind_vals, new_bind_vals=None):
        """

        :param f:
        :param value_nodes:
        :param path:
        :param data_graph:
        :type data_graph: rdflib.Graph
        :param new_bind_vals:
        :return:
        """
        new_bind_vals = new_bind_vals or {}
        bind_vals = param_bind_vals.copy()
        bind_vals.update(new_bind_vals)
        results = []
        for v in value_nodes:
            args_map = bind_vals.copy()
            args_map.update({'this': f, 'value': v})
            try:
                result_dict = self.execute(data_graph, args_map)
                results.append((v, result_dict['_result']))
            except Exception as e:
                print(e)
                raise
        return results

    def apply_to_shape_via_constraint(self, constraint, shape, **kwargs) -> BoundShapeJSValidatorComponent:
        """
        Create a new Custom Constraint (BoundShapeValidatorComponent)
        :param constraint:
        :type constraint: JSConstraintComponent
        :param shape:
        :type shape: pyshacl.shape.Shape
        :param kwargs:
        :return:
        :rtype: BoundShapeJSValidatorComponent
        """
        return BoundShapeJSValidatorComponent(constraint, shape, self)


class JSConstraintComponentPathValidator(JSConstraintComponentValidator):
    path_validator_cache: Dict[Tuple[int, str], 'JSConstraintComponentPathValidator'] = {}

    def __new__(cls, shacl_graph: 'ShapesGraph', node, *args, **kwargs):
        cache_key = (id(shacl_graph.graph), str(node))
        found_in_cache = cls.path_validator_cache.get(cache_key, False)
        if found_in_cache:
            return found_in_cache
        self = super(JSConstraintComponentPathValidator, cls).__new__(cls, shacl_graph, node)
        cls.path_validator_cache[cache_key] = self
        return self

    def validate(self, f, value_nodes, path, data_graph, param_bind_vals, new_bind_vals=None):
        """

        :param f:
        :param value_nodes:
        :param path:
        :param data_graph:
        :type data_graph: rdflib.Graph
        :param new_bind_vals:
        :return:
        """
        new_bind_vals = new_bind_vals or {}
        args_map = param_bind_vals.copy()
        args_map.update(new_bind_vals)
        args_map.update({'this': f, 'path': path})
        results = []
        try:
            result_dict = self.execute(data_graph, args_map)
            results.append((f, result_dict['_result']))
        except Exception as e:
            print(e)
            raise
        return results
