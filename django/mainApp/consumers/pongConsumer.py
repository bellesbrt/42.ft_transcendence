from channels.generic.websocket import AsyncWebsocketConsumer
from ..pongFunctions.handlerInitGame import handle_init_game
from ..pongFunctions.handlerPaddleMove import handle_paddle_move
from ..pongFunctions.gameSettingsClass import GameSettings
import json

class PongConsumer(AsyncWebsocketConsumer):

	gameSettings = GameSettings(800)

	async def disconnect(self, close_code):
		if self.gameSettings.ball.task:
			self.gameSettings.ball.task.cancel()

	async def connect(self):
		await self.accept()

	async def receive(self, text_data):
		message = json.loads(text_data)
		message_type = message.get('type')

		if message_type == 'init_local_game':
			self.gameSettings.setNbPaddles(2)
			await handle_init_game(self, message_type)

		elif message_type == 'init_ai_game':
			self.gameSettings.setNbPaddles(2)
			self.gameSettings.setIsAIGame(True)
			await handle_init_game(self, message_type)

		elif message_type == 'paddle_move':
			await handle_paddle_move(message, self)
