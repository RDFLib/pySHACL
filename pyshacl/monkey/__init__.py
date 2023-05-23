# -*- coding: utf-8 -*-

import rdflib
from packaging.version import Version
from rdflib import store

RDFLIB_VERSION = Version(rdflib.__version__)
RDFLIB_421 = Version("4.2.1")
RDFLIB_500 = Version("5.0.0")
RDFLIB_600 = Version("6.0.0")
RDFLIB_602 = Version("6.0.2")
RDFLIB_611 = Version("6.1.1")
RDFLIB_620 = Version("6.2.0")


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


def empty_iterator():
    # noinspection PyUnreachableCode
    if False:
        # noinspection PyUnreachableCode
        yield None  # type: ignore[unreachable]


def apply_patches():
    if RDFLIB_602 <= RDFLIB_VERSION < RDFLIB_611:
        # Fixes https://github.com/RDFLib/rdflib/pull/1432
        setattr(store.Store, "namespaces", empty_iterator)
    return True
