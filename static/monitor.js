var hostname = 'ws://' + location.hostname + '/websocket';

var id;
var ws;
var player;

function onYouTubePlayerAPIReady() {
	player = new YT.Player('player', {
		height: '768',
		width: '1024',
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
		ws.send('finish');
}

function init() {
	ws = new WebSocket(hostname);
	
	ws.onmessage = function(message) {
		var songs = JSON.parse(message.data).queue;
		var ol = document.getElementById('list');
		
		for(var i = ol.childNodes.length - 1; i > -1; i--)
			ol.removeChild(ol.childNodes[i]);
		
		for(var i = 0; i < songs.length; i++) {
			var element = document.createElement('li');
			element.innerText = songs[i].title + ' (' + songs[i].duration + ')';
			ol.appendChild(element);
		}
		
		if(songs.length == 0) {
			id = null;
			player.stopVideo();
		} else if(songs[0].id != id) {
			id = songs[0].id;
			player.loadVideoById(id);
		}
	}
	
	ws.onclose = function() {
		ws.close();
		ws = new WebSocket(hostname);
	}
	ws.onerror = function() {
		ws.close();
		ws = new WebSocket(hostname);
	}
}