/* JS globale di QStode */

/* Funzioni per completion & co */

function comma_split(val) {
	return val.split(/,\s*/);
}

function extract_last(term) {
	return comma_split(term).pop();
}

function is_https() {
	return window.location.protocol == 'https:';
}

/* Codice DOM-dipendente */
$(function() {

	/* tooltip per il search Form sulla navbar */
	$('#query').tooltip({
		title: "Inserire una o piu' tag, separate da virgola",
		placement: 'bottom'
	});

	// completion per search nella navbar
	$(".search-query")
	// don't navigate away from the field on tab when selecting an item
		.bind( "keydown", function( event ) {
			if ( event.keyCode == $.ui.keyCode.TAB &&
				 $( this ).data( "ui-autocomplete" ).menu.active ){
					 event.preventDefault();
				 }
		})
		.autocomplete({
			minLength: 0,
			/* Con questo posso giostrarmela con il jsonify() di Flask, che crea per forza un dict con una chiave,
			 mentre jquery-ui si aspetta secca una lista.
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
				return false;
			},

			focus: function() {
				// prevent value inserted on focus
				return false;
			}
		});


	$(".bookmarklet").popover({
		trigger: "hover",
		content: "Devi trascinare questo link nella barra degli indirizzi del tuo browser (Firefox, Safari, ...)."
	});

});
