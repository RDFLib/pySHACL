# -*- coding: latin-1 -*-
#
import os
import sys

from pyshacl.cli import main as validate_main
from pyshacl.cli_rules import main as rules_main


def str_is_true(s_var: str):
    if len(s_var) > 0:
        if s_var.lower() not in ("0", "f", "n", "false", "no"):
            return True
    return False


do_server = os.getenv("PYSHACL_HTTP", "")
do_server = os.getenv("PYSHACL_SERVER", do_server)

first_arg = None if len(sys.argv) < 2 else sys.argv[1]

if first_arg is not None and str(first_arg).lower() in ('rules', '--rules'):
    rules_main(prog="python3 -m pyshacl")
elif (first_arg is not None and str(first_arg).lower() in ('serve', 'server', '--server')) or (
    do_server and str_is_true(do_server)
):
    from pyshacl.sh_http import main as http_main

    http_main()
else:
    validate_main(prog="python3 -m pyshacl")
