from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email ,username , password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        if not username:
            raise ValueError('Username must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username ,  **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user 

    def create_superuser(self, email , username , password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email=email, username=username, password=password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin" , "Admin",
        USER = "user" , "User"
        
    role=models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)  
    otp_created_at = models.DateTimeField(blank=True, null=True)  

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 

    objects = UserManager()

    def __str__(self):
        return self.email



