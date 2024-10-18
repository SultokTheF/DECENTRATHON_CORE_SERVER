from rest_framework import serializers
from .models import Context

class ContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Context
        fields = ['id', 'language', 'context']
