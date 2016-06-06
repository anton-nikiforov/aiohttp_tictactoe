
$(function() {

	var game = $('#game'), ws_url = game.data('url');

	if(!ws_url) {
		throw 'Improperly configured: url is required.';
	}

	var ws = new WebSocket(location.origin.replace(/^http/, 'ws') + ws_url),
		_c = function(a){return $(document.createElement(a))},
		addMessage = function(text) {$('#log').append(_c('div').text(text));};

	ws.onopen = function() {
	    addMessage('Connection opened.');

    	if(!!game.data('in-game')) {
		    $(document).on('click', '.game__field button', function() {
		    	var _this = $(this);
		    	context = {
		    		'i': _this.data('i'),
		    		'j': _this.data('j')
		    	};
		    	ws.send(JSON.stringify(context));
		    });
		}
	};
	ws.onmessage = function(event) {
	   	addMessage(event.data);
   		console.log(event.data);

	   	data = $.parseJSON(event.data);

	   	if(!!data.status) {
	   		$('#move_' + data.i + '_' + data.j).text(game.data('user')).attr('disabled', 'disabled');
	   	}
	};
	ws.onclose = function() {
		addMessage('Connection closed.');
	};
	
	if(!game.data('in-game')) {	
		$('.game__field button').attr('disabled', 'disabled');
	}
});