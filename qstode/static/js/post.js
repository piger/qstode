/*
 * Codice JQuery-UI per completion di tag e categorie, datepicker con
 * calendario per content_date.
 */

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
			/* Con questo posso giostrarmela con il jsonify() di
			 * Flask, che crea per forza un dict con una chiave, mentre
			 * jquery-ui si aspetta secca una lista.
			 */
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
				terms.push( ui.item.value );
				// add placeholder to get the comma-and-space at the end
				terms.push("");
				this.value = terms.join(", ");

				// move caret to end of line
				// http://stackoverflow.com/questions/4715762/javascript-move-caret-to-last-character
				if (typeof this.selectionStart == "number") {
					this.selectionStart = this.selectionEnd = this.value.length;
				} else if (typeof this.createTextRange != "undefined") {
					var range = this.createTextRange();
					range.collapse(false);
					range.select();
				}
				return false;
			},

			focus: function(event, ui) {
				// prevent value inserted on focus
				return false;
			}
		});

	$('.datepicker').datepicker();
});
