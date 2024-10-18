import random
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client

def generate_random_password(length=8):
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = f"{request.build_absolute_uri('/user/verify-email/')}?uid={uid}&token={token}"
    
    send_mail(
        subject="Подтверждение регистрации",
        message=f"Для подтверждения учетной записи перейдите по ссылке: {verification_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

def generate_sms_code():
    return random.randint(100000, 999999)

def send_verification_sms(user):
    sms_code = generate_sms_code()
    user.sms_code = sms_code  
    user.save()

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your verification code is: {sms_code}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=user.phone_number
    )


