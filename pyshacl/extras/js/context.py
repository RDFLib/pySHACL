import pprint
from decimal import Decimal
from typing import Union

import pyduktape2
from pyduktape2 import JSProxy
from rdflib import BNode, Literal, URIRef
from rdflib.namespace import XSD

from pyshacl.errors import ReportableRuntimeError

from . import load_into_context


class URIRefNativeWrapper(object):
    inner_type = "URIRef"

    def __init__(self, uri):
        if isinstance(uri, URIRef):
            self.inner = uri
        else:
            self.inner = URIRef(uri)

    @property
    def uri(self):
        return str(self.inner)

    def __eq__(self, other):
        return self.inner.__eq__(other.inner)

    def __repr__(self):
        inner_repr = repr(self.inner)
        return "URIRefNativeWrapper({})".format(inner_repr)


class BNodeNativeWrapper(object):
    inner_type = "BNode"

    def __init__(self, id_):
        if isinstance(id_, BNode):
            self.inner = id_
        else:
            self.inner = BNode(id_ or None)

    @property
    def identifier(self):
        return str(self.inner)

    def __eq__(self, other):
        return self.inner.__eq__(other.inner)

    def __repr__(self):
        inner_repr = repr(self.inner)
        return "BNodeNativeWrapper({})".format(inner_repr)


class LiteralNativeWrapper(object):
    inner_type = "Literal"

    def __init__(self, lexical, dtype=None, lang=None):
        if isinstance(lexical, Literal):
            self.inner = lexical
        else:
            if isinstance(dtype, URIRefNativeWrapper):
                dtype = dtype.inner
            self.inner = Literal(lexical, lang=lang, datatype=dtype)

    @property
    def lexical(self):
        return self.inner.value

    @property
    def language(self):
        return self.inner.language

    @property
    def datatype(self):
        return self.inner.datatype

    def __eq__(self, other):
        return self.inner.__eq__(other.inner)

    def __repr__(self):
        inner_repr = repr(self.inner)
        return "LiteralNativeWrapper({})".format(inner_repr)


class GraphNativeWrapper(object):
    def __init__(self, g):
        self.inner = g


class IteratorNativeWrapper(object):
    def __init__(self, it):
        self.it = it

    def it_next(self):
        return next(self.it)


def _make_uriref(args):
    uri = getattr(args, '0')
    return URIRefNativeWrapper(uri)


def _make_bnode(args):
    id_ = getattr(args, '0')
    return BNodeNativeWrapper(id_)


def _make_literal(args):
    lexical, dtype, lang = getattr(args, '0'), getattr(args, '1'), getattr(args, '2')
    if isinstance(dtype, JSProxy):
        as_native = getattr(dtype, '_native', None)
        if as_native is not None:
            dtype = as_native
    return LiteralNativeWrapper(lexical, dtype, lang)


def _native_node_equals(args):
    this, other = getattr(args, '0'), getattr(args, '1')
    if isinstance(this, (URIRefNativeWrapper, BNodeNativeWrapper, LiteralNativeWrapper)):
        this = this.inner
    if isinstance(other, (URIRefNativeWrapper, BNodeNativeWrapper, LiteralNativeWrapper)):
        other = other.inner
    return this == other


def _native_graph_find(args):
    # args are: g, s, p, o
    triple = [getattr(args, '0'), getattr(args, '1'), getattr(args, '2'), getattr(args, '3')]
    wrapped_triples = []
    for t in triple:
        if isinstance(t, (GraphNativeWrapper, URIRefNativeWrapper, BNodeNativeWrapper, LiteralNativeWrapper)):
            wrapped_triples.append(t.inner)
        else:
            wrapped_triples.append(t)
    g, s, p, o = wrapped_triples[:4]
    it = iter(g.triples((s, p, o)))
    return IteratorNativeWrapper(it)


def _native_iterator_next(args):
    arg0 = getattr(args, "0")
    if isinstance(arg0, IteratorNativeWrapper):
        arg0 = arg0.it
    try:
        spo_list = next(arg0)
    except StopIteration:
        return None
    wrapped_list = []
    for item in spo_list[:3]:
        if isinstance(item, URIRef):
            wrapped_list.append(URIRefNativeWrapper(item))
        elif isinstance(item, BNode):
            wrapped_list.append(BNodeNativeWrapper(item))
        elif isinstance(item, Literal):
            wrapped_list.append(LiteralNativeWrapper(item))
        else:
            raise RuntimeError("Bad item returned from iterator!")
    return wrapped_list


def _pprint(args):
    arg0 = getattr(args, '0')
    pprint.pprint(arg0)


printJs = '''\
function pprint(o) {
    return _pprint({'0': o});
}
'''

namedNodeJs = '''\
function NamedNode(uri, _native) {
    this.uri = uri;
    if (! _native) {
        _native = _make_uriref({'0': uri});
    }
    this._native = _native;
}
NamedNode.from_native = function(native) {
    var uri = native.uri;
    return new NamedNode(uri, native);
}
NamedNode.prototype.toPython = function() { return this._native; }
NamedNode.prototype.toString = function() { return "NamedNode("+this.uri+")"; }
NamedNode.prototype.isURI = function() { return true; }
NamedNode.prototype.isBlankNode = function() { return false; }
NamedNode.prototype.isLiteral = function() { return false; }
NamedNode.prototype.equals = function(other) {
    if (other.constructor && other.constructor === NamedNode) {
        return _native_node_equals({"0": this._native, "1": other._native});
    }
    return false;
}
'''

blankNodeJs = '''\
function BlankNode(id, _native) {
    this.id = id || null;
    if (! _native) {
        _native = _make_bnode({'0': id});
    }
    this._native = _native;
}
BlankNode.from_native = function(native) {
    var id = native.identifier;
    return new BlankNode(id, native);
}
BlankNode.prototype.toPython = function() { return this._native; }
BlankNode.prototype.toString = function() { return "BlankNode("+this.id+")"; }
BlankNode.prototype.isURI = function() { return false; }
BlankNode.prototype.isBlankNode = function() { return true; }
BlankNode.prototype.isLiteral = function() { return false; }
BlankNode.prototype.equals = function(other) {
    if (other.constructor && other.constructor === BlankNode) {
        return _native_node_equals({"0": this._native, "1": other._native});
    }
    return false;
}
'''

literalJs = '''\
function Literal(lex, languageOrDatatype, _native) {
    this.lex = lex;
    var ndict;
    if (languageOrDatatype.isURI && languageOrDatatype.isURI()) {
        this.language = "";  // Language cannot be null, be empty string
        this.datatype = languageOrDatatype;
        ndict = {'0': lex, '1': languageOrDatatype, '2': null};
    } else {
        var _lang = ""+languageOrDatatype;
        this.language = _lang;
        this.datatype = new NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#langString");
        ndict = {'0': lex, '1': null, '2': languageOrDatatype};
    }
    if (! _native) {
        _native = _make_literal(ndict);
    }
    this._native = _native;
}
Literal.from_native = function(native) {
    var lex = native.lexical;
    var languageOrDatatype;
    var lang = native.language;
    var dt = native.datatype;
    if (lang) {
        languageOrDatatype = ""+lang;
    } else if (dt) {
        languageOrDatatype = new NamedNode(dt);
    } else {
        languageOrDatatype = new NamedNode("http://www.w3.org/2001/XMLSchema#string");
    }
    return new Literal(lex, languageOrDatatype, native);
}
Literal.prototype.toPython = function() { return this._native; }
Literal.prototype.toString = function() { return "Literal("+this.lex+", dt="+this.datatype+", lang='"+this.language+"')"; }
Literal.prototype.isURI = function() { return false; }
Literal.prototype.isBlankNode = function() { return false; }
Literal.prototype.isLiteral = function() { return true; }
Literal.prototype.equals = function(other) {
    if (other.constructor && other.constructor === Literal) {
        return _native_node_equals({'0': this._native, '1': other._native});
    }
    return false;
}
'''

termFactoryJs = '''\
function TermFactoryFactory() {
}
TermFactoryFactory.prototype.namedNode = function(uri) { return new NamedNode(uri); }
TermFactoryFactory.prototype.blankNode = function(id) { return new BlankNode(id); }
TermFactoryFactory.prototype.literal = function(lex, languageOrDatatype) { return new Literal(lex, languageOrDatatype); }
var TermFactory = new TermFactoryFactory();
'''

graphJs = '''\
function Triple(s, p, o) {
    this.subject = s;
    this.predicate = p;
    this.object = o;
}
function Iterator() {
    this._native = null;
    this.closed = false;
}
Iterator.from_native = function(native) {
    var i = new Iterator();
    i._native = native;
    return i;
}
Iterator.prototype.next = function() {
    if (this.closed) {
        1/0; //exception
    }
    if (this._native === null) {
        return null;
    }
    var bits = _native_iterator_next({"0": this._native});
    if (bits === null) {
        //This is the end of the iteration
        return null;
    }
    var converted_bits = [];
    for (var i=0; i<3; i++) {
        var b = bits[i];
        var inner_type = b.inner_type;
        if (inner_type === "URIRef") {
            converted_bits[i] = NamedNode.from_native(b);
        } else if (inner_type === "BNode") {
            converted_bits[i] = BlankNode.from_native(b);
        } else if (inner_type === "Literal") {
            converted_bits[i] = Literal.from_native(b);
        } else {
            1/0; //exception
        }
    }
    return new Triple(converted_bits[0], converted_bits[1], converted_bits[2]);
}
Iterator.prototype.close = function() {
    if (this.closed) { return; }
    this.closed = true;
    this._native = null;
}
Iterator.prototype.toPython = function() { return this._native; }
function Graph(_native) {
    this._native = _native;
}
Graph.prototype.toPython = function() { return this._native; }
Graph.prototype.find = function(s, p, o) {
    if (this._native === null) {
        return null;
    }
    if (s && s.hasOwnProperty('_native')) { s = s._native; }
    if (p && p.hasOwnProperty('_native')) { p = p._native; }
    if (o && o.hasOwnProperty('_native')) { o = o._native; }
    var native_it = _native_graph_find({'0': this._native, '1': s, '2': p, '3': o});
    var it = Iterator.from_native(native_it);
    return it;
}
'''


class SHACLJSContext(object):
    __slots__ = ("context", "fns")

    def __init__(self, data_graph, *args, shapes_graph=None, **kwargs):
        context = pyduktape2.DuktapeContext()
        context.set_globals(
            _pprint=_pprint,
            _make_uriref=_make_uriref,
            _make_bnode=_make_bnode,
            _make_literal=_make_literal,
            _native_node_equals=_native_node_equals,
            _native_iterator_next=_native_iterator_next,
            _native_graph_find=_native_graph_find,
        )
        context.eval_js(printJs)
        context.eval_js(termFactoryJs)
        context.eval_js(namedNodeJs)
        context.eval_js(blankNodeJs)
        context.eval_js(literalJs)
        context.eval_js(graphJs)

        context.set_globals(_native_data_graph=GraphNativeWrapper(data_graph))
        if shapes_graph is not None:
            context.set_globals(_native_shapes_graph=GraphNativeWrapper(shapes_graph))
        else:
            context.set_globals(_native_shapes_graph=None)
        context.eval_js('''var $data = new Graph(_native_data_graph);\n''')
        if shapes_graph is not None:
            context.eval_js('''var $shapes = new Graph(_native_shapes_graph);\n''')
        else:
            context.eval_js('''var $shapes;\n''')  # leave $shapes undefined
        context.set_globals(*args, **kwargs)

        self.context = context
        self.fns = {}

    def load_js_library(self, library: str):
        fns = load_into_context(self.context, library)
        self.fns.update(fns)

    @classmethod
    def build_results_as_constraint(cls, res):
        if isinstance(res, JSProxy):
            try:
                return res.toPython()
            except AttributeError:
                pass
            # this means its a JS Array or Object
            keys = list(iter(res))
            if len(keys) < 1:
                res = []
            else:
                first_key = keys[0]
                if isinstance(first_key, JSProxy):
                    # res is an array of objects
                    new_res = []
                    for k in keys:
                        try:
                            new_res.append(k.toPython())
                            continue
                        except AttributeError:
                            pass

                        v = getattr(k, 'value', None)
                        m = getattr(k, 'message', None)
                        p = getattr(k, 'path', None)

                        if v is not None:
                            try:
                                v = v.toPython()
                            except AttributeError:
                                pass
                        if v is not None and hasattr(v, 'inner'):
                            v = v.inner

                        if p is not None:
                            try:
                                p = p.toPython()
                            except AttributeError:
                                pass
                        if p is not None and hasattr(p, 'inner'):
                            p = p.inner
                        r = {'value': v, 'message': m, 'path': p}
                        new_res.append(r)
                    return new_res
                try:
                    getattr(res, first_key)
                    new_res = {}
                    for k in keys:
                        v = getattr(res, k, None)
                        if v is not None:
                            try:
                                v = v.toPython()
                            except AttributeError:
                                pass
                        if v is not None and hasattr(v, 'inner'):
                            v = v.inner
                        new_res[k] = v
                    return new_res
                except AttributeError:
                    # This must be an array of something else
                    res = keys
        elif isinstance(res, (Literal, URIRef, BNode)):
            pass
        elif isinstance(res, Decimal):
            res = Literal(res, datatype=XSD['decimal'])
        elif isinstance(res, (int, float, str, bytes, bool)):
            res = Literal(res)
        return res

    @classmethod
    def build_results_as_construct(cls, res):
        if isinstance(res, JSProxy):
            try:
                return res.toPython()
            except AttributeError:
                pass
            # this means its a JS Array or Object
            keys = list(iter(res))
            if len(keys) < 1:
                res = []
            else:
                first_key = keys[0]
                if isinstance(first_key, JSProxy):
                    # res is an array of objects or array of arrays
                    new_res = []
                    for k in keys:
                        try:
                            new_res.append(k.toPython())
                            continue
                        except AttributeError:
                            pass
                        subkeys = list(iter(k))
                        if len(subkeys) < 1:
                            new_res.append([])
                        else:
                            first_subkey = subkeys[0]
                            if isinstance(first_subkey, JSProxy):
                                if len(subkeys) >= 3:
                                    # res is an array of arrays
                                    this_s = subkeys[0]
                                    this_p = subkeys[1]
                                    this_o = subkeys[2]
                                else:
                                    raise ReportableRuntimeError(
                                        "JS Function returned incorrect number of items in the array."
                                    )
                            else:
                                this_s = getattr(k, 'subject', None)
                                this_p = getattr(k, 'predicate', None)
                                this_o = getattr(k, 'object', None)
                            try:
                                this_s = this_s.toPython()
                            except AttributeError:
                                pass
                            if this_s is not None and hasattr(this_s, 'inner'):
                                this_s = this_s.inner
                            try:
                                this_p = this_p.toPython()
                            except AttributeError:
                                pass
                            if this_p is not None and hasattr(this_p, 'inner'):
                                this_p = this_p.inner
                            try:
                                this_o = this_o.toPython()
                            except AttributeError:
                                pass
                            if this_o is not None and hasattr(this_o, 'inner'):
                                this_o = this_o.inner
                            new_res.append((this_s, this_p, this_o))
                    return new_res
                else:
                    # a JS Rules function must return an array of arrays, or array of objects
                    # otherwise, it does nothing!
                    return []
        return res

    @classmethod
    def build_results_as_target(cls, res):
        if isinstance(res, JSProxy):
            try:
                return res.toPython()
            except AttributeError:
                pass
            # this means its a JS Array or Object
            keys = list(iter(res))
            if len(keys) < 1:
                res = []
            else:
                first_key = keys[0]
                if isinstance(first_key, JSProxy):
                    # res is an array of objects or array of arrays
                    new_res = []
                    for k in keys:
                        try:
                            k = k.toPython()
                        except AttributeError:
                            pass
                        if k is not None and hasattr(k, 'inner'):
                            k = k.inner
                        new_res.append(k)
                    return new_res
                else:
                    # a JS Target function must return an array of Nodes
                    # otherwise, it does nothing!
                    return []
        return res

    @classmethod
    def build_results_as_shacl_function(cls, res, return_type=None):
        if isinstance(res, JSProxy):
            try:
                return res.toPython()
            except AttributeError:
                return None
        elif isinstance(res, (Literal, URIRef, BNode)):
            pass
        elif return_type is not None and isinstance(res, (int, float)):
            lex = str(res)
            res = Literal(lex, datatype=return_type, normalize=False)
        elif isinstance(res, (float, Decimal)):
            res = Literal(str(res), datatype=XSD['decimal'])
        elif isinstance(res, bool):
            res = Literal(res, datatype=XSD['boolean'])
        elif isinstance(res, (int, float, str, bytes, bool)):
            res = Literal(res, datatype=return_type, normalize=False)
        return res

    def get_fn_args(self, fn_name, args_map):
        c = self.context
        try:
            fn = c.get_global(fn_name)
        except BaseException as e:
            print(e)
            raise
        if fn is None:
            raise ReportableRuntimeError("JS Function {} cannot be found in the loaded files.".format(fn_name))
        if fn_name not in self.fns:
            raise ReportableRuntimeError("JS Function {} args cannot be determined. Bad JS structure?".format(fn_name))
        known_fn_args: tuple = self.fns[fn_name]
        needed_args = []
        for k, v in args_map.items():
            look_for = "$" + str(k)
            positions = []
            start = 0
            while True:
                try:
                    pos = known_fn_args.index(look_for, start)
                    positions.append(pos)
                except ValueError:
                    break
                start = pos + 1
            if not positions:
                continue
            for p in positions:
                needed_args.append((p, k, v))
        for i, a in enumerate(known_fn_args):
            if a.startswith("$"):
                a = a[1:]
            if a not in args_map:
                needed_args.append((i, a, None))
        needed_args = [v for p, k, v in sorted(needed_args)]
        return needed_args

    def run_js_function(self, fn_name, args, returns: Union[list, None] = None):
        if returns is None:
            returns = []
        c = self.context
        args_string = ""
        bind_dict = {}
        preamble = ""
        for i, a in enumerate(args):
            arg_name = "fn_arg_" + str(i + 1)
            if isinstance(a, URIRef):
                wrapped_a: Union[URIRefNativeWrapper, BNodeNativeWrapper, LiteralNativeWrapper] = URIRefNativeWrapper(
                    a
                )
                native_name = "_{}_native".format(arg_name)
                preamble += "var {} = NamedNode.from_native({});\n".format(arg_name, native_name)
                bind_dict[native_name] = wrapped_a
            elif isinstance(a, BNode):
                wrapped_a = BNodeNativeWrapper(a)
                native_name = "_{}_native".format(arg_name)
                preamble += "var {} = BlankNode.from_native({});\n".format(arg_name, native_name)
                bind_dict[native_name] = wrapped_a
            elif isinstance(a, Literal):
                wrapped_a = LiteralNativeWrapper(a)
                native_name = "_{}_native".format(arg_name)
                preamble += "var {} = Literal.from_native({});\n".format(arg_name, native_name)
                bind_dict[native_name] = wrapped_a
            elif a is None:  # this is how we set an undefined variable
                preamble += "var {};\n".format(arg_name)
            else:
                bind_dict[arg_name] = a

            args_string = args_string + arg_name + ","
        c.set_globals(**bind_dict)
        args_string = args_string.rstrip(',')
        c.eval_js(preamble)
        res = c.eval_js("\n{}({});".format(fn_name, args_string))
        returns_dict = {}
        for r in returns:
            try:
                returns_dict[r] = c.get_global(r)
            except BaseException as e:
                print(e)
                returns_dict[r] = None
        returns_dict['_result'] = res
        return returns_dict
