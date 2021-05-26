var NS = "http://datashapes.org/js/tests/rules/rectangle.test#";

function computeArea($this) {
	var width = getProperty($this, "width");
	var height = getProperty($this, "height");
	var area = TermFactory.literal(width.lex * height.lex, width.datatype);
	var areaProperty = TermFactory.namedNode(NS + "area");
	return [
		[$this, areaProperty, area]
	];
}

function getProperty($this, name) {
	var it = $data.find($this, TermFactory.namedNode(NS + name), null);
	var result = it.next().object;
	it.close();
	return result;
}
