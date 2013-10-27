/*
 * Codice JQuery-UI per completion di tag e categorie, datepicker con
 * calendario per content_date.
 */

$(function() {
	$("#tags")
	// don't navigate away from the field on tab when selecting an item
		.bind( "keydown", function( event ) {
			if ( event.keyCode == $.ui.keyCode.TAB &&
				 $( this ).data( "autocomplete" ).menu.active ){
					 event.preventDefault();

				 }
			/* Questo sarebbe il codice per i suggerimenti.
			 } else if ( event.keyCode == $.ui.keyCode.COMMA ) {
			 tags = this.value;
			 $.ajax({
			 url: url_autocomplete_suggestions,
			 dataType: 'json',
			 data: {
			 term: tags
			 },
			 success: function(data) {
			 nomi = new Array(), i;

			 for (var i=0; i < data.results.length; i++) {
			 nomi.push(data.results[i].label);
			 }

			 $("#tags-suggestions-text").text(nomi.join(', '));
			 }
			 });
			 }
			 */
		})
		.autocomplete({
			minLength: 0,
			/*
			 source: function( request, response ) {
			 $.getJSON("{{ url_for('complete_tags') }}", {
			 term: extract_last( request.term )
			 }, response );
			 },
			 */
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
