from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("The username field is required.")
        if not email:
            raise ValueError("The email field is required.")
        if not extra_fields.get("phone"):
            raise ValueError("The phone field is required.")
        if not extra_fields.get("national_id"):
            raise ValueError("The national_id field is required.")
        if not extra_fields.get("full_name"):
            raise ValueError("The full_name field is required.")
        email = self.normalize_email(email)
        return super().create_user(username, email=email, password=password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=32, unique=True)
    full_name = models.CharField(max_length=255)

    objects = CustomUserManager()

    REQUIRED_FIELDS = ["email", "phone", "national_id", "full_name"]

    def __str__(self):
        return self.username

