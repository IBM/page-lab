(function ($, PL) {

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
    
    
    function bindLinks () {
        $(document.body).on("click", "a", function (evt) {
            if (evt.currentTarget.classList.contains("pl-open-lighthouse-report")) {
                evt.preventDefault();
                
                // Get the run ID, 
                // Hit our API to get the Lighthouse raw data object,
                // Pass the object to the Lighthouse Viewer function.
                // Boom.
                var xhr = new XMLHttpRequest();
                xhr.open('GET', PL.urls.api_lighthouse_data + evt.currentTarget.dataset.runid + "/");
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        var data = JSON.parse(xhr.responseText);
                        PL.openTabAndSendJsonReport(data.results.rawData, PL.urls.report_lighthouse_viewer);
                    }
                    else {
                        alert("Woops, something happened and we couldn't get that report.");
                    }
                };
                xhr.send();                
            }
        });
    }


    $(bindLinks);
    
	
})(jQuery, PL);

