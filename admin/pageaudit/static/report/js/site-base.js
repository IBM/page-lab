(function ($, PL) {

	// Core namespace utility
	PL.namespace = function() {
		var scope = arguments[0],
			ln = arguments.length,
			i, value, split, x, xln, parts, object;

		for (i = 1; i < ln; i++) {
			value = arguments[i];
			parts = value.split(".");
			object = scope[parts[0]] = Object(scope[parts[0]]);
			for (x = 1, xln = parts.length; x < xln; x++) {
				object = object[parts[x]] = Object(object[parts[x]]);
			}
		}
		return object;
	};


})(jQuery, PL);
