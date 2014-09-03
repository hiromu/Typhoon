var hostname = 'ws://' + location.hostname + ':' + location.port + '/websocket';
var ws;
		
function init() {
	if (window['ReconnectingWebSocket'] != undefined)
		ws = new ReconnectingWebSocket(hostname);
	else
		ws = new WebSocket(hostname);
	
	ws.onmessage = function(message) {
		var data = JSON.parse(message.data);
		var songs = data.queue;
		$('#dislike').text(data.dislike + ' / ' + data.limit);
		
		var table = $('div.queue>table>tbody');
		table.children().remove();
		for (var i = 0; i < songs.length; i++) {
			var tr = $('<tr>');

			if (i == 0)
				tr.append($('<td>').text('Now'));
			else
				tr.append($('<td>').text(i));

			tr.append($('<td>').text(songs[i].title));
			tr.append($('<td>').text(songs[i].duration));
			table.append(tr);
		}
	}
}

function dislike() {
	ws.send(JSON.stringify({'dislike': 1}));
}
