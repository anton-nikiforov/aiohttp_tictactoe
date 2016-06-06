
var host = location.origin.replace(/^http/, 'ws')
var ws = new WebSocket(host +"/ws");

var _c = function(a){return $(document.createElement(a))},
	addMessage = function(text) {$('#log').append(_c('div').text(text));};

ws.onopen = function() {
    addMessage('Connection opened.');
};
ws.onmessage = function(event) {
   addMessage(event);
   console.log(event);
};
ws.onclose = function() {
	addMessage('Connection closed.');
};