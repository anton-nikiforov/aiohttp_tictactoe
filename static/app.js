
$(function() {

	var game = $('#game'), ws_url = game.data('url');

	if(!ws_url) {
		throw 'Improperly configured: url is required.';
	}

	if(!!game.data('in-game')) {
		var ws = new WebSocket(location.origin.replace(/^http/, 'ws') + ws_url),
			_c = function(a){return $(document.createElement(a))},
			addMessage = function(text) {$('#log').append(_c('div').text(text));};

		ws.onopen = function() {
		    addMessage('Connection opened.');

		    $(document).on('click', '.game__field button', function() {
		    	var _this = $(this);
		    	context = {
		    		'i': _this.data('i'),
		    		'j': _this.data('j')
		    	};
		    	ws.send(JSON.stringify(context));
		    });
		};
		ws.onmessage = function(event) {
		   addMessage(event);
		   console.log(event);
		};
		ws.onclose = function() {
			addMessage('Connection closed.');
		};
	}
	else {
		$('.game__field button').attr('disabled', 'disabled');
	}
});