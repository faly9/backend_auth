from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from .models import Message, Client
from .serializers import MessageSerializer, ClientSerializer

class ConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, other_id):
        user = request.user
        messages = Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=other_id)) |
            (Q(sender_id=other_id) & Q(receiver=user))
        ).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
