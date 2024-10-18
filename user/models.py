from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, first_name=None, last_name=None, password=None, role='USER', **extra_fields):
        if not email and not phone_number:
            raise ValueError('Either email or phone number must be provided')

        if email:
            email = self.normalize_email(email)

        user = self.model(
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            role=role,  
            **extra_fields
        )
        user.set_password(password)

        # Automatically set is_staff and is_superuser for ADMIN role
        if role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True  

        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, role='ADMIN', **extra_fields)

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('USER', 'User'),
        ('ADMIN', 'Admin'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent'),
        ('STAFF', 'Staff'),
    )

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)  
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    iin = models.CharField(max_length=12, unique=True, null=True, blank=True)
    role = models.CharField(max_length=6, choices=ROLE_CHOICES, default='USER')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  
    is_superuser = models.BooleanField(default=False)  
    is_verified = models.BooleanField(default=False)  
    date_joined = models.DateTimeField(default=timezone.now)
    sms_code = models.CharField(max_length=6, null=True, blank=True) 

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email or self.phone_number
    
class DeviceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='device_tokens', on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.email} - {self.token}"