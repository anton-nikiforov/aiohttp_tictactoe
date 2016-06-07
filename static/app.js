
$(function() {

	var game = $('#game'), ws_url = game.data('url');

	if(!ws_url) {
		throw 'Improperly configured: url is required.';
	}

	var ws = new WebSocket(location.origin.replace(/^http/, 'ws') + ws_url),
		_c = function(a){return $(document.createElement(a))},
		addMessage = function(text) {$('#log').append(_c('div').text(text));};

	ws.onopen = function() {
	    addMessage('ws: Connection opened.');

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
	   	data = $.parseJSON(event.data);

	   	addMessage(data.status+': '+data.message);
		console.log(data);

	   	if(data.status == window.STATUS['OK']) {
	   		$('#move_' + data.i + '_' + data.j)
	   			.text(data.current_user_id)
	   			.attr('disabled', 'disabled');

	   		if(!!data.winner_id) {
	   			$('.game__field button').attr('disabled', 'disabled');

	   			$('#player_' + data.winner_id).addClass('winner').append(_c('span').text(' is winner!'));
	   		}
	   	}
	};
	ws.onclose = function() {
		addMessage('ws: Connection closed.');
	};
	
	if(!game.data('in-game')) {	
		$('.game__field button').attr('disabled', 'disabled');
	}
});