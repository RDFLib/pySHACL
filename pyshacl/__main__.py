# -*- coding: latin-1 -*-
#
import os
import sys

from pyshacl.cli import main


def str_is_true(s_var: str):
    if len(s_var) > 0:
        if s_var.lower() not in ("0", "f", "n", "false", "no"):
            return True
    return False


do_server = os.getenv("PYSHACL_HTTP", "")
do_server = os.getenv("PYSHACL_SERVER", do_server)

if (len(sys.argv) > 1 and str(sys.argv[1]).lower() in ('serve', 'server', '--server')) or (
    do_server and str_is_true(do_server)
):
    from pyshacl.sh_http import cli as http_cli

    sys.exit(http_cli())

sys.exit(main())
