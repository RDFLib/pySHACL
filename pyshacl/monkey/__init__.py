# -*- coding: utf-8 -*-

from distutils.version import LooseVersion

import rdflib

from rdflib import plugin, store


RDFLIB_VERSION = LooseVersion(rdflib.__version__)
RDFLIB_421 = LooseVersion("4.2.1")
RDFLIB_500 = LooseVersion("5.0.0")


def rdflib_bool_patch():
    from rdflib.term import _XSD_PFX, URIRef, _toPythonMapping

    rdflib.NORMALIZE_LITERALS = False
    # we want to consider only 'true' to be a valid XSD:boolean truth (ie, ignore '1')
    _toPythonMapping[URIRef(_XSD_PFX + 'boolean')] = lambda i: i.lower() == 'true'


def rdflib_bool_unpatch():
    from rdflib.term import _XSD_PFX, URIRef, _toPythonMapping

    rdflib.NORMALIZE_LITERALS = True
    if RDFLIB_500 > RDFLIB_VERSION:
        # versions before rdflib 5.0.0
        _toPythonMapping[URIRef(_XSD_PFX + 'boolean')] = lambda i: i.lower() in ['true', '1']
    else:
        # rdflib 5.0.0 and above
        from rdflib.term import _parseBoolean

        _toPythonMapping[URIRef(_XSD_PFX + 'boolean')] = _parseBoolean


def rdflib_term_ge_le_patch():
    def __le__(term, other):
        r = term.__lt__(other)
        if r:
            return r
        try:
            return term.eq(other)
        except TypeError:
            return NotImplemented

    def __ge__(term, other):
        try:
            return term.__gt__(other) or term.eq(other)
        except TypeError:
            return NotImplemented

    setattr(rdflib.term.Literal, "__ge__", __ge__)
    setattr(rdflib.term.Literal, "__le__", __le__)


def apply_patches():
    if RDFLIB_421 >= RDFLIB_VERSION:
        rdflib_term_ge_le_patch()
    if RDFLIB_421 <= RDFLIB_VERSION:
        plugin.register("default", store.Store, "pyshacl.monkey.memory2", "Memory2")
        plugin.register("Memory2", store.Store, "pyshacl.monkey.memory2", "Memory2")
    return True
