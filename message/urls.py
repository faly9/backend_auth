from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationView, ClientViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('conversation/<int:other_id>/', ConversationView.as_view(), name='chat-history'),
]
