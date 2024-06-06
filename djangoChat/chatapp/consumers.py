import json
import logging
from channels.generic.websocket import WebsocketConsumer, AsyncConsumer
from asgiref.sync import async_to_sync
from .models import Messages, ChatGroup

logger = logging.getLogger(__name__)


# Note:- This comsumer is making use of publisher/subscriber model.
class ChatConsumer(WebsocketConsumer):

    def connect(self):
        '''
            This method will handsake with the client and form a connection to get hold to the connection.
        '''
        # Get room name from websocket url route
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # Create a room group so we can gather multiple clients under one group.
        self.room_group_name = f"chat_{self.room_name}"
        
        self.room, created = ChatGroup.objects.get_or_create(
            name=self.room_group_name
        )

        if created:
            self.room.owner = self.user
            self.room.save()

        self.room.users.add(self.user)

        # Add Group into websocket channel layer.        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"Connected to the room {self.room_name}")

        # Handshake and hold the websocket connection.
        self.accept()


    def disconnect(self, closed_code):
        '''
            This method will terminate the websocker connection and will get terminated for both parties.
        '''

        # Disconnect wensocker and remove from the channel layer.
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"Disconnected from {self.room_name}")

    
    def receive(self, text_data):
        '''
            Recieve messages from websocket and pass it to the handler.    
        '''
        # convert json into python supported data structure.
        content = json.loads(text_data)
        message = content["message"]

        response = {
            "type": "chat_handler",
            "author": self.scope["user"].username,
            "message": message
        }

        room = self.user.chatgroups.get(name=self.room_group_name)

        message = Messages.objects.create(
            message=message,
            author=self.user,
            room=self.room
        )

        # Send message to the handler
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            response
        )

    def chat_handler(self, event):

        # Send message to WebSocket
        self.send(text_data=json.dumps(event))

    @property
    def user(self):
        user = self.scope['user']
        return user

class DirectMessageConsumer(WebsocketConsumer):
    connected_clients = set()

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        self.connected_clients.add(self)

        self.accept()

    def disconnect(self, code):
        logger.info("Disconnected..")
        self.connected_client.remove(self)

    def receive(self, text_data):
        content = json.loads(text_data)
        print(self.scope['user'])
        message = content['message']
        author = self.scope['user'].username
        
        self.send_message(author, message)

    def send_message(self, author, message):
        for client in self.connected_clients:
            client.send(text_data=json.dumps({"author": author, "message": message}))


