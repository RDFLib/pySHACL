from decimal import Decimal
from logging import Logger
from typing import Union

from rdflib import Literal, URIRef

from .consts import SH_datatype, SH_nodeKind, SH_optional, SH_order, SH_path
from .errors import ConstraintLoadError, ReportableRuntimeError
from .shape import Shape


class SHACLParameter(Shape):
    __slots__ = ("nodekind", "datatype", "param_order", "optional")

    def __init__(self, sg, param_node, path=None, logger: Union[Logger, None] = None):
        """
        :type sg: ShapesGraph
        :type param_node: URIRef
        """
        if path is None:
            paths = list(sg.objects(param_node, SH_path))
            if len(paths) < 1:
                path = URIRef("http://")  # todo: is this a blank path?
            elif len(paths) > 1:
                raise ConstraintLoadError(
                    "sh:parameter cannot have more than one value for sh:path.",
                    "https://www.w3.org/TR/shacl-af/#functions-example",
                )
            else:
                path = paths[0]
        super(SHACLParameter, self).__init__(sg, param_node, p=True, path=path, logger=logger)

        nodekinds = list(sg.objects(self.node, SH_nodeKind))
        if len(nodekinds) < 1:
            self.nodekind = None
        elif len(nodekinds) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:nodeKind.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            self.nodekind = nodekinds[0]

        datatypes = list(sg.objects(self.node, SH_datatype))
        if len(datatypes) < 1:
            self.datatype = None
        elif len(datatypes) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:datatype.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            self.datatype = datatypes[0]

        orders = list(sg.objects(self.node, SH_order))
        if len(orders) < 1:
            self.param_order = None
        elif len(orders) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:order.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            order = orders[0]
            if not isinstance(order, Literal):
                raise ConstraintLoadError(
                    "sh:order value must be a literal of type Decimal or Integer",
                    "https://www.w3.org/TR/shacl-af/#functions-example",
                )
            if isinstance(order.value, Decimal):
                order = order.value
            elif isinstance(order.value, int):
                order = Decimal(order.value)
            elif isinstance(order.value, float):
                order = Decimal(str(order.value))
            else:
                raise ConstraintLoadError(
                    "sh:order value must be a literal of type Decimal or Integer",
                    "https://www.w3.org/TR/shacl-af/#functions-example",
                )
            self.param_order = order
        optionals = list(sg.objects(self.node, SH_optional))
        if len(optionals) < 1:
            self.optional = False
        elif len(optionals) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:optional.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            o = optionals[0]
            if not (isinstance(o, Literal) and isinstance(o.value, bool)):
                # TODO:coverage: we don't have any tests for invalid constraints
                raise ConstraintLoadError(
                    "A sh:parameter value for sh:optional must be a valid RDF Literal of type xsd:boolean.",
                    "https://www.w3.org/TR/shacl/#constraint-components-parameters",
                )
            self.optional = bool(optionals[0])

    def __str__(self):
        name = str(self.node)
        return "<Parameter {}>".format(name)

    @property
    def localname(self):
        path = self.path()
        hash_index = path.find('#')
        if hash_index > 0:
            ending = path[hash_index + 1 :]
            return ending
        right_slash_index = path.rfind('/')
        if right_slash_index > 0:
            # TODO:coverage: No test for this case where path has a forwardslash separator
            ending = path[right_slash_index + 1 :]
            return ending
        raise ReportableRuntimeError("Cannot get a local name for {}".format(path))
