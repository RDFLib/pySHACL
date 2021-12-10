# -*- coding: utf-8 -*-
#
from functools import lru_cache
from warnings import warn

import pkg_resources

from pkg_resources import DistributionNotFound, UnknownExtra


# In dev mode, the extras-loader doesn't check if extension is installed before loading it.
# This is useful when testing, when we're working on a codebase of a library that is not yet installed.
dev_mode = False


@lru_cache()
def check_extra_installed(extra_name: str):
    if dev_mode:
        return True
    check_name = "pyshacl[" + extra_name + "]"
    # first check if pyshacl is installed using the normal means
    try:
        _ = pkg_resources.require("pyshacl")
    except DistributionNotFound:
        # Hmm, it thinks pyshacl isn't installed. Can't even check for extras
        return None
    try:
        _ = pkg_resources.require(check_name)
        return True
    except UnknownExtra:
        # That extra doesn't exist in this version of pyshacl
        warn(Warning("Extra \"{}\" doesn't exist in this version of pyshacl.".format(extra_name)))
        return False
    except DistributionNotFound:
        # That extra is not installed right now
        return False
    except BaseException:
        raise
