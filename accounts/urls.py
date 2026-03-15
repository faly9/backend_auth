from django.urls import path
# Ajout de UserListView ici
from .views import register_view, login_view, activate_account, verify_otp, hello_api, UserListView

urlpatterns = [
    path('register/', register_view, name="register"),
    path('login/', login_view, name="login"),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('hello/', hello_api, name="helloapi"),
    # Maintenant l'import est correct et .as_view() fonctionnera
    path('users/', UserListView.as_view(), name='user-list'), 
]