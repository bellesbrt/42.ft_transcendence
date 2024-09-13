import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
	@database_sync_to_async
	def create_notification(self, channel, user):
		if channel.private:
			self._create_private_channel_notification(channel, user)
		else:
			self._create_public_channel_notification(channel, user)

	def _create_private_channel_notification(self, channel, user):
		from mainApp.models import Notification
		for other_user in channel.users.exclude(id=user.id):
			notification = Notification(
				user=user,
				type='message',
				imageType='user',
				imageUser=other_user.photo.url,
				title="New message",
				message=other_user.username,
				redirect=f"/chat/{self.room_id}"
			)
			notification.save()

	def _create_public_channel_notification(self, channel, user):
		from mainApp.models import Notification
		notification = Notification(
			user=user,
			type='message',
			imageType='message',
			title="New message",
			message=channel.name,
			redirect=f"/chat/{self.room_id}"
		)
		notification.save()


	@database_sync_to_async
	def get_users(self, room_id):
		users = []
		from mainApp.models import Channel
		try:
			channel = Channel.objects.get(room_id=room_id)
			for user in channel.users.all():
				if user.id != self.scope['user'].id:
					users.append(user)
			return users
		except Channel.DoesNotExist:
			return None


	@database_sync_to_async
	def change_status_to_online(self):
		User = get_user_model()
		user = User.objects.get(id=self.scope['user'].id)
		user.set_status('online')

	async def connect(self):
		self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
		self.room_group_name = f"chat_{self.room_id}"
		# Join room group
		await self.channel_layer.group_add(self.room_group_name, self.channel_name)
		await self.accept()

	@database_sync_to_async
	def update_last_interaction(self, room_id):
		from mainApp.models import Channel
		channel = Channel.objects.get(room_id=room_id)
		channel.last_interaction = timezone.now()
		channel.save()

	async def disconnect(self, close_code):
		await self.change_status_to_online()
		await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
		self.room_group_name = None
		self.room_id = None

	async def receive(self, text_data):
		"""
		Receive a message from the WebSocket and handle it accordingly.
		"""
		text_data_json = json.loads(text_data)
		username = text_data_json.get("username")
		message = text_data_json.get("message")
		text_data_json = json.loads(text_data)
		sender = text_data_json.get("sender")
		timestamp = timezone.localtime().strftime("%d-%m-%Y %H:%M")

		# Save message
		await self.save_message(sender, message)

		# Get channel
		channel = await self.get_channel()
		if channel is None:
			return

		# Get users
		usersToSend = await self.get_users(self.room_id)

		# Send notification to users
		if usersToSend is not None:
			for user in usersToSend:
				if user.status != f"chat:{self.room_id}":
					if self.scope['user'].id not in user.blockedUsers:
						await self.create_notification(channel, user)
		await self.update_last_interaction(self.room_id)

		# Send a message to room group
		await self.channel_layer.group_send(
			self.room_group_name, {
				"type": "chat_message",
				"message": message,
				"sender": sender,
				"username": username,
				"timestamp": timestamp
			}
		)


	@database_sync_to_async
	def save_message(self, sender, message):
		from mainApp.models import Channel, Message
		# Get channel
		try:
			channel = Channel.objects.get(room_id=self.room_id)
		except Channel.DoesNotExist:
			return
		# Save message
		Message.objects.create(sender_id=sender, message=message, channel=channel)


	@database_sync_to_async
	def get_channel(self):
		from mainApp.models import Channel

		try:
			return Channel.objects.get(room_id=self.room_id)
		except Channel.DoesNotExist:
			return None


	async def chat_message(self, event):
		"""
		Receive a chat message from the room group and send it to connected WebSocket clients.
		"""
		username = event.get("username")
		sender = event.get("sender")
		message = event.get("message")

		message_data = {
			"message": message,
			"sender": sender,
			"username": username,
		}
		# Send message to WebSocket
		await self.send(text_data=json.dumps(message_data))
