#
#
import typing
from urllib import request

try:
    import regex
except ImportError:
    import re

    regex = re

if typing.TYPE_CHECKING:
    from pyduktape2 import DuktapeContext

JS_FN_RE1 = regex.compile(rb'function\s+([^ \n]+)\s*\((.*)\)\s*\{', regex.MULTILINE | regex.IGNORECASE)
JS_FN_RE2 = regex.compile(
    rb'(?:let|const|var)\s+([^ \n]+)\s*=\s*function\s*\((.*)\)\s*\{', regex.MULTILINE | regex.IGNORECASE
)


def get_js_from_web(url: str):
    """

    :param url:
    :type url: str
    :return:
    """
    headers = {
        'Accept': 'application/javascript, text/javascript, application/ecmascript, text/ecmascript,' 'text/plain'
    }
    r = request.Request(url, headers=headers)
    resp = request.urlopen(r)
    code = resp.getcode()
    if not (200 <= code <= 210):
        raise RuntimeError("Cannot pull JS Library URL from the web: {}, code: {}".format(url, str(code)))
    return resp


def get_js_from_file(filepath: str):
    if filepath.startswith("file://"):
        filepath = filepath[7:]
    f = open(filepath, "rb")
    return f


def extract_functions(content):
    fns = {}
    matches1 = regex.findall(JS_FN_RE1, content)
    for m in matches1:
        name = m[0].decode('utf-8')
        params = tuple(p.strip().decode('utf-8') for p in m[1].split(b',') if p)
        fns[name] = params
    matches2 = regex.findall(JS_FN_RE2, content)
    for m in matches2:
        name = m[0].decode('utf-8')
        params = tuple(p.strip().decode('utf-8') for p in m[1].split(b',') if p)
        fns[name] = params
    return fns


def load_into_context(context: 'DuktapeContext', location: str):
    f = None
    try:
        if location.startswith("http:") or location.startswith("https:"):
            f = get_js_from_web(location)
        else:
            f = get_js_from_file(location)
        contents = f.read()
    finally:
        if f:
            f.close()
    fns = extract_functions(contents)
    context.eval_js(contents)
    return fns
