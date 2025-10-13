import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_ai.settings')

app = Celery('face_ai')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
