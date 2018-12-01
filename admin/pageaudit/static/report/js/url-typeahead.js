
(function($) {
	var $inputField = {},
		$searchForm = {},
		$typeaheadUl = {},
		$typeaheadContainer = {},
		defaultTypeaheadRequestPause = 50, // # of MS to wait between typing before making a WSR.
		latestText = "",
		requestCount = 0,
		typeaheadResultsShowing = false,
		makeTypeaheadRequest = (function() {
			var timer = 0;
			return function(callback, ms) {
				var waitTime = ms || defaultTypeaheadRequestPause;
				clearTimeout(timer);
				timer = setTimeout(callback, waitTime);
			};
		})();


	function clearTypeahead () {
		if ($typeaheadUl.length > 0) {
			$typeaheadUl.empty();
		}
	}


	function requestTypeaheadText (forceRequest) {
		var currentSearchTerm = $inputField[0].value;

		if (currentSearchTerm === latestText && !forceRequest) {
			return;
		}

		latestText = currentSearchTerm;

		// If they cleared the search field (there's no value in the text field), remove the typeahead box and stop.
		if (currentSearchTerm === "") {
			makeTypeaheadRequest(function() {
				clearTypeahead();
				showTypeaheadResults(false);
				$searchForm.attr("action", "");
			}, defaultTypeaheadRequestPause + 10);

			return;
		}

		// Call the throttler with our callback function to run to make a typeahead service request.
		makeTypeaheadRequest(function() {
			$.ajax({
				url: PL.urls.api_url_typeahead + "?q=" + currentSearchTerm,
				dataType: "json",
				searchTerm: currentSearchTerm,
				requestCount: ++requestCount,
				success: function (response) {
					// If this request isn't the latest one (for slow API responses), 
					//  don't update the TA box with it's results.
					if (requestCount !== this.requestCount) {
						return;
					}
					
					if (response === null) {
						showTypeaheadResults(false);
						return;
					}

					var listArr = [],
						i = 0,
						len = 1
						results = response.results;
				
					if (results.length > 0) {
						len = results.length;
						
						// Loop thru all results. The createContainer function determines the limit to show from this array.
						for (i; i < len; i++) {
							if (results[i].url) {
								listArr.push(results[i]);
							}
						}
					}
					else {
    					listArr.push({
        					id: 0,
        					url: "No results found"
        				});
					}
					
					// Call the masthead typeahead API with the term used for *this WSR* 
					//  and the array you created of results to show.
					createTypeaheadContainer(this.searchTerm, listArr);
				},
				error: function(response) {
					console.error('Error calling typeahead service: ', response);
				}
			});
		});
	}

	// This limits the # that we show in the container.
	function createTypeaheadContainer (searchString, results) {
		var items = results,
			lis = "",
			maxNum = 6,
			searchedFor = searchString;

		items.sort();

		// Update this to better include min/max #s with 'for'.
		$.each(items, function (i, itemObj) {
			var term = itemObj.url,
				reg = new RegExp(searchedFor, 'i');
			
			term = term.replace(reg, '<strong>' + searchedFor + '</strong>');
			
			if (i < maxNum) {
				lis += '<li data-urlid="' + itemObj.id + '" id="pl-search-overlay-typeahead-res-' + i + '" role="option" tabindex="-1" class="nowrap"><a class="db relative" href="#" tabindex="-1">' + term + '</a></li>';
			}
		});

		// If they emptied the field after this WSR ran, clear the typeaheads.
		if ($inputField.val() === "") {
			clearTypeahead();
			showTypeaheadResults(false);
		}
		else {
			// Inject typeahead list on first time we have results.
			if (!$typeaheadContainer.find("ul")[0]) {
				$typeaheadContainer.html($typeaheadUl);
			}

			$typeaheadUl.html(lis);

			showTypeaheadResults(true);
		}
	}

	function showTypeaheadResults (b) {
		if (b) {
			$typeaheadContainer.addClass("pl-fadein").removeClass("pl-fadeout");
			typeaheadResultsShowing = true;
		}
		else {
			$typeaheadContainer.addClass("pl-fadeout").removeClass("pl-fadein");
			typeaheadResultsShowing = false;
		}
	}


	// Setup and bind fields
	function setupFields () {
		$inputField = $("#pl-url-search");
		$searchForm = $inputField.closest("form");
		$typeaheadContainer = $("#pl-typeahead-container");
		$typeaheadUl = $('<ul class="pl-dropdown-menu list pa0 ma0" role="listbox" aria-live="polite" aria-label="Suggestions"></ul>');

        $searchForm.on("submit", function (evt) {
            evt.preventDefault();
            
            // Hit service to validate URL report exists (in case of free-type in URL)
            // Returns the ID or null.
            // If not null, goto ID.
            var requestUrl = PL.urls.api_urlid + "?url=" + $inputField[0].value
            var xhr = new XMLHttpRequest();
            xhr.open('GET', requestUrl);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var data = JSON.parse(xhr.responseText);
                    try {
                        if (data.results.urlid) {
                            window.location.href = "urls/detail/" + data.results.urlid;
                        }
                        else {
                            showTypeaheadResults(true);
                        }
                    }
                    catch (ex) {
                        showTypeaheadResults(true);
                    }
                }
                else {
                    alert("DOH! Something happened and we couldn't find that URL.");
                }
            };
            xhr.send(); 
        })
        
		// Bind the results so when you click on one, it replaces the input text with it.
		$typeaheadUl.on("click", function (evt) {
			evt.preventDefault();
			evt.stopPropagation();
			
			if ($(evt.target).parent().data("urlid") !== 0) {
    		    $inputField.val(evt.target.text);
    		    $searchForm.trigger("submit");
			}
		});

		$inputField.on("input", function () {
			requestTypeaheadText();
		}).on("focus", function () {
			// If there is a value in the field, show the results on FIELD focus only.
			if ($inputField.val() !== "") {
				showTypeaheadResults(true);
			}
		}).on("keydown", function (evt) {
			// HAVE to use keycode for xbrowser support.
			var keyCode = evt.keyCode;

			// LEFT/RIGHT/TAB
			// Let natural behavior happen if: left/right arrow or tab.
			if (keyCode === 37 || keyCode === 39) {
				return;
			}

			if (evt.keyCode === 9) {
				showTypeaheadResults(false);
			}

			// UP/DOWN: 
			// If not showing, request current value typeahead
			// else goto next if it's already showing.
			// UP
			if (keyCode === 38) {
				evt.preventDefault();

				if (!typeaheadResultsShowing) {
					requestTypeaheadText();
				}				
				else {
					gotoPrevTypeaheadResult();
					setInputFieldValue();
				}
			}
			// DOWN
			else if (keyCode === 40) {
				evt.preventDefault();
				
				if (!typeaheadResultsShowing) {
					requestTypeaheadText();
				}
				else {
					gotoNextTypeaheadResult();
					setInputFieldValue();
				}
			}
		}).on("blur", function (evt) {
			showTypeaheadResults(false);
		});
	}


	function gotoNextTypeaheadResult () {
		var $nextItem = $typeaheadUl.find("li.pl-highlight").next("li");
		
		$typeaheadUl.find("li.pl-highlight").removeClass("pl-highlight");
			
		if ($nextItem[0]) {
			$nextItem.addClass("pl-highlight");
		}
		else {
			$("li:first", $typeaheadUl).addClass("pl-highlight");
		}

		// If this item if the section heading, skip it and goto the next one.
		if ($typeaheadUl.find("li.pl-highlight").hasClass("typeahead-nooption")) {
			gotoNextTypeaheadResult();
		}
	}


	function gotoPrevTypeaheadResult () {
		var $prevItem = $typeaheadUl.find("li.pl-highlight").prev("li");
		
		$typeaheadUl.find("li.pl-highlight").removeClass("pl-highlight");
			
		if ($prevItem[0]) {
			$prevItem.addClass("pl-highlight");
		}
		else {
			$("li:last", $typeaheadUl).addClass("pl-highlight");
		}

		// If this item if the section heading, skip it and goto the next one.
		if ($typeaheadUl.find("li.pl-highlight").hasClass("typeahead-nooption")) {
			gotoPrevTypeaheadResult();
		}
	}


	function setInputFieldValue () {
		// Set active dedcendent attr. on field to tell ATs this one is active so they read it since we don't
		//  focus on it, then change the text in the text field.
		var $highlightedLi = $typeaheadUl.find("li.pl-highlight");
		
		$inputField.attr("aria-activedescendant", $highlightedLi.attr("id"));

		$inputField.val($highlightedLi.text());
	}


	// Onload, setup bindings and fields.
	$(setupFields);

})(jQuery);
