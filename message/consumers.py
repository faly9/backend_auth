# message/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from django.contrib.auth import get_user_model
User = get_user_model() # À mettre ici pour qu'il soit global au fichier
# ⚠️ Important : définir User avant la classe
class PrivateChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.user_id = int(self.scope['url_route']['kwargs']['user_id'])
        except KeyError:
            await self.close()
            return

        self.group_name = f"user_{self.user_id}"

        # Joindre le groupe de l'utilisateur
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accepter la connexion WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        # Retirer le consommateur du groupe
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            receiver_id = int(data.get("receiver"))

            if not message:
                # Ignorer les messages vides
                return

            # Récupérer sender et receiver depuis la base
            sender = await User.objects.aget(id=self.user_id)
            receiver = await User.objects.aget(id=receiver_id)

            # Sauvegarder le message dans la base
            await Message.objects.acreate(sender=sender, receiver=receiver, content=message)

            # Envoyer le message au destinataire via le channel layer
            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    "type": "send_message",
                    "message": message,
                    "sender": self.user_id,
                    
                }
            )
        except Exception as e:
            # Debug : imprime l'erreur côté serveur pour développement
            print(f"[WebSocket ERROR] {e}")

    async def send_message(self, event):
        try:
            await self.send(text_data=json.dumps({
                "message": event.get("message"),
                "sender": event.get("sender"),
            }))
        except Exception as e:
            print(f"[Send ERROR] {e}")
