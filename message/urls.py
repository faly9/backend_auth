from django.urls import path
from .views import ConversationView

urlpatterns = [
    # Exemple : http://127.0.0.1:8000/conversation/2/
    # (Le 2 est l'ID de la personne avec qui vous discutez)
    path('conversation/<int:other_id>/', ConversationView.as_view(), name='chat-history'),
]