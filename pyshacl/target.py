import typing
from typing import List, Sequence, Type, Union
from warnings import warn

from .constraints import ConstraintComponent
from .consts import SH, RDF_type, RDFS_subClassOf, SH_parameter, SH_select, SH_SPARQLTargetType
from .errors import ConstraintLoadError, ShapeLoadError
from .helper import get_query_helper_cls
from .parameter import SHACLParameter
from .pytypes import GraphLike

if typing.TYPE_CHECKING:
    from .shapes_graph import ShapesGraph

SH_labelTempalate = SH.labelTemplate
SH_Target = SH.Target
SH_TargetType = SH.TargetType
SH_JSTarget = SH.JSTarget
SH_JSTargetType = SH.JSTargetType
SH_SPARQLTarget = SH.SPARQLTarget


class SHACLTargetType(object):
    __slots__ = ("sg", "node", "parameters", "label_template")

    def __init__(self, t_node, sg):
        """

        :param t_node:
        :type t_node: rdflib.Identifier
        :param sg:
        :type sg: ShapesGraph
        """
        super(SHACLTargetType, self).__init__()
        self.node = t_node
        self.sg = sg
        params = list(sg.objects(t_node, SH_parameter))
        self.parameters = [SHACLParameter(sg, p) for p in params]  # type: List[SHACLParameter]
        ltemps = list(sg.objects(t_node, SH_labelTempalate))
        if len(ltemps) < 1:
            self.label_template = None
        elif len(ltemps) > 1:
            raise ConstraintLoadError(
                "SHACLTargetType cannot have more than one value for sh:labelTemplate.",
                "https://www.w3.org/TR/shacl-af/#SPARQLTargetType",
            )
        else:
            self.label_template = ltemps[0]

    def apply(self):
        self.sg.add_shacl_target_type(self.node, self)

    def check_params(self, target_declaration):
        assert False  # is this even used?
        param_kv = {}
        for p in self.parameters:
            n = p.node
            vals = set(self.sg.objects(target_declaration, n))
            if len(vals) < 1:
                if p.optional:
                    continue
                raise ShapeLoadError(
                    "sh:target does not have a value for {}".format(n),
                    "https://www.w3.org/TR/shacl-af/#SPARQLTargetType",
                )
            if len(vals) > 1:
                warn(Warning("Found more than one value for {} on sh:target. Using just first one.".format(n)))
            param_kv[p] = next(iter(vals))
        return param_kv

    def bind(self, shape, target_declaration):
        assert False  # is this even used?
        param_vals = self.check_params(target_declaration)
        return BoundSHACLTargetType(self, target_declaration, shape, param_vals)


class TargetDeclarationWrapper(object):
    __slots__ = ("sg", "node")

    def __init__(self, sg, node):
        self.sg = sg
        self.node = node

    def objects(self, pred):
        return self.sg.objects(self.node, pred)


class BoundSHACLTargetType(ConstraintComponent):
    __slots__ = ('target_type', 'target_declaration', 'param_vals')

    def __init__(self, target_type, target_declaration, shape, param_vals=None):
        """

        :param target_type: The source TargetType, this is needed to bind the parameters in the query_helper
        :type target_type: SPARQLConstraintComponent
        :param shape:
        :type shape: pyshacl.shape.Shape
        :param param_vals:
        :type param_vals: Dict[SHACLParameter, Any]
        """
        super(BoundSHACLTargetType, self).__init__(shape)
        self.target_type = target_type
        sg = self.shape.sg
        self.target_declaration = TargetDeclarationWrapper(sg, target_declaration)
        self.param_vals = param_vals

    @classmethod
    def constraint_parameters(cls):
        return []

    @classmethod
    def constraint_name(cls):
        return "SPARQLTargetType"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_SPARQLTargetType

    def evaluate(self, target_graph: GraphLike, focus_value_nodes: typing.Dict, _evaluation_path: List):
        raise NotImplementedError()

    def find_targets(self, data_graph):
        return NotImplementedError()


class BoundSPARQLTargetType(BoundSHACLTargetType):
    __slots__ = ('query_helper',)

    def __init__(self, target_type, target_declaration, shape):
        super(BoundSPARQLTargetType, self).__init__(target_type, target_declaration, shape)
        params = self.target_type.parameters
        SPARQLQueryHelper = get_query_helper_cls()
        self.query_helper = SPARQLQueryHelper(
            self.target_declaration, self.target_type.node, self.target_type.select, params
        )
        # Setting self.shape into QueryHelper automatically applies query_helper.bind_params and bind_messages
        self.query_helper.collect_prefixes()

    def find_targets(self, data_graph):
        qh = self.query_helper
        bind_vals = qh.param_bind_map
        # Don't pre-bind variables here!
        # init_binds, sparql_text = qh.pre_bind_variables(self.target_type.node, extravars=bind_vals.keys())
        # init_binds.update(bind_vals)
        sparql_text = qh.apply_prefixes(qh.select_text)
        results = data_graph.query(sparql_text, initBindings=bind_vals)
        return results


class SPARQLTargetType(SHACLTargetType):
    __slots__ = ('select',)

    def __init__(self, t_node, sg):
        super(SPARQLTargetType, self).__init__(t_node, sg)
        selects = list(self.sg.objects(self.node, SH_select))
        num_selects = len(selects)
        if num_selects > 1:
            raise ConstraintLoadError(
                "SPARQLTargetType cannot have more than one value for sh:select.",
                "https://www.w3.org/TR/shacl-af/#SPARQLTargetType",
            )
        elif num_selects < 1:
            raise ConstraintLoadError(
                "SPARQLTargetType must have a value for sh:select.",
                "https://www.w3.org/TR/shacl-af/#SPARQLTargetType",
            )
        self.select = selects[0]

    def bind(self, shape, target_declaration):
        return BoundSPARQLTargetType(self, target_declaration, shape)


def gather_target_types(shacl_graph: 'ShapesGraph') -> Sequence[Union['SHACLTargetType', 'SPARQLTargetType']]:
    """

    :param shacl_graph:
    :type shacl_graph: ShapesGraph
    :return:
    :rtype: [SHACLTargetType]
    """
    all_target_types: List[Union['SHACLTargetType', 'SPARQLTargetType']] = []
    sub_targets = set(shacl_graph.subjects(RDFS_subClassOf, SH_Target))

    # remove these two which are the known native types in shacl.ttl
    sub_targets = sub_targets.difference({SH_JSTarget, SH_SPARQLTarget})

    if shacl_graph.js_enabled:
        from pyshacl.extras.js.target import JSTargetType

        use_js: Union[bool, Type] = JSTargetType
    else:
        use_js = False

    for s in sub_targets:
        types = set(shacl_graph.objects(s, RDF_type))
        found = False
        if SH_SPARQLTargetType in types:
            all_target_types.append(SPARQLTargetType(s, shacl_graph))
            found = True
        if SH_JSTargetType in types:
            found = True
            if use_js:
                all_target_types.append(JSTargetType(s, shacl_graph))
            else:
                pass  # JS Mode is not enabled. Silently ignore JSTargetTypes
        if not found:
            warn(Warning("The only SHACLTargetType currently implemented is SPARQLTargetType."))

    return all_target_types


def apply_target_types(tts: Sequence):
    for t in tts:
        t.apply()
