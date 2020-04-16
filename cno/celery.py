import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cno.settings')
app = Celery('cno', broker='pyamqp://{}:{}@{}:5672//'
             .format(os.getenv('CNO_IM_RMQ_USER'), os.getenv('CNO_IM_RMQ_PASSWORD'), os.getenv('CNO_IM_RMQ_HOST')))
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
