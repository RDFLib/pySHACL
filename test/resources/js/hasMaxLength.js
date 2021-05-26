function hasMaxLength($value, $maxLength) {
	if($value.isLiteral()) {
		return $value.lex.length <= $maxLength.lex;
	}
	else if($value.isURI()) {
		return $value.uri.length <= $maxLength.lex;
	}
	else { // Blank node
		return false;
	}
}
