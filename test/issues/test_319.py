# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/319
"""

import gc
import io
import threading
from contextlib import redirect_stderr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from rdflib import OWL, RDF, URIRef

from pyshacl.rdfutil.load import load_from_source


ROOT_TTL = b"""\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
<http://example.test/root> a owl:Ontology ;
    owl:imports <IMPORT_URL> .
"""

IMPORTED_TTL = b"""\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
<http://example.test/imported> a owl:Ontology .
"""


class Issue319Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/root.ttl":
            body = self.server.root_body
        elif self.path == "/import.ttl":
            body = IMPORTED_TTL
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/turtle")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def test_319_http_owl_imports_do_not_leave_closed_response_finalizers():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Issue319Handler)
    host, port = server.server_address
    root_url = f"http://{host}:{port}/root.ttl"
    import_url = f"http://{host}:{port}/import.ttl"
    server.root_body = ROOT_TTL.replace(b"IMPORT_URL", import_url.encode("ascii"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    stderr = io.StringIO()
    try:
        with redirect_stderr(stderr):
            graph = load_from_source(root_url, do_owl_imports=True)
            assert (URIRef("http://example.test/imported"), RDF.type, OWL.Ontology) in graph
            del graph
            gc.collect()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    stderr_text = stderr.getvalue()
    assert "Exception ignored while finalizing file" not in stderr_text
    assert "I/O operation on closed file" not in stderr_text
