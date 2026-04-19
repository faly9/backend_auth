from django.urls import path
# Ajout de UserListView ici
from .views import register_view, login_view, activate_account, verify_otp, UserListView,refresh_access_token,logout_view

urlpatterns = [
    path('register/', register_view, name="register"),
    path('login/', login_view, name="login"),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    # Maintenant l'import est correct et .as_view() fonctionnera
    path('users/', UserListView.as_view(), name='user-list'), 
    path('refresh/', refresh_access_token, name='refresh-token'), 
    path('logout/', logout_view, name='logout'),
]