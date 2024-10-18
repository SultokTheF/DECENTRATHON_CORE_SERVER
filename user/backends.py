from django.contrib.auth.backends import ModelBackend
from .models import CustomUser

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(
                models.Q(email=username) | models.Q(phone_number=username)
            )
        except CustomUser.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None
