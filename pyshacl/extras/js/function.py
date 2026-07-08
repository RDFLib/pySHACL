#
#
from __future__ import annotations

import functools
import typing
from typing import Dict, Union

from rdflib.plugins.sparql.sparql import SPARQLError

from ...errors import ReportableRuntimeError
from ...functions.shacl_function import SHACLFunction
from ...graph_abstraction import has_oxigraph, to_ox, to_rdf
from .js_executable import JSExecutable

if typing.TYPE_CHECKING:
    from ...graph_abstraction import DataGraph
    from ...shapes_graph import ShapesGraph
if has_oxigraph:
    from pyoxigraph import BlankNode as ox_BlankNode
    from pyoxigraph import NamedNode as ox_NamedNode
    from pyoxigraph import Triple as ox_Triple
else:
    ox_BlankNode = None
    ox_NamedNode = None
    ox_Triple = None


class JSFunction(SHACLFunction):
    __slots__ = ('js_exe',)

    def __init__(self, fn_node, shapes_graph: 'ShapesGraph'):
        super(JSFunction, self).__init__(fn_node, shapes_graph)
        self.js_exe = JSExecutable(shapes_graph, fn_node)

    def execute(self, g, *args):
        params = self.get_params_in_order()
        if len(args) != len(params):
            raise ReportableRuntimeError("Got incorrect number of arguments for JSFunction {}.".format(self.node))
        args_map = {}
        for i, p in enumerate(params):
            arg = args[i]
            ln = p.localname
            if arg is None and p.optional is False:
                raise ReportableRuntimeError("Got NoneType for Non-optional argument {}.".format(ln))
            args_map[ln] = arg
        results = self.js_exe.execute(g, args_map, mode="function", return_type=self.rtype)
        res = results['_result']
        return res

    def execute_from_sparql(self, e, ctx):
        if not e.expr:
            raise SPARQLError("Nothing given to SPARQLFunction.")
        params = self.get_params_in_order()
        num_params = len(params)
        if len(e.expr) > num_params:
            raise SPARQLError("Too many parameters passed to SPARQLFunction.")
        elif len(e.expr) < num_params:
            raise SPARQLError("Too few parameters passed to SPARQLFunction.")
        args_map = {str(var): val for var, val in ctx.ctx.initBindings.items()}
        args_map.update({str(var): val for var, val in ctx.ctx.bindings.items()})
        g = ctx.ctx.graph
        for i, var in enumerate(e.expr):
            var_val = ctx[var]
            param_name = params[i].localname
            args_map[param_name] = var_val
        results = self.js_exe.execute(g, args_map, mode="function", return_type=self.rtype)
        res = results['_result']
        return res

    def execute_oxigraph(
        self,
        g: 'DataGraph',
        args_map: Dict[str, Union[ox_NamedNode, ox_BlankNode, ox_Triple]],
    ):
        """Run the SHACL-JS function body and return a pyoxigraph term."""
        rdf_args_map = {k: to_rdf(v) if v is not None else None for k, v in args_map.items()}
        results = self.js_exe.execute(g, rdf_args_map, mode="function", return_type=self.rtype)
        res = results['_result']
        if res is None:
            return None
        return to_ox(res)

    def execute_from_sparql_oxigraph(
        self,
        g: 'DataGraph',
        *args: Union[ox_NamedNode, ox_BlankNode, ox_Triple],
    ):
        """Oxigraph custom-function callback: evaluated argument terms in, one RDF term out."""
        if not g.is_oxigraph:
            raise ReportableRuntimeError("execute_from_sparql_oxigraph requires an Oxigraph-backed DataGraph.")
        params = self.get_params_in_order()
        num_params = len(params)
        num_args = len(args)
        if num_args > num_params:
            raise ValueError("Too many parameters passed to JSFunction {}.".format(self.node))
        if num_args < num_params:
            raise ValueError("Too few parameters passed to JSFunction {}.".format(self.node))
        args_map: Dict[str, Union[ox_NamedNode, ox_BlankNode, ox_Triple]] = {}
        for i, p in enumerate(params):
            ox_arg = args[i]
            ln = p.localname
            if ox_arg is None and p.optional is False:
                raise ReportableRuntimeError("Got NoneType for Non-optional argument {}.".format(ln))
            args_map[ln] = ox_arg
        return self.execute_oxigraph(g, args_map)

    def apply(self, g: 'DataGraph'):
        super(JSFunction, self).apply(g)
        if has_oxigraph:
            g.register_custom_function(
                self.node,
                self.execute_from_sparql,
                functools.partial(self.execute_from_sparql_oxigraph, g),
                True,
                True,
            )
        else:
            g.register_custom_function(self.node, self.execute_from_sparql, None, True, True)

    def unapply(self, g: 'DataGraph'):
        super(JSFunction, self).unapply(g)
        if has_oxigraph:
            g.unregister_custom_function(self.node, self.execute_from_sparql, self.execute_from_sparql_oxigraph)
        else:
            g.unregister_custom_function(self.node, self.execute_from_sparql, None)
