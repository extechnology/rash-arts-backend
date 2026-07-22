from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from django.utils import timezone
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, username=None, email=None, phone=None, password=None, **extra_fields):
        if not (username or email or phone):
            raise ValueError("User must have either a username, email, or phone.")

        if email:
            email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            phone=phone,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            username=username,
            email=email,
            phone=phone,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    fullname = models.CharField(max_length=255, blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or self.email or self.phone or f"User {self.id}"


class RegistrationOTP(models.Model):
    identifier = models.CharField(max_length=255)  
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.identifier} - {self.otp}"
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        from datetime import timedelta

        # Delete old OTPs for the same identifier
        RegistrationOTP.objects.filter(identifier=self.identifier).delete()
        super().save(*args, **kwargs)

    def is_valid(self, input_otp):
        # OTP is valid for 10 minutes

        if self.otp != input_otp:
            return False
        if timezone.now() > self.created_at + timedelta(minutes=10):
            return False
        return True


    
class ResetPasswordOTP(models.Model):
    identifier = models.CharField(max_length=255)  # can be email or phone
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.identifier} - {self.otp}"
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        from datetime import timedelta

        ResetPasswordOTP.objects.filter(identifier=self.identifier).delete()
        super().save(*args, **kwargs)
        
    def is_valid(self, input_otp):

        if self.otp != input_otp:
            return False
        if timezone.now() > self.created_at + timedelta(minutes=10):
            return False
        return True

# 