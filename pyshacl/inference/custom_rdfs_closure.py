# -*- coding: utf-8 -*-
from RDFClosure.RDFSClosure import RDFS_Semantics as OrigRDFSSemantics
from RDFClosure.OWLRL import OWLRL_Semantics

from RDFClosure.RDFS import Resource, Class, Datatype
from RDFClosure.OWL import OWLClass, Thing, equivalentClass, DataRange

class CustomRDFSSemantics(OrigRDFSSemantics):
    def one_time_rules(self):
        """
        Override the RDFSClosure one-time-rules so that it does nothing
        These rules usually add 'hidden' literals to the graph in
        such a way that breaks some SHACL validation tests.
        """
        pass


class CustomRDFSOWLRLSemantics(CustomRDFSSemantics, OWLRL_Semantics):
    """
    Custom hybrid RDFS+OWL-RL using our CustomRDFSSemantics above.
    Copied directly from RDFSClosure.CombinedClosure
    with a few tiny modifications
    """
    full_binding_triples = [
        (Thing, equivalentClass, Resource),
        (Class, equivalentClass, OWLClass),
        (DataRange, equivalentClass, Datatype)
    ]

    def __init__(self, graph, axioms, daxioms, rdfs=True):
        OWLRL_Semantics.__init__(self, graph, axioms, daxioms, rdfs)
        CustomRDFSSemantics.__init__(self, graph, axioms, daxioms, rdfs)
        self.rdfs = True

    # noinspection PyMethodMayBeStatic
    @staticmethod
    def add_new_datatype(uri, conversion_function, datatype_list,
                         subsumption_dict=None, subsumption_key=None,
                         subsumption_list=None):
        """If an extension wants to add new datatypes, this method should be invoked at initialization time.

        @param uri: URI for the new datatypes, like owl_ns["Rational"]
        @param conversion_function: a function converting the lexical representation of the datatype to a Python value,
        possibly raising an exception in case of unsuitable lexical form
        @param datatype_list: list of datatypes already in use that has to be checked
        @param subsumption_dict: dictionary of subsumption hierarchies (indexed by the datatype URI-s)
        @param subsumption_key: key in the dictionary, if None, the uri parameter is used
        @param subsumption_list: list of subsumptions associated to a subsumption key (ie, all datatypes that are
        superclasses of the new datatype)
        """
        from RDFClosure.DatatypeHandling import AltXSDToPYTHON, \
            use_Alt_lexical_conversions

        if datatype_list:
            datatype_list.append(uri)

        if subsumption_dict and subsumption_list:
            if subsumption_key:
                subsumption_dict[subsumption_key] = subsumption_list
            else:
                subsumption_dict[uri] = subsumption_list

        AltXSDToPYTHON[uri] = conversion_function
        use_Alt_lexical_conversions()

    def post_process(self):
        """Do some post-processing step. This method when all processing is done, but before handling possible
        errors (ie, the method can add its own error messages). By default, this method is empty, subclasses
        can add content to it by overriding it.
        """
        OWLRL_Semantics.post_process(self)

    def rules(self, t, cycle_num):
        """
        @param t: a triple (in the form of a tuple)
        @param cycle_num: which cycle are we in, starting with 1. This value is forwarded to all local rules; it is
        also used locally to collect the bnodes in the graph.
        """
        OWLRL_Semantics.rules(self, t, cycle_num)
        if self.rdfs:
            CustomRDFSSemantics.rules(self, t, cycle_num)

    def add_axioms(self):
        if self.rdfs:
            CustomRDFSSemantics.add_axioms(self)
        OWLRL_Semantics.add_axioms(self)

    def add_d_axioms(self):
        if self.rdfs:
            CustomRDFSSemantics.add_d_axioms(self)
        OWLRL_Semantics.add_d_axioms(self)

    def one_time_rules(self):
        """Adds some extra axioms and calls for the d_axiom part of the OWL Semantics."""
        for t in self.full_binding_triples:
            self.store_triple(t)

        # Note that the RL one time rules include the management of datatype which is a true superset
        # of the rules in RDFS. It is therefore unnecessary to add those even self.rdfs is True.
        OWLRL_Semantics.one_time_rules(self)
