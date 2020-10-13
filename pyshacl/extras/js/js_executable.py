#
#
import typing
from rdflib import Literal
from pyshacl.consts import SH, SH_jsLibrary, SH_jsFunctionName
from pyshacl.errors import ConstraintLoadError
from .context import SHACLJSContext

if typing.TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph

SH_jsLibraryURL = SH.term('jsLibraryURL')


class JSExecutable(object):
    __slots__ = ("sg", "node", "fn_name", "libraries")

    def __new__(cls, shapes_graph: 'ShapesGraph', node):
        return super(JSExecutable, cls).__new__(cls)

    def __init__(self, shapes_graph: 'ShapesGraph', node):
        self.node = node
        self.sg = shapes_graph
        fn_names = set(shapes_graph.objects(node, SH_jsFunctionName))
        if len(fn_names) < 1:
            raise ConstraintLoadError(
                "At least one sh:jsFunctionName must be present on a JS Executable.",
                "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
            )
        elif len(fn_names) > 1:
            raise ConstraintLoadError(
                "At most one sh:jsFunctionName can be present on a JS Executable.",
                "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
            )
        fn_name = next(iter(fn_names))
        if not isinstance(fn_name, Literal):
            raise ConstraintLoadError(
                "sh:jsFunctionName must be an RDF Literal with type xsd:string.",
                "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
            )
        else:
            fn_name = str(fn_name)
        self.fn_name = fn_name
        library_defs = shapes_graph.objects(node, SH_jsLibrary)
        seen_library_defs = []
        libraries = {}
        for libn in library_defs:
            # Library defs can only do two levels deep for now.
            # TODO: Make this recursive somehow to some further depth
            if libn in seen_library_defs:
                continue
            if isinstance(libn, Literal):
                raise ConstraintLoadError(
                    "sh:jsLibrary must not have a value that is a Literal.",
                    "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                )
            seen_library_defs.append(libn)
            jsLibraryURLs = list(shapes_graph.objects(libn, SH_jsLibraryURL))
            if len(jsLibraryURLs) > 0:
                libraries[libn] = libraries.get(libn, [])
            for u in jsLibraryURLs:
                if not isinstance(u, Literal):
                    raise ConstraintLoadError(
                        "sh:jsLibraryURL must have a value that is a Literal.",
                        "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                    )
                libraries[libn].append(str(u))
            library_defs2 = shapes_graph.objects(libn, SH_jsLibrary)
            for libn2 in library_defs2:
                if libn2 in seen_library_defs:
                    continue
                if isinstance(libn2, Literal):
                    raise ConstraintLoadError(
                        "sh:jsLibrary must not have a value that is a Literal.",
                        "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                    )
                seen_library_defs.append(libn2)
                jsLibraryURLs2 = list(shapes_graph.objects(libn2, SH_jsLibraryURL))
                if len(jsLibraryURLs2) > 0:
                    libraries[libn2] = libraries.get(libn2, [])
                for u2 in jsLibraryURLs2:
                    if not isinstance(u2, Literal):
                        raise ConstraintLoadError(
                            "sh:jsLibraryURL must have a value that is a Literal.",
                            "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                        )
                    libraries[libn2].append(str(u2))
        self.libraries = libraries

    def execute(self, datagraph, args_map, *args, **kwargs):
        ctx = SHACLJSContext(self.sg, datagraph, **kwargs)
        for lib_node, lib_urls in self.libraries.items():
            for lib_url in lib_urls:
                ctx.load_js_library(lib_url)
        fn_args = ctx.get_fn_args(self.fn_name, args_map)
        return ctx.run_js_function(self.fn_name, fn_args)
