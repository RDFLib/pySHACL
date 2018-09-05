# -*- coding: utf-8 -*-
import rdflib
import RDFClosure as owl_rl
if owl_rl.json_ld_available:
    import rdflib_jsonld
from pyshacl.shape import find_shapes
from pyshacl.consts import RDF_type, SH_conforms, \
    SH_result, SH_ValidationReport
import logging

logging.basicConfig(level=logging.INFO)
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

    @classmethod
    def create_validation_report(cls, conforms, results):
        v_text = "Validation Report\nConforms: {}\n".format(str(conforms))
        result_len = len(results)
        if not conforms:
            assert result_len > 0, \
                "A Non-Conformant Validation Report must have at least one result."
        if result_len > 0:
            v_text += "Results ({}):\n".format(str(result_len))
        vg = rdflib.Graph()
        vr = rdflib.BNode()
        vg.add((vr, RDF_type, SH_ValidationReport))
        vg.add((vr, SH_conforms, rdflib.Literal(conforms)))
        for result in iter(results):
            _d, _bn, _tr = result
            v_text += _d
            vg.add((vr, SH_result, _bn))
            for tr in iter(_tr):
                vg.add(tr)
        log.info(v_text)
        return vg

    def __init__(self, target_graph, *args,
                 shacl_graph=None, options=None, **kwargs):
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
        if self.options.get('inference', True):
            self._run_pre_inference(self.target_graph)
        shapes = find_shapes(self.shacl_graph)
        fails = []
        non_conformant = False
        for s in shapes:
            _is_conform, _fails = s.validate(self.target_graph)
            non_conformant = non_conformant or (not _is_conform)
            fails.extend(_fails)
        report = self.create_validation_report((not non_conformant), fails)
        return (not non_conformant), report


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


