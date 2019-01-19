import os

from celery import Celery

app = Celery('processed_rows', backend=os.environ['BACKEND_CONN'], broker=os.environ['BROKER_CONN'])
