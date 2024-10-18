from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Устанавливаем настройки по умолчанию для Django для программы Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')  # core — это название твоего проекта

app = Celery('UIREN_SERVER')

# Настройки Django для Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находит и загружает задачи из всех приложений Django
app.autodiscover_tasks()
