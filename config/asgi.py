import os
import django # <--- Ajouté
from django.core.asgi import get_asgi_application

# 1. On définit d'abord le module de réglages
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. On initialise Django (indispensable pour charger les modèles)
django.setup() # <--- Ajouté

# 3. Maintenant on peut importer le reste sans erreur
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import message.routing 

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            message.routing.websocket_urlpatterns
        )
    ),
})