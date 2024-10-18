from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContextViewSet, answer_question

router = DefaultRouter()
router.register(r'contexts', ContextViewSet, basename='context')

urlpatterns = [
    path('', include(router.urls)),
    path('answer/', answer_question, name='answer-question'),
]