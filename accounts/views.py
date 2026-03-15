from django.shortcuts import render
from django.http import JsonResponse
# importation de l'user
from .models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
# token
from rest_framework_simplejwt.tokens import RefreshToken
# login and sing up
from django.contrib.auth import authenticate, login
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
# show peaple
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer

from rest_framework.response import Response

@api_view(["GET"])
def hello_api(request):
    return Response({"message": "Salut depuis Django !"})

@api_view(['POST'])
def register_view(request):
    try:
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not email:
            return JsonResponse({'error': 'Email must be set'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = User.objects.create_user(email=email, username=username, password=password)
        user.is_active = False
        user.save()

        # génération token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        activation_link = f"http://127.0.0.1:8000/accounts/activate/{uid}/{token}/"

        send_mail(
            "Activation de votre compte",
            f"Bonjour {username}, cliquez sur ce lien pour activer votre compte:\n{activation_link}",
            None,
            [email],
            fail_silently=False
        )

        return JsonResponse({
            'message': 'Utilisateur créé. Vérifiez votre email pour activer votre compte.'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@api_view(['POST'])
def login_view(request):

    data = request.data
    email = data.get('email')
    password = data.get('password')

    user = authenticate(request, username=email, password=password)

    if user is None:
        return JsonResponse({"message": "Identifiants invalides"}, status=401)

    if not user.is_active:
        return JsonResponse({"message": "Compte non activé"}, status=403)

    # génération OTP
    otp = str(random.randint(100000, 999999))

    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()

    send_mail(
        "Votre code OTP",
        f"Votre code de connexion est : {otp}",
        None,
        [user.email],
        fail_silently=False
    )

    return JsonResponse({
        "message": "OTP envoyé à votre email"
    })

@api_view(['POST'])
def verify_otp(request):

    email = request.data.get("email")
    otp = request.data.get("otp")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Utilisateur introuvable"}, status=404)

    if user.otp != otp:
        return JsonResponse({"error": "OTP invalide"}, status=400)

    refresh = RefreshToken.for_user(user)

    return JsonResponse({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id" : user.id,
        "email": user.email
    })

@csrf_exempt
def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return JsonResponse({"message": "Compte activé avec succès !"})

    return JsonResponse({"error": "Lien invalide"})


# afficher tous les users de la base afin d'envoyer des message
class UserListView(APIView):
    permission_classes = [IsAuthenticated] # Commente ceci juste pour 1 test
    
    def get(self, request):
        print(f"DEBUG: Header Auth -> {request.headers.get('Authorization')}")
        print(f"DEBUG: User -> {request.user}") 
        
        users = User.objects.exclude(id=request.user.id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)