from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # Pour forcer la connexion
from django.db.models import Q
from .models import Message
from .serializers import MessageSerializer

class ConversationView(APIView):
    permission_classes = [IsAuthenticated] # Vérifie que le Token est valide

    def get(self, request, other_id):
        # L'utilisateur connecté est dans request.user
        user = request.user
        
        # Filtrage sécurisé
        messages = Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=other_id)) |
            (Q(sender_id=other_id) & Q(receiver=user))
        ).order_by('timestamp')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)