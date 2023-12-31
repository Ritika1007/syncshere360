import json 
from asgiref.sync import async_to_sync,sync_to_async
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name #%s mean? https://www.geeksforgeeks.org/what-does-s-mean-in-a-python-format-string/
        #Join room group
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )
    
    #Receive message from WebSocket
    async def receive(self,text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        isTyping = text_data_json['isTyping']
        username = text_data_json['username']
        clickedSend = text_data_json['clickedSend']
        if isTyping == False and clickedSend == True:
            await sync_to_async(Message.objects.create)(room_name=self.room_name,username=username,message=message)
        #gets info and saves to channel layer group
        await self.channel_layer.group_send(
            self.room_group_name,{'type': 'chat_message','message': message,'isTyping':isTyping,'username':username,'clickedSend':clickedSend}
        )

    #Receive message from group
    async def chat_message(self,event):
        type,message,isTyping,username,clickedSend = event['type'],event['message'],event['isTyping'],event['username'],event['clickedSend']
        if isTyping or clickedSend == False:
            if username != str(self.scope['user']):
                if clickedSend == False and isTyping == True:
                    message = f"{username} is typing..."
                else:
                    message = '' 
            else:
                message = ''
        #Send message to WebSocket
        await self.send(text_data = json.dumps({'message':message,'isTyping':isTyping,'clickedSend':clickedSend,'username':username}))
