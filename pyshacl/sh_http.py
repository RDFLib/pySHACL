# HTTP Server for PySHACL
import os
import sys

try:
    import sanic.application.logo
    from sanic import Request, Sanic
    from sanic.exceptions import InvalidUsage
    from sanic.response import HTTPResponse, JSONResponse, text
    from sanic_cors.extension import CORS
    from sanic_ext import Extend, openapi
except ImportError:
    raise RuntimeError("The optional PySHACL HTTP server components are not installed. See README.md for details.")

from dataclasses import dataclass
from enum import Enum
from textwrap import dedent

from sanic_ext.extensions.openapi import types as openapi_types
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from . import __version__ as pyshacl_version
from . import validate
from .errors import ConstraintLoadError, ReportableRuntimeError, RuleLoadError, ShapeLoadError, ValidationFailure

API_VERSION = "v1"


class InferenceKind(Enum):
    NONE = "none"
    RDFS = "rdfs"
    OWLRL = "owlrl"
    BOTH = "both"


class InputRDFFormat(Enum):
    AUTO = "auto"
    TURTLE = "turtle"
    XML = "xml"
    JSONLD = "json-ld"
    NT = "nt"
    N3 = "n3"


@dataclass
class ValidationRequest:
    data_graph: openapi_types.String(  # type: ignore[valid-type]
        required=True, title="DataGraph", description="The target DataGraph to validate (serialized in an RDF string)"
    )
    shapes_graph: openapi_types.String(  # type: ignore[valid-type]
        required=False,
        nullable=True,
        title="DataGraph",
        description="Your SHACL ShapesGraph (serialized in an RDF string)",
    )
    ontology_graph: openapi_types.String(  # type: ignore[valid-type]
        required=False, nullable=True, title="OntologyGraph", description="Optional ontological definitions graph"
    )
    data_graph_format: openapi_types.String(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default="auto",
        title="DataGraph RDF format",
        description="Optionally specify the RDF format for your DataGraph",
        enum=InputRDFFormat,
    )
    shapes_graph_format: openapi_types.String(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default="auto",
        title="ShapesGraph RDF format",
        description="Optionally specify the RDF format for your ShapesGraph",
        enum=InputRDFFormat,
    )
    ontology_graph_format: openapi_types.String(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default="auto",
        title="OntologyGraph RDF format",
        description="Optionally specify the RDF format for your OntologyGraph",
        enum=InputRDFFormat,
    )
    advanced: openapi_types.Boolean(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default=False,
        title="Advanced",
        description="Enable features from the SHACL Advanced Features spec.",
    )
    inference: openapi_types.String(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default="none",
        title="Pre-Inference",
        description="Set a pre-inference option",
        enum=InferenceKind,
    )
    do_owl_imports: openapi_types.Boolean(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default=False,
        title="Do OWL Imports",
        description="Enable the feature to follow links to import OWL ontologies in Shapes graph and Ontology Graph.",
    )
    allow_infos: openapi_types.Boolean(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default=False,
        title="Allow Infos",
        description="The datagraph will still be considered conformant when encountering constraint failures with "
        "sh:Info level severity.",
    )
    allow_warnings: openapi_types.Boolean(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default=False,
        title="Allow Warnings",
        description="The datagraph will still be considered conformant when encountering constraint failures with "
        "sh:Warning or sh:Info level severity.",
    )
    iterate_rules: openapi_types.Boolean(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default=False,
        title="Iterate Rules",
        description="Continue to execute SHACL Rules until the resulting output graph reaches steady state. "
        "This only works when advanced mode is enabled, and is usually not required.",
    )
    js: openapi_types.String(  # type: ignore[valid-type]
        required=False, nullable=False, default=False, title="JS", description="Enable SHACL-JS validator extension"
    )
    metashacl: openapi_types.Boolean(  # type: ignore[valid-type]
        required=False,
        nullable=False,
        default=False,
        title="MetaSHACL",
        description="Validate your SHACL Shapesfile against the shacl-shacl shapes before validating the datagraph.",
    )


failures_array_ref = openapi.Component(
    openapi_types.Array(
        items=openapi.String(title="ValidationFailure", required=True, nullable=False, format="text/plain"),
        required=False,
        nullable=True,
        description="Optional array of validation errors in text format.",
        format="application/json",
    ),
    name="ValidationFailureArray",
)


@dataclass
class ValidationResponseSimple:
    conforms: openapi_types.Boolean(  # type: ignore[valid-type]
        required=True, title="Conforms", description="The datagraph conforms to the SHACL Shapes"
    )
    validation_report: openapi_types.String(  # type: ignore[valid-type]
        required=False,
        nullable=True,
        title="ValidationReport",
        description="The text representation of the validation report.",
    )
    validation_failures: failures_array_ref  # type: ignore[valid-type]


def make_validation_response_RDF(format, mimetype):
    this_type_ref = openapi.Component(
        openapi_types.String(
            required=True,
            title=f"ValidationReport{format}",
            description=f"The {format} representation of the validation report.",
            format=mimetype,
        ),
        name=f"ValidationReport{format}",
    )
    return openapi.Component(
        openapi_types.Schema(oneOf=[this_type_ref, failures_array_ref], name=f"ValidationResponse{format}"),
        name=f"ValidationResponse{format}",
    )


validation_request_ref = openapi.Component(ValidationRequest)
validation_response_simple_ref = openapi.Component(ValidationResponseSimple)
validation_response_ntriples_ref = make_validation_response_RDF("NTriples", "application/n-triples")
validation_response_json_ld_ref = make_validation_response_RDF("JSONLD", "application/ld+json")
validation_response_xml_ref = make_validation_response_RDF("ApplicationXML", "application/xml")
validation_response_rdf_ref = make_validation_response_RDF("RDFXML", "application/rdf+xml")
validation_response_ttl_ref = make_validation_response_RDF("Turtle", "text/turtle")

ALLOWED_RESPONSE_TYPES = {
    "text/plain": validation_response_simple_ref,
    "application/json": validation_response_simple_ref,
    "application/ld+json": validation_response_json_ld_ref,
    "application/xml": validation_response_xml_ref,
    "application/rdf+xml": validation_response_rdf_ref,
    "text/turtle": validation_response_ttl_ref,
    "application/n-triples": validation_response_ntriples_ref,
}


@openapi.definition(
    summary="Validate",
    description="Send a validation request, consisting of a DataGraph, SHACL shapes graph, and optional parameters.",
    body=RequestBody(
        {"application/json": validation_request_ref},
        required=True,
        description="ValidationRequest body",
    ),
    validate=False,
    response=Response(ALLOWED_RESPONSE_TYPES, status=200),
)
async def sh_validate(request: Request) -> HTTPResponse:
    content_type = "application/json"  # Default content type is the fallback
    content_types = (request.headers.getall("Content-Type"),)
    for c_t in content_types:
        if isinstance(c_t, (list, tuple, set)):
            content_types_array = c_t
        else:
            content_types_array = [c_t]
        for c_t2 in content_types_array:
            split_ct = [p.strip() for p in c_t2.split(",")]
            for c_t3 in split_ct:
                content_type = ([p.strip() for p in c_t3.split(";")][0]).lower()

    accept_type = "text/plain"  # Default return type is the fallback
    accept_types = (request.headers.getall("Accept"),)
    for a_t in accept_types:
        if isinstance(a_t, (list, tuple, set)):
            accept_types_array = a_t
        else:
            accept_types_array = [a_t]
        for a_t2 in accept_types_array:
            split_at = [p.strip() for p in a_t2.split(",")]
            for a_t3 in split_at:
                accept_type = ([p.strip() for p in a_t3.split(";")][0]).lower()

    if content_type != "application/json":
        raise InvalidUsage(
            "Request should be encoded in format application/json in accordance with the OpenAPI schema."
        )
    if accept_type not in ALLOWED_RESPONSE_TYPES.keys():
        raise InvalidUsage("Invalid response type requested.")

    try:
        body = request.json
    except ValueError:
        raise InvalidUsage("Invalid JSON payload.")

    data_graph = body.get("data_graph", None)
    if data_graph is None:
        raise InvalidUsage("DataGraph was not provided.")
    data_graph_format = body.get("data_graph_format", None)
    shapes_graph = body.get("shapes_graph", None)
    shapes_graph_format = body.get("shapes_graph_format", None)
    ontology_graph = body.get("ontology_graph", None)
    ontology_graph_format = body.get("ontology_graph_format", None)
    advanced = body.get("advanced", False)
    inference = body.get("inference", 'none')
    do_owl_imports = body.get("do_owl_imports", False)
    allow_infos = body.get("allow_infos", False)
    allow_warnings = body.get("allow_warnings", False)
    iterate_rules = body.get("iterate_rules", False)
    js = body.get("js", False)
    metashacl = body.get("metashacl", False)

    if str(data_graph_format).lower() == "auto":
        data_graph_format = None
    if str(ontology_graph_format).lower() == "auto":
        ontology_graph_format = None
    if str(shapes_graph_format).lower() == "auto":
        shapes_graph_format = None
    if not advanced:
        iterate_rules = False

    try:
        _conforms, _graph, _text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            ontology_graph=ontology_graph,
            data_graph_format=data_graph_format,
            shacl_graph_format=shapes_graph_format,
            ontology_graph_format=ontology_graph_format,
            advanced=advanced,
            inference=inference,
            do_owl_imports=do_owl_imports,
            js=js,
            metashacl=metashacl,
            allow_infos=allow_infos,
            allow_warnings=allow_warnings,
            iterate_rules=iterate_rules,
            debug=False,
        )
    except ValidationFailure as f:
        err = "Validation Failure: " + str(f)
        simple_resp = ValidationResponseSimple(conforms=None, validation_report=None, validation_failures=[err])
    except RuleLoadError as r:
        err = "Rule Load Error: " + str(r)
        simple_resp = ValidationResponseSimple(conforms=None, validation_report=None, validation_failures=[err])
    except ShapeLoadError as s:
        err = "Shape Load Error: " + str(s)
        simple_resp = ValidationResponseSimple(conforms=None, validation_report=None, validation_failures=[err])
    except ConstraintLoadError as c:
        err = "Constraint Load Error: " + str(c)
        simple_resp = ValidationResponseSimple(conforms=None, validation_report=None, validation_failures=[err])
    except ReportableRuntimeError as s:
        err = "Runtime Error: " + str(s)
        simple_resp = ValidationResponseSimple(conforms=None, validation_report=None, validation_failures=[err])
    except RuntimeError as e:
        err = "Runtime Error: Internal Error"
        import traceback

        # Print this to stderr in the console, not
        sys.stderr.write(f"{repr(e)}\r\n")
        traceback.print_tb(e.__traceback__, file=sys.stderr)
        sys.stderr.flush()
        simple_resp = ValidationResponseSimple(conforms=None, validation_report=None, validation_failures=[err])
    else:
        simple_resp = ValidationResponseSimple(conforms=_conforms, validation_report=_text, validation_failures=[])
    if accept_type == "text/plain":
        if simple_resp.validation_failures:
            failure_texts = "\r\n".join(simple_resp.validation_failures)
            resp_txt = f"validation_failures:\r\n{failure_texts}\r\n"
        else:
            resp_txt = f"conforms: {simple_resp.conforms}\r\n{simple_resp.validation_report}\r\n"
        return text(resp_txt, content_type=accept_type)
    elif accept_type == "application/json":
        resp_dict = {
            "conforms": simple_resp.conforms or False,
            "validation_report": simple_resp.validation_report,
            "validation_failures": simple_resp.validation_failures,
        }
        # Note, this is regular REST JSON, not a real JSON-LD RDF result
        return JSONResponse(resp_dict, content_type=accept_type)
    if simple_resp.validation_failures:
        # Not sure if we can translate these failures into RDF. Probably not possible.
        # Pull a swiftie and return JSON instead.
        resp_dict = {
            "conforms": False,
            "validation_report": simple_resp.validation_report,
            "validation_failures": simple_resp.validation_failures,
        }
        return JSONResponse(resp_dict, content_type="application/json")
    if accept_type == "application/ld+json":
        graph_str = _graph.serialize(format="json-ld")
    elif accept_type == "text/turtle":
        graph_str = _graph.serialize(format="turtle")
    elif accept_type == "application/xml" or accept_type == "application/rdf+xml":
        graph_str = _graph.serialize(format="xml")
    else:
        graph_str = _graph.serialize(format="ntriples")
    return HTTPResponse(body=graph_str, content_type=accept_type)


BASE_LOGO = """
            PySHACL
    Running HTTP REST Service

"""

COLOR_LOGO = """\033[48;2;255;13;104m                     \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ███████╗██╗  ██╗  \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ██╔════╝██║  ██║  \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ███████╗███████║  \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ╚════██║██╔══██║  \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ███████║██║  ██║  \033[0m
\033[38;2;255;255;255;48;2;255;13;104m   ╚══════╝╚═╝  ╚═╝  \033[0m
\033[48;2;255;13;104m   Running PySHACL   \033[0m
   HTTP REST Service """

FULL_COLOR_LOGO = """\033[38;2;255;13;104m             \033[0m
\033[38;2;255;13;104m ██████╗ ██╗   ██╗\033[0m ███████╗██╗  ██╗ █████╗  ██████╗██╗
\033[38;2;255;13;104m ██╔══██╗╚██╗ ██╔╝\033[0m ██╔════╝██║  ██║██╔══██╗██╔════╝██║
\033[38;2;255;13;104m ██████╔╝ ╚████╔╝ \033[0m ███████╗███████║███████║██║     ██║
\033[38;2;255;13;104m ██╔═══╝   ╚██╔╝  \033[0m ╚════██║██╔══██║██╔══██║██║     ██║
\033[38;2;255;13;104m ██║        ██║   \033[0m ███████║██║  ██║██║  ██║╚██████╗███████╗
\033[38;2;255;13;104m ╚═╝        ╚═╝   \033[0m ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
"""  # noqa


def app_factory() -> Sanic:
    sanic.application.logo.BASE_LOGO = BASE_LOGO
    sanic.application.logo.COLOR_LOGO = COLOR_LOGO
    sanic.application.logo.FULL_COLOR_LOGO = FULL_COLOR_LOGO
    app = Sanic("PySHACL")
    app.config['MOTD_DISPLAY']["Application"] = "PySHACL HTTP SERVICE"
    CORS_OPTIONS = {"resources": r'/*', "origins": "*", "methods": ["GET", "POST", "HEAD", "OPTIONS"]}
    app.config['CORS_AUTOMATIC_OPTIONS'] = True
    # Disable sanic-ext built-in CORS, and add the Sanic-CORS plugin
    Extend(app, extensions=[CORS], config={"CORS": False, "CORS_OPTIONS": CORS_OPTIONS})

    app.ext.openapi.describe(
        "PySHACL Simple Validation Service API",
        version=API_VERSION,
        description=dedent(
            f"""
            # Info
            PySHACL is hosting its own simple validation service API endpoint.

            PySHACL version: `{pyshacl_version}`

            PySHACL API Spec Version: `{API_VERSION}`

            _Previously a standalone wrapper service, this feature is now built into PySHACL._
            """
        ),
    )
    app.route("/validate", methods=('POST', 'OPTIONS'))(sh_validate)
    return app


def run_server():
    PYSHACL_SERVER_LISTEN = os.getenv("PYSHACL_SERVER_LISTEN", "127.0.0.1")
    PYSHACL_SERVER_PORT_str = os.getenv("PYSHACL_SERVER_PORT", "8099")
    PYSHACL_SERVER_HOSTNAME = os.getenv("PYSHACL_SERVER_HOSTNAME", "")
    try:
        PYSHACL_SERVER_PORT = int(PYSHACL_SERVER_PORT_str)
    except ValueError:
        raise RuntimeError("Invalid port given for PySHACL Server Port")
    app: Sanic = app_factory()
    if PYSHACL_SERVER_HOSTNAME:
        app.config.SERVER_NAME = PYSHACL_SERVER_HOSTNAME
    app.run(
        PYSHACL_SERVER_LISTEN,
        port=PYSHACL_SERVER_PORT,
        access_log=False,
        auto_reload=False,
        single_process=True,
        legacy=False,
        debug=False,
    )


def cli():
    """CLI entrypoint for the HTTP Service"""
    try:
        run_server()
    except RuntimeError as r:
        import traceback

        sys.stderr.write(f"{r}\r\n")
        traceback.print_tb(r.__traceback__, file=sys.stderr)
        sys.stderr.flush()
        return 1
    return 0
