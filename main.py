# -*- coding: utf-8 -*-

import httplib2
import json
import os
import re

import isodate

import apiclient.discovery
import oauth2client.client
import oauth2client.file
import oauth2client.tools

import tornado.ioloop
import tornado.web
import tornado.websocket

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
OAUTH_STORAGE_FILE = os.path.join(os.path.dirname(__file__), 'oauth2.json')

YOUTUBE_READ_SCOPE = 'https://www.googleapis.com/auth/youtube.readonly'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

DISLIKE_LIMIT = 3

api = None

clients = []
dislike = []
volumechange = []
volume = 50
queue = []

def broadcast():
	message = json.dumps({'queue': queue, 'dislike': len(dislike), 'limit': DISLIKE_LIMIT, 'volume': volume})
	for client in clients:
		client.write_message(message)

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		return self.render(os.path.join('templates', 'index.html'), error = '')

	def post(self):
		url = self.get_argument('url')
		match = re.match('^https?://www.youtube.com/watch\?v=([^?&]*)', url)
		error = ''

		if match:
			id = match.group(1)

			if not filter(lambda x: x['id'] == id, queue):
				movie = api.videos().list(part = 'snippet,contentDetails', id = id).execute()

				if len(movie['items']):
					movie = movie['items'][0]
					title = movie['snippet']['title']
					duration = str(isodate.parse_duration(movie['contentDetails']['duration']))

					queue.append({'id': id, 'title': title, 'duration': duration,})
					broadcast()
				else:
					error = 'Not found'
			else:
				error = 'The movie is already in queue'
		else:
			error = 'Invalid URL'

		return self.render(os.path.join('templates', 'index.html'), error = error)

class MonitorHandler(tornado.web.RequestHandler):
	def get(self):
		return self.render(os.path.join('templates', 'monitor.html'))

class WebSocketHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		if self not in clients:
			clients.append(self)
			self.write_message({'queue': queue, 'dislike': len(dislike), 'limit': DISLIKE_LIMIT, 'volume': volume})

	def on_message(self, message):
		global queue, dislike, volumechange, volume

		message = json.loads(message)
		if 'finish' in message and message['finish'] == queue[0]['id']:
			queue = queue[1:]
			dislike = []
			volumechange = []
			volume = 50
			broadcast()
		elif 'dislike' in message:
			ip = self.request.headers.get('X-Forwarded-For', self.request.headers.get('X-Real-Ip', self.request.remote_ip))
			if ip not in dislike:
				dislike.append(ip)
				if len(dislike) >= DISLIKE_LIMIT:
					queue = queue[1:]
					dislike = []
				broadcast()
		elif 'volumeup' in message or 'volumedown' in message:
			ip = self.request.headers.get('X-Forwarded-For', self.request.headers.get('X-Real-Ip', self.request.remote_ip))
			if ip not in volumechange:
				volumechange.append(ip)
				if 'volumeup' in message:
					volume = min(100, volume + 20)
				else:
					volume = max(0, volume - 20)
				broadcast()

	def on_close(self):
		if self in clients:
			clients.remove(self)

	def on_error(self):
		if self in clients:
			clients.remove(self)


if __name__ == '__main__':
	flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope = YOUTUBE_READ_SCOPE)

	storage = oauth2client.file.Storage(OAUTH_STORAGE_FILE)
	credentials = storage.get()
	if credentials is None or credentials.invalid:
		credentials = oauth2client.tools.run_flow(flow, storage, oauth2client.tools.argparser.parse_args())

	api = apiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http = credentials.authorize(httplib2.Http()))

	application = tornado.web.Application([
		(r'/', MainHandler),
		(r'/monitor', MonitorHandler),
		(r'/websocket', WebSocketHandler),
	], static_path = os.path.join(os.path.dirname(__file__), 'static'))

	application.listen(23456)
	tornado.ioloop.IOLoop.instance().start()
