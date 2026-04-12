from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import UserSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    data = request.data

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not email:
        return Response({'error': 'Email requis'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email déjà utilisé'}, status=400)

    if username and User.objects.filter(username=username).exists():
        return Response({'error': 'Username déjà utilisé'}, status=400)

    user = User.objects.create_user(
        email=email,
        username=username or email.split('@')[0],
        password=password
    )
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_link = f"http://127.0.0.1:8000/accounts/activate/{uid}/{token}/"

    send_mail(
        "Activation de votre compte",
        f"Bonjour, cliquez ici pour activer :\n{activation_link}",
        None,
        [email],
    )

    return Response({
        'message': 'Compte créé. Vérifiez votre email.'
    }, status=201)


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and not user.is_active and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh_str = str(refresh)

        return redirect(
            f"http://localhost:3000/activate-success?access={access}&refresh={refresh_str}"
        )

    return redirect("http://localhost:3000/activate-error")


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email et mot de passe requis"}, status=400)

    user = authenticate(request, username=email, password=password)

    if user is None:
        return Response({"error": "Identifiants invalides"}, status=401)

    if not user.is_active:
        return Response({"error": "Compte non activé"}, status=403)

    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()

    send_mail(
        "Code de connexion",
        f"Votre OTP : {otp} (valable 5 min)",
        None,
        [user.email],
    )

    return Response({"message": "OTP envoyé"})


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not email or not otp:
        return Response({"error": "Email et OTP requis"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)

    if user.otp != otp or not user.otp_created_at:
        return Response({"error": "OTP invalide"}, status=400)

    if timezone.now() > user.otp_created_at + timedelta(minutes=5):
        return Response({"error": "OTP expiré"}, status=400)

    user.otp = None
    user.otp_created_at = None
    user.save()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({
        "access": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    })
    response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=False,          # OK en local (HTTP)
    samesite="Lax",        # 🔥 OBLIGATOIRE en cross-origin
    max_age=7 * 24 * 3600,
)
    print(response)

    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_access_token(request):
    print("COOKIES:", request.COOKIES)
    refresh_token = request.COOKIES.get('refresh_token')

    if not refresh_token:
        return Response({"detail": "Refresh token manquant"}, status=401)

    try:
        refresh = RefreshToken(refresh_token)
        user_id = refresh.payload.get('user_id')

        if not user_id:
            return Response({"detail": "Token invalide"}, status=401)

        user = User.objects.get(id=user_id)

        return Response({
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        })

    except (TokenError, User.DoesNotExist):
        return Response({"detail": "Token invalide ou expiré"}, status=401)
    except Exception:
        return Response({"detail": "Erreur serveur"}, status=500)


@api_view(['POST'])
def logout_view(request):
    response = Response({"message": "Déconnecté"})
    response.delete_cookie("refresh_token")
    return response


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.exclude(id=request.user.id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)