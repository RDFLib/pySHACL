#
#
import typing

from rdflib.plugins.sparql.operators import register_custom_function, unregister_custom_function
from rdflib.plugins.sparql.sparql import SPARQLError

from pyshacl.errors import ReportableRuntimeError
from pyshacl.functions.shacl_function import SHACLFunction

from .js_executable import JSExecutable

if typing.TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph


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

    def apply(self, g):
        super(JSFunction, self).apply(g)
        register_custom_function(self.node, self.execute_from_sparql, True, True)

    def unapply(self, g):
        super(JSFunction, self).unapply(g)
        unregister_custom_function(self.node, self.execute_from_sparql)
