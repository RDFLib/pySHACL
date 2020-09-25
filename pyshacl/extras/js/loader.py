import typing
from urllib import request
if typing.TYPE_CHECKING:
    from pyduktape2 import DuktapeContext

def get_js_from_web(url: str):
    """

    :param url:
    :type url: str
    :return:
    """
    headers = {'Accept': 'application/javascript, text/javascript, application/ecmascript, text/ecmascript,'
                         'text/plain'}
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
    context.eval_js(contents)
    return
