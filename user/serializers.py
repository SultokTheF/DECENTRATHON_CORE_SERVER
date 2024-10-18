from rest_framework import serializers
from .models import CustomUser, DeviceToken
from .utils import generate_random_password 
from .utils import send_verification_email, send_verification_sms
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token']

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'iin', 'date_joined', 'is_active', 'is_staff', 'role']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.iin = validated_data.get('iin', instance.iin)  
        instance.role = validated_data.get('role', instance.role)

        instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'first_name', 'last_name', 'iin', 'password', 'role')

    def validate(self, data):
        """
        Ensure that at least either email or phone number is provided.
        """
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Either email or phone number must be provided.")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', 'USER')

        # Create the user
        user = CustomUser.objects.create_user(
            email=validated_data.get('email'),
            phone_number=validated_data.get('phone_number'),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            iin=validated_data['iin'],
            password=password,
            role=role
        )

        # Automatically set is_staff and is_superuser for ADMIN role
        if role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True  

        user.save()

        # Send verification based on email or SMS
        if user.email:
            send_verification_email(user, self.context['request'])
        elif user.phone_number:
            send_verification_sms(user)

        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'iin', 'role', 'is_active', 'is_verified')  # Ensure these fields are included

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден.")
        return value

    def save(self):
        request = self.context.get('request')
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = f"{request.build_absolute_uri('/user/password-reset-confirm/')}?uid={uid}&token={token}"
        
        send_mail(
            subject="Сброс пароля",
            message=f"Для сброса пароля перейдите по следующей ссылке: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = attrs.get('uid')
            token = attrs.get('token')
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)

            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError('Неверный токен или UID.')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Неверный токен или UID.')
        return attrs

    def save(self):
        uid = self.validated_data.get('uid')
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
        user.set_password(self.validated_data.get('new_password'))
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        email_or_phone = attrs.get('email', None)
        password = attrs.get('password', None)

        try:
            if '@' in email_or_phone:
                user = CustomUser.objects.get(email=email_or_phone)
            else:
                user = CustomUser.objects.get(phone_number=email_or_phone)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid login credentials.")

        if user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("Account is not activated yet.")
            return super().validate(attrs)
        else:
            raise serializers.ValidationError("Invalid login credentials.")




