from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import register_device_token, UserViewSet, UserByTokenView, VerifyEmailView, UserProfileView, PasswordResetRequestView, PasswordResetConfirmView, VerifySMSView, AdminCreateStaffView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserByTokenView.as_view(), name='user_by_token'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('verify-sms/', VerifySMSView.as_view(), name='verify-sms'),
    path('register-device-token/', register_device_token, name='register-device-token'),
    path('admin/create-staff/', AdminCreateStaffView.as_view(), name='admin-create-staff'),


    path('', include(router.urls)),
]
