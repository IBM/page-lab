
(function($) {
	var $inputField = {},
		$searchForm = {};

	function setupFields () {
		$inputField = $("#pl-substring-search");
		$searchForm = $inputField.closest("form");

        $searchForm.on("submit", function (evt) {
            evt.preventDefault();
            window.location.href = "{% url 'plr:reports_browse' %}?filter=" + $inputField[0].value;
        });
	}
	$(setupFields);

})(jQuery);
