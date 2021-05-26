var EXbornIn = TermFactory.namedNode("http://datashapes.org/sh/tests/js/target/jsTargetType-001.test#bornIn");

function findBornIn($country) {
    var spo = $data.find(null, EXbornIn, $country);
	var accum = [];
	for(var t = spo.next(); t; t = spo.next()) {
		var subject = t.subject;
		accum.push(subject);
	}
	return accum;
}
