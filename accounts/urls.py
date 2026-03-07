from django.urls import path
from .views import register_view , login_view , activate_account ,  verify_otp
urlpatterns = [
    path('register/' , register_view , name = "register"),
    path('login/' , login_view , name = "login"),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('verify-otp/', verify_otp, name='verify_otp'),
]