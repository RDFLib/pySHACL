#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

from prettytable import PrettyTable
from rdflib.namespace import SH

from pyshacl import __version__, validate
from pyshacl.errors import (
    ConstraintLoadError,
    ReportableRuntimeError,
    RuleLoadError,
    ShapeLoadError,
    ValidationFailure,
)


class ShowVersion(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super(ShowVersion, self).__init__(
            option_strings=option_strings, dest=dest, default=default, nargs=0, help=help
        )

    def __call__(self, parser, namespace, values, option_string=None):
        # parser.exit() writes message to stderr before calling sys.exit()
        parser.exit(status=0, message="PySHACL Version: " + str(__version__) + "\n")


def str_is_true(s_var: str):
    if len(s_var) > 0:
        if s_var.lower() not in ("0", "f", "n", "false", "no"):
            return True
    return False


parser = argparse.ArgumentParser(description='PySHACL {} Validator command line tool.'.format(str(__version__)))
parser.add_argument(
    'data',
    metavar='DataGraph',
    type=argparse.FileType('rb'),
    help='The file containing the Target Data Graph.',
    default=None,
    nargs='?',
)
parser.add_argument(
    '-s', '--shacl', dest='shacl', action='store', nargs='?', help='A file containing the SHACL Shapes Graph.'
)
parser.add_argument(
    '-e',
    '--ont-graph',
    dest='ont',
    action='store',
    nargs='?',
    help='A file path or URL to a document containing extra ontological information. '
    'RDFS and OWL definitions from this are used to inoculate the DataGraph.',
)
parser.add_argument(
    '-i',
    '--inference',
    dest='inference',
    action='store',
    default='none',
    choices=('none', 'rdfs', 'owlrl', 'both'),
    help='Choose a type of inferencing to run against the Data Graph before validating.',
)
parser.add_argument(
    '-m',
    '--metashacl',
    dest='metashacl',
    action='store_true',
    default=False,
    help='Validate the SHACL Shapes graph against the shacl-shacl Shapes Graph before validating the Data Graph.',
)
parser.add_argument(
    '-im',
    '--imports',
    dest='imports',
    action='store_true',
    default=False,
    help='Allow import of sub-graphs defined in statements with owl:imports.',
)
parser.add_argument(
    '-a',
    '--advanced',
    dest='advanced',
    action='store_true',
    default=False,
    help='Enable features from the SHACL Advanced Features specification.',
)
parser.add_argument(
    '-j',
    '--js',
    dest='js',
    action='store_true',
    default=False,
    help='Enable features from the SHACL-JS Specification.',
)
parser.add_argument(
    '-it',
    '--iterate-rules',
    dest='iterate_rules',
    action='store_true',
    default=False,
    help="Run Shape's SHACL Rules iteratively until the data_graph reaches a steady state.",
)
parser.add_argument('--abort', dest='abort', action='store_true', default=False, help='Abort on first invalid data.')
parser.add_argument(
    '--allow-info',
    '--allow-infos',
    dest='allow_infos',
    action='store_true',
    default=False,
    help='Shapes marked with severity of Info will not cause result to be invalid.',
)
parser.add_argument(
    '-w',
    '--allow-warning',
    '--allow-warnings',
    dest='allow_warnings',
    action='store_true',
    default=False,
    help='Shapes marked with severity of Warning or Info will not cause result to be invalid.',
)
parser.add_argument(
    '-d', '--debug', dest='debug', action='store_true', default=False, help='Output additional runtime messages.'
)
parser.add_argument(
    '-f',
    '--format',
    dest='format',
    action='store',
    help='Choose an output format. Default is \"human\".',
    default='human',
    choices=('human', 'table', 'turtle', 'xml', 'json-ld', 'nt', 'n3'),
)
parser.add_argument(
    '-df',
    '--data-file-format',
    dest='data_file_format',
    action='store',
    help='Explicitly state the RDF File format of the input DataGraph file. Default=\"auto\".',
    default='auto',
    choices=('auto', 'turtle', 'xml', 'json-ld', 'nt', 'n3'),
)
parser.add_argument(
    '-sf',
    '--shacl-file-format',
    dest='shacl_file_format',
    action='store',
    help='Explicitly state the RDF File format of the input SHACL file. Default=\"auto\".',
    default='auto',
    choices=('auto', 'turtle', 'xml', 'json-ld', 'nt', 'n3'),
)
parser.add_argument(
    '-ef',
    '--ont-file-format',
    dest='ont_file_format',
    action='store',
    help='Explicitly state the RDF File format of the extra ontology file. Default=\"auto\".',
    default='auto',
    choices=('auto', 'turtle', 'xml', 'json-ld', 'nt', 'n3'),
)
parser.add_argument('-V', '--version', action=ShowVersion, help='Show PySHACL version and exit.')
parser.add_argument(
    '-o',
    '--output',
    dest='output',
    nargs='?',
    type=argparse.FileType('w'),
    help='Send output to a file (defaults to stdout).',
    default=sys.stdout,
)
parser.add_argument(
    '--server',
    help='Ignore all the rest of the options, start the HTTP Server. Same as `pyshacl_server`.',
    action='store_true',
    dest='server',
    default=False,
)
# parser.add_argument('-h', '--help', action="help", help='Show this help text.')


def main():
    basename = os.path.basename(sys.argv[0])
    if basename == "__main__.py":
        parser.prog = "python3 -m pyshacl"
    do_server = os.getenv("PYSHACL_HTTP", "")
    do_server = os.getenv("PYSHACL_SERVER", do_server)
    if do_server:
        args = {}
    else:
        args = parser.parse_args()
    if str_is_true(do_server) or args.server:
        from pyshacl.sh_http import cli as http_cli

        sys.exit(http_cli())
    elif not args.data:
        # No datafile give, and not starting in server mode.
        sys.stderr.write('Validation Error. No DataGraph file supplied.\n')
        parser.print_usage(sys.stderr)
        sys.exit(1)
    validator_kwargs = {'debug': args.debug}
    if args.shacl is not None:
        validator_kwargs['shacl_graph'] = args.shacl
    if args.ont is not None:
        validator_kwargs['ont_graph'] = args.ont
    if args.format not in ['human', 'table']:
        validator_kwargs['serialize_report_graph'] = args.format
    if args.inference != 'none':
        validator_kwargs['inference'] = args.inference
    if args.imports:
        validator_kwargs['do_owl_imports'] = True
    if args.metashacl:
        validator_kwargs['meta_shacl'] = True
    if args.advanced:
        validator_kwargs['advanced'] = True
    if args.js:
        validator_kwargs['js'] = True
    if args.iterate_rules:
        if not args.advanced:
            sys.stderr.write("Iterate-Rules option only works when you enable Advanced Mode.\n")
        else:
            validator_kwargs['iterate_rules'] = True
    if args.abort:
        validator_kwargs['abort_on_first'] = True
    if args.allow_infos:
        validator_kwargs['allow_infos'] = True
    if args.allow_warnings:
        validator_kwargs['allow_warnings'] = True
    if args.shacl_file_format:
        _f: str = args.shacl_file_format
        if _f != "auto":
            validator_kwargs['shacl_graph_format'] = _f
    if args.ont_file_format:
        _f = args.ont_file_format
        if _f != "auto":
            validator_kwargs['ont_graph_format'] = _f
    if args.data_file_format:
        _f = args.data_file_format
        if _f != "auto":
            validator_kwargs['data_graph_format'] = _f
    try:
        is_conform, v_graph, v_text = validate(args.data, **validator_kwargs)
        if isinstance(v_graph, BaseException):
            raise v_graph
    except ValidationFailure as vf:
        args.output.write("Validator generated a Validation Failure result:\n")
        args.output.write(str(vf.message))
        args.output.write("\n")
        sys.exit(1)
    except ShapeLoadError as sle:
        sys.stderr.write("Validator encountered a Shape Load Error:\n")
        sys.stderr.write(str(sle))
        sys.exit(2)
    except ConstraintLoadError as cle:
        sys.stderr.write("Validator encountered a Constraint Load Error:\n")
        sys.stderr.write(str(cle))
        sys.exit(2)
    except RuleLoadError as rle:
        sys.stderr.write("Validator encountered a Rule Load Error:\n")
        sys.stderr.write(str(rle))
        sys.exit(2)
    except ReportableRuntimeError as rre:
        sys.stderr.write("Validator encountered a Runtime Error:\n")
        sys.stderr.write(str(rre.message))
        sys.stderr.write("\nIf you believe this is a bug in pyshacl, open an Issue on the pyshacl github page.\n")
        sys.exit(2)
    except NotImplementedError as nie:
        sys.stderr.write("Validator feature is not implemented:\n")
        sys.stderr.write(str(nie.args[0]))
        sys.stderr.write("\nIf your use-case requires this feature, open an Issue on the pyshacl github page.\n")
        sys.exit(3)
    except RuntimeError as re:
        import traceback

        traceback.print_tb(re.__traceback__)
        sys.stderr.write(
            "\n\nValidator encountered a Runtime Error. Please report this to the PySHACL issue tracker.\n"
        )
        sys.exit(2)

    if args.format == 'human':
        args.output.write(v_text)
    elif args.format == 'table':
        t1 = PrettyTable()
        t1.field_names = ["Conforms"]
        t1.align = "c"
        t1.add_row([is_conform])
        args.output.write(str(t1))
        args.output.write('\n\n')

        def col_widther(s, w):
            """Split strings to a given width for table"""
            s2 = []
            i = 0
            while i < len(s):
                s2.append(s[i : i + w])
                i += w
            return '\n'.join(s2)

        if not is_conform:
            t2 = PrettyTable()
            t2.field_names = ['No.', 'Severity', 'Focus Node', 'Result Path', 'Message', 'Component', 'Shape', 'Value']
            t2.align = "l"

            for i, o in enumerate(v_graph.objects(None, SH.result)):
                r = {}
                for o2 in v_graph.predicate_objects(o):
                    r[o2[0]] = str(col_widther(o2[1].replace(f'{SH}', ''), 25))  # max col width 30 chars
                t2.add_row(
                    [
                        i + 1,
                        r[SH.resultSeverity],
                        r[SH.focusNode],
                        r[SH.resultPath] if r.get(SH.resultPath) is not None else '-',
                        r[SH.resultMessage] if r.get(SH.resultMessage) is not None else '-',
                        r[SH.sourceConstraintComponent],
                        r[SH.sourceShape],
                        r[SH.value] if r.get(SH.value) is not None else '-',
                    ]
                )
                t2.add_row(['', '', '', '', '', '', '', ''])
            args.output.write(str(t2))
    else:
        if isinstance(v_graph, bytes):
            v_graph = v_graph.decode('utf-8')
        args.output.write(v_graph)
    args.output.close()
    if is_conform:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
