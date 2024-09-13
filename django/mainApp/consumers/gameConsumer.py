from channels.generic.websocket import AsyncWebsocketConsumer

from .gameConsumerUtils.handlePaddleMove import handlePaddleMove
from .gameConsumerUtils.handleInitGame import handleInitGame

import json

gameSettingsInstances = {}
class GameConsumer(AsyncWebsocketConsumer):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.gameSettingsInstances = gameSettingsInstances

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
			self.game_group_name,
			self.channel_name
		)

	async def connect(self):
		
		self.game_id = self.scope['url_route']['kwargs']['game_id']
		self.game_group_name = f'game_{self.game_id}'

		await self.channel_layer.group_add(
			self.game_group_name,
			self.channel_name
		)

		await self.accept()

	# Called by server when a message is received from the group
	async def reload_page(self, event):
		event_msg = json.dumps(event)
		await self.send(text_data=event_msg)

	async def init_paddle_position(self, event):
		event_msg = json.dumps(event)
		await self.send(text_data=event_msg)

	async def update_ball_position(self, event):
		event_msg = json.dumps(event)
		await self.send(text_data=event_msg)

	async def update_paddle_position(self, event):
		event_msg = json.dumps(event)
		await self.send(text_data=event_msg)

	async def update_score(self, event):
		event_msg = json.dumps(event)
		await self.send(text_data=event_msg)

	async def receive(self, text_data):
		message = json.loads(text_data)
		gameID = self.scope['url_route']['kwargs']['game_id']

		message_type = message['type']

		if message_type.startswith('init_'):
			await handleInitGame(self, gameID, message_type, message['playerID'])

		elif message_type == 'paddle_move':
			gameSettings = self.gameSettingsInstances[gameID]
			await handlePaddleMove(self, message, gameSettings, message['playerID'])

		elif message_type == 'reload_page':
			await self.channel_layer.group_send(
				self.game_group_name,
				{
					'type': 'reload_page',
					'playerID': message['playerID']
				}
			)
	async def game_over(self, event):
		event_msg = json.dumps(event)
		await self.send(text_data=event_msg)
