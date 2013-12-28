$(function() {
	$("#tags")
	    // don't navigate away from the field on tab when selecting an item
		.bind( "keydown", function( event ) {
			if ( event.keyCode == $.ui.keyCode.TAB &&
				 $( this ).data("ui-autocomplete").menu.active ){
					 event.preventDefault();

				 }
		})
		.autocomplete({
			minLength: 0,
			source: function(request, response) {
				$.ajax({
					url: url_autocomplete_tags,
					dataType: "json",
					data: {
						term: extract_last(request.term)
					},
					success: function(data) {
						response( $.map(data.results, function(item) {
							return {
								label: item.label,
								value: item.value
							};
						}));
					}
				});
			},

			select: function(event, ui) {
				var terms = comma_split( this.value );
				// removes the current input
				terms.pop();
				// add the selected item
				terms.push(ui.item.value);
				// add placeholder to get the comma-and-space at the end
				terms.push("");
				this.value = terms.join(", ");

				// Move caret and focus to the end of the input box;
				// this doesn't work in Chrome! :(
				$(this).caretToEnd();

				// Canceling this event prevents the value from being
				// updated, but does not prevent the menu from
				// closing.
				return false;
			},

			focus: function(event, ui) {
				// prevent value inserted on focus
				return false;
			}
		});
});
