# ChatApp
Simple Chat Application made with django, websockets and rabbitmq.

## Set Up and Installation (Must have Python3)

* Create a Folder for the Chat Application and add virtual environment
```bash
mkdir chat_app
cd chat_app
pipenv shell
```
* Clone the Repo
* Install requirements.txt
```bash
pip install -r requirements.txt
```
* Install Erlang and RabbitMQ
  Visit Erlang, RabitMQ websites and download from installer with default settings.
* Enable rabitMQ by going to (C:\Program Files\RabbitMQ Server\rabbitmq_server-x.x.x\sbin) in cmd and run 
```bash
rabbitmq-plugins.bat enable rabbitmq_management
``` 
* In terminal run makemigrations and migrations in django.
```bash
py manage.py makemigrations
py manage.py migrate
```
* Then create two superusers with command
```bash
py manage.py createsuperuser
```
* To enable two users to chat locally, you can log in as one user in a regular Chrome tab and as another user in an incognito tab. Each user must be logged in to the admin     panel to chat.
  Go to the admin Panel with `localhost/admin`

  And login with username and password of each user in different tabs that were created with createsuperuser command.
  Connect both users to the same chat room using URLs like: `localhost/chat/<chat_room_name>`
  
  This setup allows each user to be authenticated and participate in the same chat room for communication.

## Code documentation

#### Configuration
In your Django project's settings, you need to configure the ASGI application and set up the channel layers for WebSocket communication. Here's what each part does:
```python
ASGI_APPLICATION = 'config.asgi.application'
```
This setting specifies the ASGI application to use. ASGI stands for Asynchronous Server Gateway Interface, which is a specification for building asynchronous web applications with Python. The ASGI_APPLICATION setting points to the ASGI application callable, which in this case is located at config.asgi.application.
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": 'channels_rabbitmq.core.RabbitmqChannelLayer',
        "CONFIG": {
            "host": "amqp://guest:guest@127.0.0.1:5672/"
        }
    }
}
```
This configuration sets up the channel layer backend for Django Channels, which handles the asynchronous communication in your application. Here’s a breakdown of the components:

* default: This is the name of the channel layer configuration. You can define multiple channel layers if needed, but typically you will have one default layer.
* BACKEND: This specifies the backend to use for the channel layer. In this case, it is set to `channels_rabbitmq.core.RabbitmqChannelLayer`, indicating that RabbitMQ will be used as the message broker.
 CONFIG: This section contains the configuration details for connecting to RabbitMQ:
* host: This is the URL for the RabbitMQ server. `amqp://guest:guest@127.0.0.1:5672/` is the default connection string, where:
amqp is the protocol used by RabbitMQ.
* `guest:guest` are the default username and password for RabbitMQ.
127.0.0.1 is the localhost address, meaning RabbitMQ is running on the same machine as the application.
5672 is the default port for RabbitMQ.
* In summary, this configuration sets up your Django application to use RabbitMQ for handling WebSocket communication through Django Channels. The ASGI_APPLICATION setting specifies the entry point for the ASGI server, and CHANNEL_LAYERS configures RabbitMQ as the backend for the channels layer, enabling message passing between different parts of your application asynchronously.

#### ChatConsumer
```python
class ChatConsumer(WebsocketConsumer):
```
A consumer handling WebSocket connections for chat rooms using a publisher/subscriber model.
`connect` Method
```python
def connect(self):
    '''
        This method will handshake with the client and form a connection.
    '''
    # Get room name from websocket URL route
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

```
##### Purpose: 
* Establishes a WebSocket connection, associates the user with a chat group, and joins the group.
##### Steps:
* Extracts the room name from the URL.
* Creates or retrieves a ChatGroup object.
* Adds the user to the chat group.
* Registers the group with the channel layer.
* Accepts the WebSocket connection.

`disconnect` Method
```python
def disconnect(self, closed_code):
    '''
        This method will terminate the WebSocket connection for both parties.
    '''

    # Disconnect WebSocket and remove from the channel layer.
    async_to_sync(self.channel_layer.group_discard)(
        self.room_group_name,
        self.channel_name
    )

    logger.info(f"Disconnected from {self.room_name}")
```
##### Purpose: 
* Cleans up when a WebSocket connection is closed.
##### Steps:
* Removes the channel from the group in the channel layer.
* Logs the disconnection.

`receive` Method
```python
def receive(self, text_data):
    '''
        Receive messages from WebSocket and pass them to the handler.
    '''
    # Convert JSON into a Python-supported data structure.
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
```
##### Purpose: 
* Processes incoming messages from the WebSocket.
##### Steps:
* Parses the incoming JSON message.
* Creates a response dictionary.
* Saves the message to the database.
* Sends the message to the group handler.

`chat_handler` Method
```python
def chat_handler(self, event):
    '''
        Send message to WebSocket
    '''
    self.send(text_data=json.dumps(event))
```
##### Purpose: 
* Handles broadcasting messages to the WebSocket.
##### Steps:
* Converts the event dictionary to JSON and sends it through the WebSocket.

#### DirectMessageConsumer
```python
class DirectMessageConsumer(WebsocketConsumer):
    connected_clients = set()
```
A consumer handling direct messages between clients.

`connect` Method
```python
def connect(self):
    self.room_name = self.scope['url_route']['kwargs']['room_name']
    self.room_group_name = f"chat_{self.room_name}"

    self.connected_clients.add(self)

    self.accept()
```
##### Purpose: 
* Establishes a WebSocket connection and registers the client.
##### Steps:
* Extracts the room name from the URL.
* Adds the WebSocket connection to a set of connected clients.
* Accepts the WebSocket connection.

`disconnect` Method
```python
def disconnect(self, code):
    logger.info("Disconnected..")
    self.connected_clients.remove(self)
```
##### Purpose: 
* Cleans up when a WebSocket connection is closed.
##### Steps:
* Logs the disconnection.
* Removes the client from the set of connected clients.

`receive` Method
```python
def receive(self, text_data):
    content = json.loads(text_data)
    print(self.scope['user'])
    message = content['message']
    author = self.scope['user'].username
    
    self.send_message(author, message)
```
##### Purpose: 
* Processes incoming messages from the WebSocket.
##### Steps:
*Parses the incoming JSON message.
*Extracts the message and the author.
* Sends the message to all connected clients.

`send_message` Method
```python
def send_message(self, author, message):
    for client in self.connected_clients:
        client.send(text_data=json.dumps({"author": author, "message": message}))
```
##### Purpose: 
* Broadcasts messages to all connected clients.
##### Steps:
* Iterates over all connected clients.
* Sends the message as JSON to each client.


#### Websocket URL Patterns
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/direct/(?P<room_name>\w+)/$", consumers.DirectMessageConsumer.as_asgi())
]
```
Defines URL patterns for WebSocket connections in Django Channels.
`re_path`: Allows for regular expression-based URL routing.
`consumers`: Contains WebSocket consumer classes.
#### websocket_urlpatterns: List of URL patterns for WebSocket connections.
##### `re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi())`
##### Purpose: 
* Maps WebSocket connections for chat rooms to the ChatConsumer.
##### Pattern:
* /ws/chat/<room_name>/
* <room_name>: Parameter capturing the room name.
* Consumer: ChatConsumer: Handles WebSocket connections for chat rooms.
##### `re_path(r"ws/direct/(?P<room_name>\w+)/$", consumers.DirectMessageConsumer.as_asgi())`
##### Purpose: 
* Maps WebSocket connections for direct messages to the DirectMessageConsumer.
##### Pattern:
* /ws/direct/<room_name>/
* <room_name>: Parameter capturing the room name.
* Consumer: DirectMessageConsumer: Handles WebSocket connections for direct messages.
