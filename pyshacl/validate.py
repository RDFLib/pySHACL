# -*- coding: utf-8 -*-
import rdflib
import RDFClosure as owl_rl

from pyshacl.shape import find_shapes

if owl_rl.json_ld_available:
    import rdflib_jsonld

import logging

logging.basicConfig()
log = logging.getLogger(__name__)


class Validator(object):
    @classmethod
    def _load_default_options(cls, options_dict):
        options_dict['inference'] = True
        options_dict['abort_on_error'] = False

    @classmethod
    def _run_pre_inference(cls, target_graph):
        try:
            inferencer = owl_rl.DeductiveClosure(owl_rl.RDFS_OWLRL_Semantics)
        except Exception as e:
            log.error("Error during creation of OWL-RL Deductive Closure")
            raise e
        try:
            inferencer.expand(target_graph)
        except Exception as e:
            log.error("Error while running OWL-RL Deductive Closure")
            raise e

    def __init__(self, target_graph, *args, shacl_graph=None, options=None, **kwargs):
        if options is None:
            options = {}
        self._load_default_options(options)
        self.options = options
        assert isinstance(target_graph, rdflib.Graph),\
            "target_graph must be a rdflib Graph object"
        self.target_graph = target_graph
        if shacl_graph is None:
            shacl_graph = target_graph
        assert isinstance(shacl_graph, rdflib.Graph),\
            "shacl_graph must be a rdflib Graph object"
        self.shacl_graph = shacl_graph


    def run(self):
        if self.options['inference']:
            self._run_pre_inference(self.target_graph)
        shapes = find_shapes(self.shacl_graph)
        results = {}
        for s in shapes:
            r = s.validate(self.target_graph)
            results[s.node] = r
        return results

# TODO: check out rdflib.util.guess_format() for format. I think it works well except for perhaps JSON-LD
def _load_into_graph(target):
    if isinstance(target, rdflib.Graph):
        return target
    target_is_file = False
    target_is_text = False
    rdf_format = None
    if isinstance(target, str):
        if target.startswith('file://'):
            target_is_file = True
            target = target[7:]
        elif len(target) < 240:
            if target.endswith('.ttl'):
                target_is_file = True
                rdf_format = 'turtle'
            elif target.endswith('.xml'):
                target_is_file = True
                rdf_format = 'xml'
            elif target.endswith('.json'):
                target_is_file = True
                rdf_format = 'json-ld'
        if not target_is_file:
            target_is_text = True
    else:
        raise RuntimeError("Cannot determine the format of the input graph")
    g = rdflib.Graph()
    if target_is_file:
        import os
        file_name = os.path.abspath(target)
        with open(file_name, mode='rb') as file:
            g.parse(source=None, publicID=None, format=rdf_format,
                    location=None, file=file)
    elif target_is_text:
        g.parse(source=target)
    return g


def validate(target_graph, *args, shacl_graph=None, inference=True, abort_on_error=False, **kwargs):
    target_graph = _load_into_graph(target_graph)
    if shacl_graph is not None:
        shacl_graph = _load_into_graph(shacl_graph)
    validator = Validator(
        target_graph, shacl_graph,
        options={'inference': inference, 'abort_on_error': abort_on_error})
    return validator.run()


