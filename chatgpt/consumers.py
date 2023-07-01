"""
    handle the consumers
"""
#pylint:disable=W0201,W0221,E1101
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage, ChatThread



class ChatConsumer(AsyncWebsocketConsumer):
    """
        chat consumer class
    """
    async def connect(self):
        """
            connect ti websocket
        """
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = self.room_name

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        """
            Disconect 
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        """
            receivesa the message
        """
        text_data_json = json.loads(text_data)
        iden_user = text_data_json["iden_user"]
        message = text_data_json["message"]
        await self.save_message_to_database(message)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message, "iden_user": iden_user},
        )

    # Receive message from room group
    async def chat_message(self, event):
        """
            chat with people
        """
        message = event["message"]
        iden_user = event["iden_user"]
        await self.send(
            text_data=json.dumps({"message": message, "iden_user": iden_user})
        )

    @database_sync_to_async
    def save_message_to_database(self, message):
        """
            chat message save to db
        """
        thread_id = self.room_name
        chat_thread = ChatThread.objects.filter(thread_id=thread_id).first()
        sender = self.scope["user"]
        receiver = chat_thread.second_person
        chat_message = ChatMessage(
            thread=chat_thread, sender=sender, receiver=receiver, message=message
        )
        chat_message.save()
