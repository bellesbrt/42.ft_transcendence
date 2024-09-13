from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

import json

class StatusConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.room_group_name = 'status'

		await self.channel_layer.group_add(
			self.room_group_name,
			self.channel_name
		)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
			self.room_group_name,
			self.channel_name
		)
		# Set user to offline
		user_id = self.scope["user"].id
		await self.set_user_offline(user_id)


	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		status = text_data_json.get('status')
		user_id = text_data_json.get('id')

		await self.channel_layer.group_send(
			self.room_group_name,
			{
				'type': 'status_update',
				'status': status,
				'id': user_id,
			}
		)


	async def status_update(self, event):
		user_id = event['id']
		status = event['status']

		await self.send(text_data=json.dumps({
			'id': user_id,
			'status': status,
		}))


	@database_sync_to_async
	def set_user_offline(self, user_id):
		User = get_user_model()
		try:
			user = User.objects.get(id=user_id)
			user.status = 'offline'
			user.save()

			# Send WebSocket message to all connected clients to inform it user is offline
			async_to_sync(self.channel_layer.group_send)
			(
				self.room_group_name,
				{
					'type': 'status_update',
					'status': 'offline',
					'id': user_id,
				}
			)
		except User.DoesNotExist:
			print(f"User of id {user_id} doesn't exist")
