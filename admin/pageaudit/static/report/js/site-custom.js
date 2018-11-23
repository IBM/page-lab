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



	// Storage Util
	var me = PL.namespace(PL, "util.storage");

	/**
		Clears the user's browser localStorage (for the owning domain).
		<br />CAUTION: This is the localStorage equivalent of clearing all of the user's cookies for your domain.
		
		@method clear
		@return {Boolean} True if localStorage is supported, else false.
	**/
	me.clear = function () {
		if (!me.isSupported()) {
			return false;
		}

		localStorage.clear();
		return true;
	};

	/**
		Gets the requested item from browser localStorage.
		
		@method getItem
		@param key {String} The name of the key/item to get from localStorage.
		@return {Varies} The data for the key if localStorage is supported &amp;&amp; if key exists &amp;&amp; key is not expired,
		 else returns: null.
	**/
	me.getItem = function (key) {
		var storageData = null,
			expires = 0, // 0 means no expiration.
			timeNow = new Date().getTime();
			
		if (!me.isSupported()) {
			return null;
		}

		// If it has an expiration date (has a # other than 0) that has passed, remove it b/c it's invalid data now.
		// else parse the storage data and set it for return.
		if (localStorage.getItem(key) !== null) {
			expires = JSON.parse(localStorage.getItem(key)).expires;

			if (expires !== 0 && expires < timeNow) {
				me.removeItem(key);
			}
			else {
				storageData = JSON.parse(localStorage.getItem(key)).value;
			}
		}
		
		return storageData;
	};

	/**
		Checks if browser localStorage is supported by the current user's browser.
		<br />This is used by every method in this utility class so you don't need to use this unless you have special case use for it.
		<br />Provided as a public method purely for your convenience.
		
		@method isSupported
		@return {Boolean} True if localStorage is supported, else false.
	**/
	me.isSupported = function () {
		return localStorage && typeof JSON !== "undefined";
	};
	
	/**
		Deletes the requested item from browser localStorage.
		
		@method removeItem
		@param key {String} The name of the key/item to delete from localStorage.
		@return {Boolean} True if localStorage is supported, else false.
	**/
	me.removeItem = function (key) {
		if (!me.isSupported()) {
			return false;
		}
		localStorage.removeItem(key);
		return true;
	};

	/**
		Stores data in browser localStorage.
		
		@method setItem
		@param key {String} The name of the key to use for this data store in localStorage.
		@param value {String} The value/data to store in localStorage.
		@param [lifetime] {String} The storage item's TTL (time to live), in <strong>SECONDS</strong>. 
		  AKA: How long until it expires.
		  If lifetime is not supplied, the storage item TTL is session-only.
		@return {Boolean} True if localStorage is supported, else false.
	**/
	me.setItem = function (key, value, lifetime) {
		var expireTime = 0,
			storageObject = {},
			timeNow = new Date().getTime();
		
		// Can't do shit if localStorage isn't supported.
		if (!me.isSupported()) {
			return false;
		}

		// First we should remove this key if it already exists.
		me.removeItem(key);

		// If lifetime is specified...
		if (lifetime) {
			expireTime = lifetime * 1000;
			expireTime += timeNow;
		}

		// Build our storage object.
		storageObject = {
			"value": value, 
			"expires": expireTime
		};
		
		// Do it.
		localStorage.setItem(key, JSON.stringify(storageObject));

		return true;
	};
	
	// Copied from Lighthouse-viewer app in Google Lighthouse repo:
	// https://github.com/GoogleChrome/lighthouse/blob/master/lighthouse-core/report/html/renderer/report-ui-features.js#L353-L384 
	//   Made adjustment for origin/view path and added to our global namespace.
    PL.openTabAndSendJsonReport = function (reportJson, viewerPath) {
        const VIEWER_ORIGIN = window.location;
        // Chrome doesn't allow us to immediately postMessage to a popup right
        // after it's created. Normally, we could also listen for the popup window's
        // load event, however it is cross-domain and won't fire. Instead, listen
        // for a message from the target app saying "I'm open".
        const json = reportJson;
        
        window.addEventListener('message', function msgHandler(/** @type {Event} */ e) {
            const messageEvent = /** @type {MessageEvent} */ (e);
            
            if (popup && messageEvent.data.opened) {
                popup.postMessage({lhresults: json}, VIEWER_ORIGIN);
                window.removeEventListener('message', msgHandler);
            }
        });
        
        // The popup's window.name is keyed by version+url+fetchTime, so we reuse/select tabs correctly
        // @ts-ignore - If this is a v2 LHR, use old `generatedTime`.
        const fallbackFetchTime = /** @type {string} */ (json.generatedTime);
        const fetchTime = json.fetchTime || fallbackFetchTime;
        const windowName = `${json.lighthouseVersion}-${json.requestedUrl}-${fetchTime}`;
        const popup = window.open(`${viewerPath}`, windowName);
    }

	
})(jQuery, PL);

