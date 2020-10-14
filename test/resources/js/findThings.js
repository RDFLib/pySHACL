var RDFtype = TermFactory.namedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type");
var OWLThing = TermFactory.namedNode("http://www.w3.org/2002/07/owl#Thing");

function findThings() {
    var spo = $data.find(null, RDFtype, OWLThing);
	var accum = [];
	for(var t = spo.next(); t; t = spo.next()) {
		var subject = t.subject;
		accum.push(subject);
	}
	return accum;
}
