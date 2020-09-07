from logging import Logger
from typing import Union

from rdflib import Literal, URIRef

from .consts import SH_datatype, SH_optional, SH_order, SH_path
from .errors import ConstraintLoadError, ReportableRuntimeError
from .shape import Shape


class SHACLParameter(Shape):
    __slots__ = ("datatype", "param_order", "optional")

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
            # TODO: check order is a literal with type Int
            self.param_order = int(orders[0])
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
