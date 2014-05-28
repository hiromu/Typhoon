# -*- coding: utf-8 -*-

import httplib2
import json
import re

import isodate

import apiclient.discovery
import oauth2client.client
import oauth2client.file
import oauth2client.tools

import tornado.ioloop
import tornado.web
import tornado.websocket

CLIENT_SECRETS_FILE = 'client_secrets.json'
YOUTUBE_READ_SCOPE = 'https://www.googleapis.com/auth/youtube.readonly'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
LIMIT = 3

api = None

clients = []
dislike = []
queue = []

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		return self.render('index.html', error = '')
		
	def post(self):
		url = self.get_argument('url')
		match = re.match('^https?://www.youtube.com/watch\?v=(.*)$', url)
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
					
					message = json.dumps({'queue': queue, 'dislike': len(dislike), 'limit': LIMIT})
					for client in clients:
						client.write_message(message)
				else:
					error = 'Not found'
			else:
				error = 'The movie is already in queue'
		else:
			error = 'Invalid URL'
			
		return self.render('index.html', error = error)

class MonitorHandler(tornado.web.RequestHandler):
	def get(self):
		return self.render('monitor.html')
		
class WebSocketHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		if self not in clients:
			clients.append(self)
			self.write_message({'queue': queue, 'dislike': len(dislike), 'limit': LIMIT})
	
	def on_message(self, message):
		global queue, dislike
		
		if message == 'finish':
			queue = queue[1:]
			self.update()
		elif message == 'dislike':
			ip = self.request.remote_ip
			if ip not in dislike:
				dislike.append(ip)
				if len(dislike) >= LIMIT:
					queue = queue[1:]
					dislike = []
				self.update()
	
	def update(self):
		message = json.dumps({'queue': queue, 'dislike': len(dislike), 'limit': LIMIT})
		for client in clients:
			client.write_message(message)
			
	def on_close(self):
		if self in clients:
			clients.remove(self)
	
	def on_error(self):
		if self in clients:
			clients.remove(self)

application = tornado.web.Application([
	(r'/', MainHandler),
	(r'/monitor', MonitorHandler),
	(r'/list', WebSocketHandler),
])

if __name__ == '__main__':
	flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope = YOUTUBE_READ_SCOPE)
	
	storage = oauth2client.file.Storage('oauth2.json')
	credentials = storage.get()
	if credentials is None or credentials.invalid:
		credentials = oauth2client.tools.run_flow(flow, storage, oauth2client.tools.argparser.parse_args())
	
	api = apiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http = credentials.authorize(httplib2.Http()))
	
	application.listen(80)
	tornado.ioloop.IOLoop.instance().start()