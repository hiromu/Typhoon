var hostname = 'ws://' + location.hostname + ':' + location.port + '/websocket';

var id;
var title;
var ws;
var player;

function onYouTubePlayerAPIReady() {
	player = new YT.Player('player', {
		height: '768',
		width: '1024',
		playerVars: {
			'controls': 0,
			'disablekb': 1
		},
		events: {
			'onReady': onPlayerReady,
			'onStateChange': onPlayerStateChange
		}
	});
}

function onPlayerReady(event) {
	event.target.playVideo();
}

function onPlayerStateChange(event) {
	if(event.data == 0)
		ws.send(JSON.stringify({'finish': id}));
}

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
		for(var i = 0; i < songs.length; i++) {
			var tr = $('<tr>');

			if(i == 0)
				tr.append($('<td>').text('Now'));
			else
				tr.append($('<td>').text(i));

			tr.append($('<td>').text(songs[i].title));
			tr.append($('<td>').text(songs[i].duration));
			table.append(tr);
		}
		
		if(songs.length == 0) {
			id = null;
			document.title = title;
			player.stopVideo();
		} else if(songs[0].id != id) {
			id = songs[0].id;
			document.title = songs[0].title + ' - ' + title;
			player.loadVideoById(id);
		}
	}
	
	title = document.title;
}
