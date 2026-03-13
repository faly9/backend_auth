import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PrivateChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
# connection en permanence avec le serveur backend
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"user_{self.user_id}"

# rejoindre le groupe,chaque user a son groupe
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
# tant que le browser se ferme , le consumer le retire dans le groupe et n envoie pas les messages 
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

# le consumer recoit le message depuis le frontend et le transforme en dictionnaire python au lieu de JSON
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        receiver = data['receiver']

# envoyer le message au destinataire
        await self.channel_layer.group_send(
            f"user_{receiver}",
            {
                'type': 'send_message',
                'message': message
            }
        )

# redis et le websocket envoie le message vers le destinataire
    async def send_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))