from django.shortcuts import render
from django.http import JsonResponse
#redirection vers la page de dashbord,juste recuperer le token via le url dans le lien de la validation
from django.shortcuts import redirect
# importation de l'user
from .models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
# token
from rest_framework_simplejwt.tokens import RefreshToken
# login and sing up
from django.contrib.auth import authenticate, login , get_user_model
# SEND EMAIL
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
import json
# OTP 
import random
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import User
from rest_framework.decorators import api_view
# show people
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer

from rest_framework.response import Response
User = get_user_model()

# REGISTER
@api_view(['POST'])
def register_view(request):
    data = request.data

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not email:
        return JsonResponse({'error': 'Email requis'}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Email déjà utilisé'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username déjà utilisé'}, status=400)

    user = User.objects.create_user(
        email=email,
        username=username,
        password=password
    )
    user.is_active = False
    user.save()

    # génération lien activation
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_link = f"http://127.0.0.1:8000/accounts/activate/{uid}/{token}/"

    send_mail(
        "Activation de votre compte",
        f"Bonjour {username}, cliquez ici : {activation_link}",
        None,
        [email],
    )

    return JsonResponse({
        'message': 'Compte créé. Vérifiez votre email.'
    }, status=201)



# LOGIN 
@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, username=email, password=password)

    if user is None:
        return JsonResponse({"error": "Identifiants invalides"}, status=401)

    if not user.is_active:
        return JsonResponse({"error": "Compte non activé"}, status=403)

    # 🔥 OTP
    otp = str(random.randint(100000, 999999))

    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()

    send_mail(
        "Votre code OTP",
        f"Votre code est : {otp}",
        None,
        [user.email],
    )

    return JsonResponse({
        "message": "OTP envoyé"
    })


# VERIFY OTP 
@api_view(['POST'])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not email or not otp:
        return JsonResponse({"error": "Email et OTP requis"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Utilisateur introuvable"}, status=404)

    # Vérifier que OTP et OTP_created_at existent
    if not user.otp or not user.otp_created_at:
        return JsonResponse({"error": "Aucun OTP généré pour cet utilisateur"}, status=400)

    # Comparer OTP
    if user.otp != otp:
        return JsonResponse({"error": "OTP invalide"}, status=400)

    # Vérifier expiration
    if timezone.now() > user.otp_created_at + timedelta(minutes=5):
        return JsonResponse({"error": "OTP expiré"}, status=400)

    # Réinitialiser OTP après usage
    user.otp = None
    user.otp_created_at = None
    user.save()

    # Génération JWT
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    # Retourner tokens + user (id, email, username)
    return JsonResponse({
        "refresh": str(refresh),
        "access": access,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }
    }, status=status.HTTP_200_OK)

# ACTIVATE ACCOUNT 
def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):
        user = None

    if user and not user.is_active and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # JWT
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh = str(refresh)

        # REDIRECTION VERS REACT
        return redirect(
            f"http://localhost:5173/activate-success?access={access}&refresh={refresh}"
        )

    return redirect("http://localhost:5173/activate-error")

# afficher tous les users de la base afin d'envoyer des message
class UserListView(APIView):
    permission_classes = [IsAuthenticated] # Commente ceci juste pour 1 test
    
    def get(self, request):
        print(f"DEBUG: Header Auth -> {request.headers.get('Authorization')}")
        print(f"DEBUG: User -> {request.user}") 
        
        users = User.objects.exclude(id=request.user.id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)