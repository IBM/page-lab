(function ($, PL) {
    
    var compare = PL.namespace(PL, "compare");
    
    var $compareTray, 
        $compareTrayBody,
        $compareTrayCompareLink,
        maxCompareNum = 3,
        compareLs = {
            keyName: "pagelabCompare",
            get: function () {
                return PL.util.storage.getItem(this.keyName);
            },
            set: function (arr) {
                return PL.util.storage.setItem(this.keyName, arr);
            },
            add: function (id) {
                var id = parseInt(id,10),
                    arrIds = this.get() || [] ;
                
                // Prevent duplicates: If the item is already in the array, don't add it again.
                if (arrIds.indexOf(id) > -1) {
                    return arrIds;
                }
                else {
                    arrIds.push(id);
                    return this.set(arrIds);                    
                }
            },
            remove: function (id) {
                var arrIds = this.get() || [] ;
                    itemIndex = arrIds.indexOf(parseInt(id,10));
                
                if (itemIndex > -1) {
                    arrIds.splice(itemIndex, 1);                
                }
                return this.set(arrIds);
            }
        };
    
    // Set the above apis to be public callable via our PL namespace.  
    compare.storage = compareLs;
    
    
    /**
        Called whenever we add/remove an item, this shows or hides the tray.
        If there are no items to compare, tray is hidden because no need for it.
        If there are any items, compare tray is shown.
        
        @method activateTray
        @private        
    **/  
    function activateTray () {
        if (getNumItemsInTray() > 0) {
            document.body.classList.add("pl-compare-enabled");
        }
        else {
            document.body.classList.remove("pl-compare-enabled");
            $compareTray.removeClass("opened");
        }
    }
    
    
    /**
        Callback from "getItemHtml". 
        Does the actual injection of the item's HTML if it was returned properly.
        
        @method addToCompareTray
        @private
        @param data {Object/JSON} The data returned from the WSR (web service request).
    **/
    function addToCompareTray (data) {
        if (data && data.results && data.results.resultsHtml) {
            $compareTrayBody.append(data.results.resultsHtml);
            compareLs.add(data.results.id);
        }
        else {
            console.warn("Sorry, there was an error retrieving URL data for the compare tray.");
        }
        
        // Decide if we need to show/hide the tray and enable the 'compare' link.
        activateTray();
        enableCompareLink();
    }
    
    
    /**
        Evaluates and decides if the compare link should be active or not.
        If there is only 1 item in the tray, there's nothing to compare, so link is inactive.
        If there are >1 items in the tray, enables 'compare' link.
        
        @method enableCompareLink
        @private
    **/
    function enableCompareLink () {
        if (getNumItemsInTray() > 1) {
            $compareTrayCompareLink.addClass("enabled");
        }
        else {
            $compareTrayCompareLink.removeClass("enabled");
        }
    }
    
    
    /**
        Takes the URL's id and retrieves the HTML snippet to use and add to the compare tray.
        
        @method getItemHtml
        @private
        @param id {Integer} The ID of a URL object.
    **/
    function getItemHtml (id) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', PL.urls.api_compareinfo + "?id=" + id);
        xhr.onload = function() {
            if (xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                addToCompareTray(data);
            }
            else {
                console.warn("Sorry, there was an error receiving the URL's info for the compare tray.");
            }
        };
        xhr.send();
    }
    
    
    /**
        Helper util function that tells us # of items in the tray, used for decisions
          on whether to show the tray and 'compare' link or not, etc.
        We don't just check "compareLs.get().length" in case user has cookies off,
          (even though no-cookies prevents cross-page state, at least on-page will work.)
        
        @method getNumItemsInTray
        @private
        @return {Integer} The # of items currently in the tray.
    **/
    function getNumItemsInTray () {
        return $(".pl-compare-item").length;
    }
    
    
    /**
        Pre-check a URL's checkbox if it is in the localStorage list of items to compare.
        <br>This is called by each page that wants to have checkboxes setup to enable the user
          to select a UR to add to the compare tray.
          
        @method populateCompareTrayFromStorage
        @param $checkboxes {DOM elements/jQuery obj} A list of checkbox elements to test if one needs to be pre-checked.
    **/
    compare.preselectCheckbox = preselectCheckbox;
    function preselectCheckbox ($checkboxes) {
        $checkboxes.each(function () {
           var checkbox = this;
           
           if (compareLs.get() && compareLs.get().indexOf(parseInt(checkbox.value,10)) > -1) {
               $(checkbox).prop("checked", true);
           }
        });
    }
    
    
    /**
        Gets localStorage value (array IDs) and gets HTML for each and adds them to compare tray onload.
        Basically, this saves compare tray items across page loads, filters, sorts, 
          etc without losing items they want to compare.
        
        @method populateCompareTrayFromStorage
        @private
    **/
    function populateCompareTrayFromStorage () {
        var existingIds = compareLs.get();
        
        // For each ID in the array in LS, get the HTML and populate the compare tray.
        $.each(existingIds, function () {
            var id = this;
            getItemHtml(id);
        });
    }
    
    
    /**
        Removes a URL from the compare tray and unchecks the box (if it's currently on the page).
        
        @method removeFromCompareTray
        @private
        @param id {Integer} The ID of a URL object.
    **/
    function removeFromCompareTray (id) {
        $compareTray.find("[data-itemid='" + id + "']").remove();
        
        $("#id_" + id).prop("checked", false);
   
        compareLs.remove(id);

        activateTray();
        enableCompareLink();
    }
    
    
    /**
        Binds (via defer/bubbling) all checkboxes inside the passed element to enable them 
          to add/remove items in the compare tray.
        <br>This is called by each page that wants to have checkboxes setup to enable the user
          to select a UR to add to the compare tray.
        
        @method setupCompareCheckboxes
        @param $elContainer {DOM/jQuery object} DOM element to search thru and bind checkboxes 
          to be able to add/remove items to the compare tray.
    **/
    compare.setupCompareCheckboxes = setupCompareCheckboxes;
    function setupCompareCheckboxes ($elContainer) {
       $elContainer.on("change", "input", function (evt) {
            // If the box is checked, and there's an available slot, add the URL.
            if (this.checked === true) {
                if (getNumItemsInTray() === maxCompareNum) {
                    alert("You can only compare up to three URLs.");
                    $(this).prop("checked", false);
                    return;
                }
                else {
                    getItemHtml(this.value);    
                }
            }
            // Otherwise they unchecked it so remove the item.
            else {
                removeFromCompareTray(this.value);
            }
        });
    }
    
    
    /**
        Sets up ALL actions on the compare tray: Open/close, Remove item, Clear all, Compare link.
        Rather simply have them all in 1 defer/bubble binding than individual el bindings.
        
        @method setupCompareTrayActions
        @private
    **/
    function setupCompareTrayActions () {
        $compareTray.on("click", "a", function (evt) {
            // ALL TRAY LINKS handled here, so we kill default onclick no matter what.
            evt.preventDefault();
            
            // Open/close link (+/- on left.)
            if (this.className.indexOf("pl-compare-closetray") > -1 || this.className.indexOf("pl-compare-opentray") > -1) {
                $compareTray.toggleClass("opened");
            }
            // "Compare" link (in center.)
            else if (this.className.indexOf("pl-compare-comparelink") > -1) {
                var urlIds = "";
                
                if (getNumItemsInTray() < 2) {
                    return;
                }
                
                $(".pl-compare-item").each(function () {
                    urlIds += $(this).data("itemid") + "/";
                });
                
                document.location.href = PL.urls.home + "urls/compare/" + urlIds;
            }
            // "Clear all" link (on right side.)
            else if (this.className.indexOf("pl-compare-clearall") > -1) {
                $(".pl-compare-item").each(function () {
                    removeFromCompareTray($(this).data("itemid"));
                });
            } 
            // "Remove" link (above each item).
            else if (this.className.indexOf("pl-compare-item-remove") > -1) {
                removeFromCompareTray($(this).data("itemid"));
            }     
        });
    }
    
           
    // Showtime. 
    
    // Sanity check. If there's more than 3 items in LS, it's tainted, so kill it.
    if (compareLs.get() && compareLs.get().length > 3) {
        compareLs.set([]);
    }
    
    // Strictly sets up the tray. 
    // Checkbox bindings are util fuction each page calls as appropriate onload.
    $(function () {
        if (document.getElementById("pl-compare")) {
            $compareTray = $("#pl-compare");
            $compareTrayBody = $("#pl-compare-body");
            $compareTrayCompareLink = $(".pl-compare-comparelink-con")
            setupCompareTrayActions();
            populateCompareTrayFromStorage();
            activateTray();
        }
    });  
    
    
})(jQuery, PL);
