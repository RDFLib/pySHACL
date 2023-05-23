import sys

mod = sys.modules[__name__]
setattr(mod, 'SPARQLQueryHelperCls', None)


def get_query_helper_cls():
    # The SPARQLQueryHelper file is expensive to load due to regex compilation steps
    # so we do it this way so its only loaded when something actually needs to use
    # a SPARQLQueryHelper
    SPARQLQueryHelperCls = getattr(mod, 'SPARQLQueryHelperCls', None)
    if SPARQLQueryHelperCls is None:
        from .sparql_query_helper import SPARQLQueryHelper

        SPARQLQueryHelperCls = SPARQLQueryHelper
        setattr(mod, 'SPARQLQueryHelperCls', SPARQLQueryHelperCls)
    return SPARQLQueryHelperCls
