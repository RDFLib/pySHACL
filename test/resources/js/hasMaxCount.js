function hasMaxCount($this, $path, $maxCount) {
	var spo = $data.find($this, $path, null);
	var accum = [];
	for(var t = spo.next(); t; t = spo.next()) {
		var object = t.object;
		accum.push(object);
	}
	if (accum.length > $maxCount.lex) {
		return false;
	}
	return true;
}
