import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import openai
from django.conf import settings
openai.api_key = settings.OPEN_AI_KEY
from . import tasks



class ChatConsumer(WebsocketConsumer):
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        response_message = message
        try:
            temp = openai.Completion.create(
                engine="ada",
                prompt="anyway i talked to priyesh today",
                max_tokens=10
            )

            rsp_msg = temp["choices"][0]["text"]
            response_message = rsp_msg
        except Exception as e:
            response_message = e
        async_to_sync(self.channel_layer.send)(
                self.channel_name,
                {
                    'type': 'chat_message',
                    'message': response_message
                }
            )

    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': f'[bot]: {message}'
        }))
